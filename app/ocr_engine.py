"""Motor de OCR com variantes, rotações, ordenação espacial e early stop."""
from dataclasses import dataclass, asdict

import numpy as np

from . import image_utils as iu
from . import vin_utils as vu
from .config import settings

_reader = None


def get_reader():
    """Carrega o EasyOCR sob demanda (evita custo no import/testes)."""
    global _reader
    if _reader is None:
        import easyocr
        _reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    return _reader


@dataclass
class OCRResult:
    vin: str | None
    valid: bool
    confidence: float
    variant: str | None
    rotation: int | None
    candidates: list[str]

    def to_dict(self):
        return asdict(self)


def order_blocks(blocks) -> tuple[str, float]:
    """Ordena blocos por linha (y) e depois coluna (x) e concatena."""
    if not blocks:
        return "", 0.0
    items = []
    for box, text, conf in blocks:
        ys = [p[1] for p in box]
        xs = [p[0] for p in box]
        items.append((sum(ys) / 4, sum(xs) / 4, text, conf))
    items.sort(key=lambda t: (round(t[0] / 25), t[1]))
    joined = "".join(i[2] for i in items)
    mean_conf = float(np.mean([i[3] for i in items]))
    return joined, mean_conf


def read_vin(img: np.ndarray, reader=None) -> OCRResult:
    reader = reader or get_reader()
    best = OCRResult(None, False, 0.0, None, None, [])
    seen: list[str] = []

    for rot in settings.fallback_rotations:
        rotated = iu.rotate(img, rot)
        for name, variant in iu.build_variants(rotated):
            blocks = reader.readtext(variant)
            text, conf = order_blocks(blocks)
            for cand in vu.extract_candidates(text, settings.max_candidates):
                if cand not in seen:
                    seen.append(cand)
                if vu.is_valid(cand):
                    # early stop: checksum bateu
                    return OCRResult(cand, True, conf, name, rot,
                                     seen[:settings.max_candidates])
            if conf > best.confidence and seen:
                best = OCRResult(seen[0], False, conf, name, rot, list(seen))

    best.candidates = seen[:settings.max_candidates]
    return best


def read_vin_from_bytes(data: bytes, reader=None) -> OCRResult:
    img = iu.decode_bytes(data)
    if img is None:
        raise ValueError("Arquivo enviado não é uma imagem válida.")
    return read_vin(img, reader)

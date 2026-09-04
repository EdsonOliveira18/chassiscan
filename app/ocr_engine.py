"""Motor de OCR com variantes, rotações, ordenação espacial e early stop."""

from __future__ import annotations

import logging
import threading
from dataclasses import asdict, dataclass, field

import numpy as np

from . import image_utils as iu
from . import vin_utils as vu
from .config import settings

logger = logging.getLogger(__name__)

_reader = None
_reader_lock = threading.Lock()

LINE_TOLERANCE_PX = 25


def get_reader():
    """Carrega o EasyOCR sob demanda, uma única vez (thread-safe)."""
    global _reader
    if _reader is None:
        with _reader_lock:
            if _reader is None:  # double-checked locking
                import easyocr

                logger.info("Inicializando EasyOCR (en, cpu)")
                _reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    return _reader


@dataclass
class OCRResult:
    vin: str | None = None
    valid: bool = False
    checksum_ok: bool = False
    confidence: float = 0.0
    variant: str | None = None
    rotation: int | None = None
    candidates: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _unpack_block(block) -> tuple[object, str, float] | None:
    """Normaliza um bloco do EasyOCR para (box, text, conf).

    Aceita (box, text, conf), (box, text) e str puro (detail=0).
    Retorna None se o bloco nao for aproveitavel.
    """
    if block is None:
        return None
    if isinstance(block, str):
        # detail=0: sem box e sem confianca -> assume 1.0 para nao ser filtrado
        return None, block, 1.0
    try:
        parts = list(block)
    except TypeError:
        return None
    if len(parts) >= 3:
        box, text, conf = parts[0], parts[1], parts[2]
    elif len(parts) == 2:
        box, text, conf = parts[0], parts[1], 1.0
    else:
        return None
    if not isinstance(text, str):
        return None
    try:
        conf = float(conf) if conf is not None else 0.0
    except (TypeError, ValueError):
        conf = 0.0
    return box, text, conf


def _centroid(box) -> tuple[float, float]:
    """Retorna (cy, cx) do bounding box; (0.0, 0.0) se indeterminado."""
    if box is None:
        return 0.0, 0.0
    try:
        pts = np.asarray(box, dtype=float)
    except (TypeError, ValueError):
        return 0.0, 0.0
    if pts.ndim != 2 or pts.shape[0] == 0 or pts.shape[1] < 2:
        return 0.0, 0.0
    return float(pts[:, 1].mean()), float(pts[:, 0].mean())


def order_blocks(blocks, min_conf: float = 0.0) -> tuple[str, float]:
    """Ordena blocos por linha (y) e coluna (x), concatena e pondera a confianca.

    Blocos com confianca abaixo de `min_conf` sao descartados.
    """
    if not blocks:
        return "", 0.0

    items: list[tuple[float, float, str, float]] = []
    for block in blocks:
        unpacked = _unpack_block(block)
        if unpacked is None:
            continue
        box, text, conf = unpacked
        text = vu.normalize(text)
        if not text or conf < min_conf:
            continue
        cy, cx = _centroid(box)
        items.append((cy, cx, text, conf))

    if not items:
        return "", 0.0

    items.sort(key=lambda t: (round(t[0] / LINE_TOLERANCE_PX), t[1]))
    joined = "".join(i[2] for i in items)

    # media ponderada pelo numero de caracteres: bloco de 1 char nao domina
    weights = [len(i[2]) for i in items]
    confs = [i[3] for i in items]
    mean_conf = float(np.average(confs, weights=weights)) if sum(weights) else 0.0
    return joined, mean_conf


def _build_result(cand: str, conf: float, name: str, rot: int, seen: list[str]) -> OCRResult:
    return OCRResult(
        vin=cand,
        valid=vu.is_valid(cand),
        checksum_ok=vu.checksum_matches(cand),
        confidence=round(conf, 4),
        variant=name,
        rotation=rot,
        candidates=seen[: settings.max_candidates],
    )


def read_vin(img: np.ndarray, reader=None) -> OCRResult:
    """Tenta extrair um VIN válido variando pré-processamento e rotação."""
    if img is None:
        raise ValueError("Imagem invalida para OCR.")

    reader = reader if reader is not None else get_reader()
    best = OCRResult()
    seen: list[str] = []
    processed_texts: set[str] = set()

    for rot in settings.fallback_rotations:
        rotated = img if rot % 360 == 0 else iu.rotate(img, rot)

        variants = list(iu.build_variants(rotated))[: settings.max_variants]
        for name, variant in variants:
            try:
                blocks = reader.readtext(variant)
            except Exception:  # pragma: no cover
                logger.warning("Falha no readtext (variant=%s, rot=%s)", name, rot)
                continue

            text, conf = order_blocks(blocks, settings.min_confidence)
            if not text or text in processed_texts:
                continue
            processed_texts.add(text)

            candidates = vu.extract_candidates(text, settings.max_candidates)
            for cand in candidates:
                if cand not in seen:
                    seen.append(cand)

            # early stop: só com confianca minima aceitavel
            for cand in candidates:
                if vu.is_valid(cand) and conf >= settings.min_confidence:
                    logger.info(
                        "VIN aceito (variant=%s, rot=%s, checksum=%s)",
                        name,
                        rot,
                        vu.checksum_matches(cand),
                    )
                    return _build_result(cand, conf, name, rot, seen)

            if candidates and conf > best.confidence:
                best = _build_result(candidates[0], conf, name, rot, seen)

    if best.vin is None and seen:
        # nenhuma variante passou o piso: usa o candidato melhor ranqueado
        ranked = sorted(seen, key=vu._score)
        best = _build_result(ranked[0], best.confidence, None, None, seen)

    best.candidates = seen[: settings.max_candidates]
    return best


def read_vin_from_bytes(data: bytes, reader=None) -> OCRResult:
    """Decodifica bytes de imagem e delega para `read_vin`."""
    if not data:
        raise ValueError("Nenhum dado de imagem recebido.")
    img = iu.decode_bytes(data)
    if img is None:
        raise ValueError("Arquivo enviado nao e uma imagem valida.")
    return read_vin(img, reader)

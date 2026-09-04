from __future__ import annotations

import logging
from collections.abc import Callable, Iterator

import cv2
import numpy as np

from .config import settings

logger = logging.getLogger(__name__)

MAX_WIDTH = 3000  # teto de upscale/downscale para nao explodir memoria/tempo
DESKEW_MIN_ANGLE = 0.5
DESKEW_MAX_ANGLE = 20.0


def _ensure_array(img: np.ndarray | None, who: str) -> np.ndarray:
    """Valida que a entrada e um ndarray nao vazio."""
    if img is None:
        raise ValueError(f"{who}: imagem ausente (None).")
    if not isinstance(img, np.ndarray):
        raise TypeError(f"{who}: esperado numpy.ndarray, recebido {type(img).__name__}.")
    if img.size == 0:
        raise ValueError(f"{who}: imagem vazia.")
    return img


def to_uint8(img: np.ndarray) -> np.ndarray:
    """Converte para uint8 preservando faixa dinamica (OpenCV exige uint8)."""
    if img.dtype == np.uint8:
        return img
    if img.dtype == np.uint16:
        return cv2.convertScaleAbs(img, alpha=255.0 / 65535.0)
    if np.issubdtype(img.dtype, np.floating):
        finite = img[np.isfinite(img)]
        if finite.size == 0:
            return np.zeros(img.shape, dtype=np.uint8)
        lo, hi = float(finite.min()), float(finite.max())
        if hi <= 1.0 and lo >= 0.0:
            return np.clip(img * 255.0, 0, 255).astype(np.uint8)
        if hi - lo < 1e-9:
            return np.zeros(img.shape, dtype=np.uint8)
        return (((img - lo) / (hi - lo)) * 255.0).clip(0, 255).astype(np.uint8)
    return np.clip(img, 0, 255).astype(np.uint8)


def to_gray(img: np.ndarray) -> np.ndarray:
    _ensure_array(img, "to_gray")
    if img.ndim == 3:
        if img.shape[2] == 4:
            gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
        elif img.shape[2] == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img[:, :, 0]
    elif img.ndim == 2:
        gray = img
    else:
        raise ValueError(f"to_gray: numero de dimensoes nao suportado ({img.ndim}).")
    return to_uint8(gray)


def resize_to_range(img: np.ndarray, min_width: int | None = None) -> np.ndarray:
    """Faz upscale se estreita demais e downscale se largura excede MAX_WIDTH."""
    _ensure_array(img, "resize_to_range")
    min_width = min_width if min_width is not None else settings.min_width
    h, w = img.shape[:2]
    if w == 0 or h == 0:
        return img

    if min_width > 0 and w < min_width:
        factor = min_width / w
        interp = cv2.INTER_CUBIC
    elif w > MAX_WIDTH:
        factor = MAX_WIDTH / w
        interp = cv2.INTER_AREA
    else:
        return img

    new_w, new_h = max(1, int(w * factor)), max(1, int(h * factor))
    return cv2.resize(img, (new_w, new_h), interpolation=interp)


# alias retrocompativel
upscale = resize_to_range


def _normalize_angle(angle: float) -> float:
    """minAreaRect retorna [0,90) no OpenCV>=4.5 e [-90,0) no legado."""
    if angle > 45:
        angle -= 90
    elif angle < -45:
        angle += 90
    return angle


def deskew(img: np.ndarray) -> np.ndarray:
    _ensure_array(img, "deskew")
    try:
        gray = to_gray(img)
        thr = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        coords = cv2.findNonZero(thr)
    except cv2.error:
        logger.debug("deskew: threshold falhou, retornando original")
        return img

    if coords is None or len(coords) < 5:
        return img

    angle = _normalize_angle(float(cv2.minAreaRect(coords)[-1]))
    if not (DESKEW_MIN_ANGLE <= abs(angle) <= DESKEW_MAX_ANGLE):
        return img

    h, w = img.shape[:2]
    if h < 2 or w < 2:
        return img

    m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    return cv2.warpAffine(img, m, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def rotate(img: np.ndarray, degrees: int) -> np.ndarray:
    """Rotaciona em multiplos de 90 graus (fallback: rotacao arbitraria)."""
    _ensure_array(img, "rotate")
    codes = {
        90: cv2.ROTATE_90_CLOCKWISE,
        180: cv2.ROTATE_180,
        270: cv2.ROTATE_90_COUNTERCLOCKWISE,
    }
    try:
        deg = int(degrees) % 360
    except (TypeError, ValueError) as exc:
        raise ValueError(f"rotate: graus invalidos ({degrees!r}).") from exc

    if deg == 0:
        return img
    if deg in codes:
        return cv2.rotate(img, codes[deg])

    h, w = img.shape[:2]
    m = cv2.getRotationMatrix2D((w / 2, h / 2), -deg, 1.0)
    return cv2.warpAffine(img, m, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


# --- as 6 variantes citadas no README ---
def v_raw(g: np.ndarray) -> np.ndarray:
    return g


def v_clahe(g: np.ndarray) -> np.ndarray:
    return cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(g)


def v_otsu(g: np.ndarray) -> np.ndarray:
    return cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]


def v_antiglare(g: np.ndarray) -> np.ndarray:
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 21))
    return cv2.morphologyEx(g, cv2.MORPH_TOPHAT, kernel)


def v_sharpen(g: np.ndarray) -> np.ndarray:
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
    return cv2.filter2D(g, -1, kernel)


def v_invert(g: np.ndarray) -> np.ndarray:
    return cv2.bitwise_not(v_otsu(g))


VariantFn = Callable[[np.ndarray], np.ndarray]

VARIANTS: list[tuple[str, VariantFn]] = [
    ("raw", v_raw),
    ("clahe", v_clahe),
    ("otsu", v_otsu),
    ("antiglare", v_antiglare),
    ("sharpen", v_sharpen),
    ("invert", v_invert),
]


def build_variants(
    img: np.ndarray, max_variants: int | None = None
) -> Iterator[tuple[str, np.ndarray]]:
    """Gera (nome, imagem) sob demanda, com resize + deskew aplicados uma vez."""
    _ensure_array(img, "build_variants")
    limit = max_variants if max_variants is not None else settings.max_variants
    limit = max(0, int(limit))
    if limit == 0:
        return

    base = deskew(resize_to_range(to_gray(img)))
    for name, fn in VARIANTS[:limit]:
        try:
            out = fn(base)
        except (cv2.error, ValueError, TypeError):
            logger.debug("build_variants: variante %s falhou, ignorando", name)
            continue
        if out is None or getattr(out, "size", 0) == 0:
            continue
        yield name, out


def decode_bytes(data: bytes) -> np.ndarray | None:
    """Decodifica bytes em BGR; retorna None se nao for imagem valida."""
    if not data:
        return None
    try:
        arr = np.frombuffer(data, np.uint8)
    except (TypeError, ValueError):
        return None
    if arr.size == 0:
        return None
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None or img.size == 0:
        return None
    return img

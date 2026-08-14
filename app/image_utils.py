"""Pré-processamento: deskew, contraste, upscale e variantes."""
import cv2
import numpy as np

from .config import settings


def to_gray(img: np.ndarray) -> np.ndarray:
    if img.ndim == 3:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img


def upscale(img: np.ndarray, min_width: int | None = None) -> np.ndarray:
    min_width = min_width or settings.min_width
    h, w = img.shape[:2]
    if w >= min_width:
        return img
    factor = min_width / w
    return cv2.resize(img, (int(w * factor), int(h * factor)),
                      interpolation=cv2.INTER_CUBIC)


def deskew(img: np.ndarray) -> np.ndarray:
    gray = to_gray(img)
    thr = cv2.threshold(gray, 0, 255,
                        cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    coords = cv2.findNonZero(thr)
    if coords is None:
        return img
    angle = cv2.minAreaRect(coords)[-1]
    angle = -(90 + angle) if angle < -45 else -angle
    if abs(angle) < 0.5:
        return img
    h, w = img.shape[:2]
    m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    return cv2.warpAffine(img, m, (w, h),
                          flags=cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_REPLICATE)


def rotate(img: np.ndarray, degrees: int) -> np.ndarray:
    codes = {90: cv2.ROTATE_90_CLOCKWISE,
             180: cv2.ROTATE_180,
             270: cv2.ROTATE_90_COUNTERCLOCKWISE}
    return img if degrees % 360 == 0 else cv2.rotate(img, codes[degrees % 360])


# --- as 6 variantes citadas no README ---
def v_raw(g):        return g
def v_clahe(g):      return cv2.createCLAHE(2.0, (8, 8)).apply(g)
def v_otsu(g):       return cv2.threshold(g, 0, 255,
                                          cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
def v_antiglare(g):  return cv2.morphologyEx(
                         g, cv2.MORPH_TOPHAT,
                         cv2.getStructuringElement(cv2.MORPH_RECT, (21, 21)))
def v_sharpen(g):    return cv2.filter2D(
                         g, -1, np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]]))
def v_invert(g):     return cv2.bitwise_not(v_otsu(g))


VARIANTS = [
    ("raw", v_raw), ("clahe", v_clahe), ("otsu", v_otsu),
    ("antiglare", v_antiglare), ("sharpen", v_sharpen), ("invert", v_invert),
]


def build_variants(img: np.ndarray, max_variants: int | None = None):
    """Gera (nome, imagem) para cada variante, com upscale + deskew aplicados."""
    limit = max_variants or settings.max_variants
    gray = deskew(upscale(to_gray(img)))
    return [(name, fn(gray)) for name, fn in VARIANTS[:limit]]


def decode_bytes(data: bytes) -> np.ndarray | None:
    arr = np.frombuffer(data, np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)

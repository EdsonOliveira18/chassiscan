"""Normalização e validação de VIN (ISO 3779 / 3780)."""

import re

VIN_LEN = 17
INVALID_CHARS = {"I": "1", "O": "0", "Q": "0"}
VIN_REGEX = re.compile(r"[A-HJ-NPR-Z0-9]{17}")

TRANSLITERATION = {
    **{c: i for i, c in enumerate("ABCDEFGHJKLMNPRSTUVWXYZ".replace("", ""), start=0)},
}
# tabela oficial
TRANSLITERATION = {
    "A": 1,
    "B": 2,
    "C": 3,
    "D": 4,
    "E": 5,
    "F": 6,
    "G": 7,
    "H": 8,
    "J": 1,
    "K": 2,
    "L": 3,
    "M": 4,
    "N": 5,
    "P": 7,
    "R": 9,
    "S": 2,
    "T": 3,
    "U": 4,
    "V": 5,
    "W": 6,
    "X": 7,
    "Y": 8,
    "Z": 9,
    **{str(d): d for d in range(10)},
}
WEIGHTS = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]


def normalize(raw: str) -> str:
    """Remove ruído e troca caracteres proibidos por seus equivalentes."""
    if not raw:
        return ""
    text = re.sub(r"[^A-Za-z0-9]", "", raw).upper()
    return "".join(INVALID_CHARS.get(ch, ch) for ch in text)


def checksum_digit(vin: str) -> str | None:
    """Retorna o dígito verificador esperado (posição 9)."""
    if len(vin) != VIN_LEN:
        return None
    total = 0
    for ch, weight in zip(vin, WEIGHTS, strict=True):
        if ch not in TRANSLITERATION:
            return None
        total += TRANSLITERATION[ch] * weight
    rest = total % 11
    return "X" if rest == 10 else str(rest)


def is_valid(vin: str) -> bool:
    """Valida tamanho, alfabeto e dígito verificador."""
    vin = normalize(vin)
    if len(vin) != VIN_LEN or not VIN_REGEX.fullmatch(vin):
        return False
    return checksum_digit(vin) == vin[8]


def extract_candidates(text: str, limit: int = 5) -> list[str]:
    """Extrai possíveis VINs de um texto bruto de OCR."""
    clean = normalize(text)
    found, seen = [], set()
    for i in range(len(clean) - VIN_LEN + 1):
        window = clean[i : i + VIN_LEN]
        if VIN_REGEX.fullmatch(window) and window not in seen:
            seen.add(window)
            found.append(window)
    found.sort(key=lambda v: not is_valid(v))  # válidos primeiro
    return found[:limit]

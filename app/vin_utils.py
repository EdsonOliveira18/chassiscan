"""Normalização e validação de VIN (ISO 3779 / 3780)."""

from __future__ import annotations

import re
from functools import lru_cache

VIN_LEN = 17

# I, O, Q nao existem no alfabeto VIN -> confusoes tipicas de OCR
INVALID_CHARS = {"I": "1", "O": "0", "Q": "0"}
VIN_REGEX = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")
_NON_ALNUM = re.compile(r"[^A-Za-z0-9]")

# Confusoes bidirecionais tipicas em chassi estampado/gravado
OCR_CONFUSIONS: dict[str, tuple[str, ...]] = {
    "0": ("D",),
    "D": ("0",),
    "1": ("7", "L"),
    "7": ("1",),
    "L": ("1",),
    "2": ("Z",),
    "Z": ("2",),
    "5": ("S",),
    "S": ("5",),
    "6": ("G",),
    "G": ("6",),
    "8": ("B",),
    "B": ("8",),
    "4": ("A",),
    "A": ("4",),
}

# Tabela oficial de transliteracao (ISO 3779)
TRANSLITERATION: dict[str, int] = {
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

WEIGHTS = (8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2)
CHECK_POSITION = 8  # 9o caractere (indice 0-based)

# WMI cujo pais exige digito verificador (FMVSS 115 / America do Norte)
CHECKSUM_REQUIRED_PREFIX = ("1", "2", "3", "4", "5", "7")

# Codigos validos para o ano-modelo (posicao 10)
YEAR_CODES = frozenset("ABCDEFGHJKLMNPRSTVWXY123456789")


def normalize(raw: str | None) -> str:
    """Remove ruido e troca caracteres proibidos por seus equivalentes."""
    if not raw:
        return ""
    text = _NON_ALNUM.sub("", raw).upper()
    return "".join(INVALID_CHARS.get(ch, ch) for ch in text)


@lru_cache(maxsize=2048)
def _is_structural(candidate: str) -> bool:
    """Cache sobre texto JA normalizado: 17 chars no alfabeto VIN."""
    return bool(VIN_REGEX.match(candidate))


def is_structural(vin: str | None) -> bool:
    """Valida apenas tamanho e alfabeto (ISO 3780). Nao checa digito."""
    return _is_structural(normalize(vin))


def checksum_digit(vin: str | None) -> str | None:
    """Retorna o digito verificador esperado (posicao 9) ou None se invalido."""
    candidate = normalize(vin)
    if len(candidate) != VIN_LEN or not _is_structural(candidate):
        return None
    total = 0
    for ch, weight in zip(candidate, WEIGHTS, strict=True):
        value = TRANSLITERATION.get(ch)
        if value is None:
            return None
        total += value * weight
    rest = total % 11
    return "X" if rest == 10 else str(rest)


def checksum_matches(vin: str | None) -> bool:
    """True se o digito verificador ISO 3779 confere."""
    candidate = normalize(vin)
    expected = checksum_digit(candidate)
    return expected is not None and expected == candidate[CHECK_POSITION]


def requires_checksum(vin: str | None) -> bool:
    """Checksum e obrigatorio apenas para VIN norte-americano."""
    candidate = normalize(vin)
    return len(candidate) == VIN_LEN and candidate[0] in CHECKSUM_REQUIRED_PREFIX


@lru_cache(maxsize=2048)
def _is_valid(candidate: str) -> bool:
    if not _is_structural(candidate):
        return False
    if candidate[0] in CHECKSUM_REQUIRED_PREFIX:
        return checksum_matches(candidate)
    # Fora da America do Norte a posicao 9 e livre: exige-se ano-modelo plausivel
    return candidate[9] in YEAR_CODES


def is_valid(vin: str | None) -> bool:
    """Valida tamanho, alfabeto e — quando aplicavel — o digito verificador."""
    return _is_valid(normalize(vin))


def is_valid_strict(vin: str | None) -> bool:
    """Validacao rigida: sempre exige o checksum ISO 3779."""
    return is_structural(vin) and checksum_matches(vin)


def repair_candidates(vin: str | None, max_edits: int = 1) -> list[str]:
    """Gera variacoes trocando 1 caractere ambiguo, mantendo so as validas."""
    candidate = normalize(vin)
    if not _is_structural(candidate) or max_edits < 1:
        return []

    out: list[str] = []
    seen: set[str] = {candidate}
    for i, ch in enumerate(candidate):
        for alt in OCR_CONFUSIONS.get(ch, ()):
            fixed = candidate[:i] + alt + candidate[i + 1 :]
            if fixed in seen or not _is_structural(fixed):
                continue
            seen.add(fixed)
            if is_valid_strict(fixed):
                out.append(fixed)
    return out


def _score(vin: str) -> tuple[int, int, int]:
    """Chave de ordenacao: menor e melhor."""
    return (
        0 if is_valid(vin) else 1,
        0 if checksum_matches(vin) else 1,
        0 if vin[9] in YEAR_CODES else 1,
    )


def extract_candidates(text: str | None, limit: int = 5) -> list[str]:
    """Extrai possiveis VINs de um texto bruto de OCR, validos primeiro."""
    if limit <= 0:
        return []
    clean = normalize(text)
    if len(clean) < VIN_LEN:
        return []

    seen: set[str] = set()
    found: list[str] = []
    for i in range(len(clean) - VIN_LEN + 1):
        window = clean[i : i + VIN_LEN]
        if window in seen or not _is_structural(window):
            continue
        seen.add(window)
        found.append(window)

    # tenta reparar 1 caractere ambiguo quando nenhum candidato e valido
    if not any(is_valid(v) for v in found):
        for base in list(found):
            for fixed in repair_candidates(base):
                if fixed not in seen:
                    seen.add(fixed)
                    found.append(fixed)

    found.sort(key=_score)  # sort estavel: mantem ordem original nos empates
    return found[:limit]

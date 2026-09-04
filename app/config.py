"""Configuração central via variáveis de ambiente, com validação e clamp."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

DEFAULT_ROTATIONS: tuple[int, ...] = (0, 90, 180, 270)
MAX_VARIANTS_AVAILABLE = 6


def _env_float(key: str, default: float, lo: float, hi: float) -> float:
    raw = os.getenv(key)
    if raw is None or not raw.strip():
        return default
    try:
        value = float(raw)
    except (TypeError, ValueError):
        logger.warning("%s=%r invalido, usando %s", key, raw, default)
        return default
    if not lo <= value <= hi:
        logger.warning("%s=%s fora de [%s, %s], ajustando", key, value, lo, hi)
        return min(max(value, lo), hi)
    return value


def _env_int(key: str, default: int, lo: int, hi: int) -> int:
    raw = os.getenv(key)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError):
        logger.warning("%s=%r invalido, usando %s", key, raw, default)
        return default
    if not lo <= value <= hi:
        logger.warning("%s=%s fora de [%s, %s], ajustando", key, value, lo, hi)
        return min(max(value, lo), hi)
    return value


def _env_rotations(key: str, default: tuple[int, ...]) -> tuple[int, ...]:
    """Aceita lista CSV de graus. Normaliza para [0,360), remove duplicatas."""
    raw = os.getenv(key)
    if not raw or not raw.strip():
        return default

    parsed: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            parsed.append(int(part) % 360)
        except ValueError:
            logger.warning("%s: rotacao %r ignorada", key, part)

    # dedup preservando ordem
    unique = list(dict.fromkeys(parsed))
    if not unique:
        logger.warning("%s=%r nao produziu rotacoes validas, usando %s", key, raw, default)
        return default
    return tuple(unique)


@dataclass(frozen=True)
class Settings:
    min_confidence: float = field(
        default_factory=lambda: _env_float("CHASSISCAN_MIN_CONF", 0.45, 0.0, 1.0)
    )
    max_variants: int = field(
        default_factory=lambda: _env_int("CHASSISCAN_MAX_VARIANTS", 6, 1, MAX_VARIANTS_AVAILABLE)
    )
    max_candidates: int = field(
        default_factory=lambda: _env_int("CHASSISCAN_MAX_CANDIDATES", 5, 1, 50)
    )
    min_width: int = field(default_factory=lambda: _env_int("CHASSISCAN_MIN_WIDTH", 900, 100, 3000))
    fallback_rotations: tuple[int, ...] = field(
        default_factory=lambda: _env_rotations("CHASSISCAN_ROTATIONS", DEFAULT_ROTATIONS)
    )

    def to_dict(self) -> dict:
        return {
            "min_confidence": self.min_confidence,
            "max_variants": self.max_variants,
            "max_candidates": self.max_candidates,
            "min_width": self.min_width,
            "fallback_rotations": list(self.fallback_rotations),
        }


settings = Settings()

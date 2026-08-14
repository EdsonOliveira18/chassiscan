from dataclasses import dataclass, field
import os


@dataclass
class Settings:
    min_confidence: float = float(os.getenv("CHASSISCAN_MIN_CONF", 0.45))
    max_variants: int = int(os.getenv("CHASSISCAN_MAX_VARIANTS", 6))
    fallback_rotations: tuple = (0, 90, 180, 270)
    min_width: int = 900          # abaixo disso, faz upscale
    max_candidates: int = 5       # candidatos retornados no fallback


settings = Settings()
                 



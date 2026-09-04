import sys
from pathlib import Path

# Garante que a raiz do projeto esteja no sys.path ANTES de importar `app`.
ROOT = Path(__file__).parent.resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import cv2  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.api import app  # noqa: E402

VALID_VIN = "1HGCM82633A004352"  # checksum ISO 3779 válido


@pytest.fixture(scope="session")
def valid_vin() -> str:
    return VALID_VIN


@pytest.fixture
def client():
    """Cliente HTTP de teste da API (dispara eventos de startup/shutdown)."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def fake_reader():
    """Reader falso: devolve blocos de OCR sem carregar o modelo real."""

    class FakeReader:
        def __init__(self, text: str = VALID_VIN, conf: float = 0.93) -> None:
            self.text = text
            self.conf = conf

        def readtext(self, _img, *_args, **_kwargs):
            box = [[0, 0], [100, 0], [100, 30], [0, 30]]
            return [(box, self.text, self.conf)]

    return FakeReader()


@pytest.fixture
def sample_image() -> np.ndarray:
    """Imagem sintética 200x1000 com o VIN válido desenhado."""
    img = np.full((200, 1000, 3), 255, dtype=np.uint8)
    cv2.putText(img, VALID_VIN, (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 2.2, (0, 0, 0), 5)
    return img

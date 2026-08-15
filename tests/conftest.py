import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.api import app

VALID_VIN = "1HGCM82633A004352"  # checksum ISO válido


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def fake_reader():
    """Reader falso: devolve blocos de OCR sem carregar modelo real."""

    class FakeReader:
        def __init__(self, text=VALID_VIN, conf=0.93):
            self.text, self.conf = text, conf

        def readtext(self, _img):
            box = [[0, 0], [100, 0], [100, 30], [0, 30]]
            return [(box, self.text, self.conf)]

    return FakeReader()


@pytest.fixture
def sample_image():
    img = np.full((200, 1000, 3), 255, np.uint8)
    import cv2

    cv2.putText(img, VALID_VIN, (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 2.2, (0, 0, 0), 5)
    return img

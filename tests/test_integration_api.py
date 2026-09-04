"""Testes de integracao da API (contratos HTTP e comportamento end-to-end)."""

import io

import cv2
import pytest

from app.api import ocr_engine

pytestmark = pytest.mark.integration


def _jpeg(img) -> io.BytesIO:
    ok, buf = cv2.imencode(".jpg", img)
    assert ok, "falha ao codificar JPEG"
    return io.BytesIO(buf.tobytes())


@pytest.fixture
def reader_fake(monkeypatch, fake_reader):
    """Injeta o reader fake e limpa o cache do singleton, se existir."""
    clear = getattr(ocr_engine.get_reader, "cache_clear", None)
    if clear:
        clear()
    monkeypatch.setattr(ocr_engine, "get_reader", lambda: fake_reader)
    yield fake_reader
    if clear:
        clear()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "service": "chassiscan", "version": "1.0.0"}


@pytest.mark.parametrize(
    ("nome", "conteudo", "mime", "esperado"),
    [
        ("x.jpg", b"", "image/jpeg", 400),
        ("x.txt", b"nao sou imagem", "text/plain", 415),
        ("x.jpg", b"\x00\x01lixo", "image/jpeg", 415),
        ("x.pdf", b"%PDF-1.7", "application/pdf", 415),
    ],
)
def test_ocr_entradas_invalidas(client, nome, conteudo, mime, esperado):
    r = client.post("/ocr/chassi", files={"file": (nome, conteudo, mime)})
    assert r.status_code == esperado
    assert "detail" in r.json()


def test_ocr_sem_arquivo(client):
    assert client.post("/ocr/chassi").status_code == 422


def test_ocr_sucesso(client, reader_fake, sample_image, valid_vin):
    r = client.post("/ocr/chassi", files={"file": ("c.jpg", _jpeg(sample_image), "image/jpeg")})
    assert r.status_code == 200
    body = r.json()
    assert body["vin"] == valid_vin
    assert body["valid"] is True
    assert set(body) >= {"vin", "valid", "confidence"}
    assert 0.0 <= body["confidence"] <= 1.0


def test_ocr_nada_detectado(client, monkeypatch, sample_image):
    monkeypatch.setattr(
        ocr_engine,
        "read_vin",
        lambda *_a, **_k: ocr_engine.OCRResult(vin=None, confidence=0.0),
    )
    r = client.post("/ocr/chassi", files={"file": ("c.jpg", _jpeg(sample_image), "image/jpeg")})
    assert r.status_code in (200, 422)
    if r.status_code == 200:
        assert r.json()["valid"] is False

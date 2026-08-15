import io

import cv2

from app.api import ocr_engine


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "service": "chassiscan", "version": "1.0.0"}


def test_ocr_arquivo_vazio(client):
    r = client.post("/ocr/chassi", files={"file": ("x.jpg", b"", "image/jpeg")})
    assert r.status_code == 400


def test_ocr_arquivo_nao_imagem(client):
    r = client.post("/ocr/chassi", files={"file": ("x.txt", b"nao sou imagem", "text/plain")})
    assert r.status_code == 415


def test_ocr_sucesso(client, monkeypatch, fake_reader, sample_image):
    monkeypatch.setattr(ocr_engine, "get_reader", lambda: fake_reader)
    buf = io.BytesIO(cv2.imencode(".jpg", sample_image)[1].tobytes())
    r = client.post("/ocr/chassi", files={"file": ("c.jpg", buf, "image/jpeg")})
    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is True
    assert body["vin"] == "1HGCM82633A004352"

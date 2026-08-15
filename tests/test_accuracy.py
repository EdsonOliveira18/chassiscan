"""Acurácia sobre lote rotulado. Coloque as fotos em tests/fixtures/
com o VIN no nome do arquivo: 1HGCM82633A004352_reflexo.jpg"""

from pathlib import Path

import cv2
import pytest

from app.ocr_engine import read_vin

FIXTURES = Path(__file__).parent / "fixtures"
MIN_ACCURACY = 0.80


def _lote():
    if not FIXTURES.exists():
        return []
    return sorted(p for p in FIXTURES.glob("*.jp*g"))


@pytest.mark.accuracy
@pytest.mark.skipif(not _lote(), reason="sem fixtures rotuladas")
def test_acuracia_do_lote():
    acertos = 0
    falhas = []
    for path in _lote():
        esperado = path.stem.split("_")[0].upper()
        obtido = read_vin(cv2.imread(str(path))).vin
        if obtido == esperado:
            acertos += 1
        else:
            falhas.append(f"{path.name}: esperado={esperado} obtido={obtido}")

    taxa = acertos / len(_lote())
    print(f"\nAcurácia: {taxa:.1%} ({acertos}/{len(_lote())})")
    assert taxa >= MIN_ACCURACY, "Falhas:\n" + "\n".join(falhas)

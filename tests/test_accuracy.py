"""Gate de acuracia do OCR sobre lote rotulado (VIN no nome do arquivo)."""

from pathlib import Path

import cv2
import pytest

from app.ocr_engine import read_vin

FIXTURES = Path(__file__).parent / "fixtures"
MIN_ACCURACY = 0.80
PADROES = ("*.jpg", "*.jpeg", "*.png", "*.webp")


def _lote() -> list[Path]:
    if not FIXTURES.is_dir():
        return []
    return sorted(p for padrao in PADROES for p in FIXTURES.glob(padrao))


LOTE = _lote()

pytestmark = [
    pytest.mark.accuracy,
    pytest.mark.slow,
    pytest.mark.skipif(not LOTE, reason="sem fixtures rotuladas em tests/fixtures/"),
]


@pytest.fixture(scope="module")
def resultados() -> list[tuple[Path, str, str | None]]:
    """Roda o OCR uma unica vez por imagem (caro)."""
    saida = []
    for path in LOTE:
        img = cv2.imread(str(path))
        assert img is not None, f"imagem ilegivel: {path.name}"
        esperado = path.stem.split("_")[0].upper()
        saida.append((path, esperado, read_vin(img).vin))
    return saida


def test_acuracia_do_lote(resultados):
    falhas = [
        f"  {p.name}: esperado={esp} obtido={obt}" for p, esp, obt in resultados if obt != esp
    ]
    acertos = len(resultados) - len(falhas)
    taxa = acertos / len(resultados)

    assert taxa >= MIN_ACCURACY, (
        f"Acuracia {taxa:.1%} ({acertos}/{len(resultados)}) < "
        f"minimo {MIN_ACCURACY:.0%}\nFalhas:\n" + "\n".join(falhas)
    )


def test_lote_tem_rotulos_validos():
    """Protege o gate contra fixture mal nomeada (que viraria falso negativo)."""
    invalidos = [
        p.name for p, esp, _ in ((p, p.stem.split("_")[0], None) for p in LOTE) if len(esp) != 17
    ]
    assert not invalidos, f"nomes sem VIN de 17 chars: {invalidos}"

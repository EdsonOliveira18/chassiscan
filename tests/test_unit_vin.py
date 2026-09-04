"""Testes unitarios de normalizacao, checksum e extracao de VIN."""

import pytest

from app import vin_utils as vu

pytestmark = pytest.mark.unit

VALID = "1HGCM82633A004352"


# ---------------------------------------------------------------- normalize
@pytest.mark.parametrize(
    ("raw", "esperado"),
    [
        ("1hg-cm 826", "1HGCM826"),
        ("IOQ123", "100123"),  # I->1, O->0, Q->0
        ("", ""),
        ("  \n\t", ""),
        # normalize NAO recorta prefixos: "vin" -> "V1N" (I->1)
        ("vin: 1HGCM82633A004352.", "V1N" + VALID),
        ("i0o1q", "10010"),  # I->1, 0, O->0, 1, Q->0
        ("!@#$%", ""),  # sem alfanumerico -> vazio
        (VALID, VALID),  # idempotente
        (None, ""),  # entrada nula
    ],
)
def test_normalize(raw, esperado):
    assert vu.normalize(raw) == esperado


def test_normalize_e_idempotente():
    uma = vu.normalize("1hg-cm iOQ")
    assert vu.normalize(uma) == uma


# ---------------------------------------------------------------- checksum
def test_checksum_digit_ok():
    assert vu.checksum_digit(VALID) == VALID[8]


@pytest.mark.parametrize("vin", ["", "ABC123", "1" * 16, "1" * 18])
def test_checksum_tamanho_invalido(vin):
    assert vu.checksum_digit(vin) is None


def test_checksum_none_nao_explode():
    assert vu.checksum_digit(None) is None


def test_checksum_ignora_posicao_9():
    """O digito verificador nao entra no proprio calculo."""
    alterado = VALID[:8] + "0" + VALID[9:]
    assert vu.checksum_digit(alterado) == VALID[8]


def test_checksum_matches():
    assert vu.checksum_matches(VALID)
    assert not vu.checksum_matches(VALID[:8] + "0" + VALID[9:])


# ---------------------------------------------------------------- is_valid
@pytest.mark.parametrize("vin", [VALID, "11111111111111111", "1M8GDM9AXKP042788"])
def test_is_valid_true(vin):
    assert vu.is_valid(vin)


@pytest.mark.parametrize(
    ("vin", "motivo"),
    [
        ("1HGCM82633A004353", "checksum errado"),
        ("SHORT", "tamanho"),
        ("1HGCM82633A0043521", "18 chars"),
        ("", "vazio"),
    ],
)
def test_is_valid_false(vin, motivo):
    assert not vu.is_valid(vin), motivo


@pytest.mark.parametrize("letra", ["I", "O", "Q"])
def test_letras_proibidas_fora_do_alfabeto(letra):
    """I/O/Q nao pertencem ao alfabeto VIN; normalize os converte."""
    bruto = VALID[:16] + letra
    assert not vu.VIN_REGEX.match(bruto)
    assert vu.normalize(bruto) == VALID[:16] + vu.INVALID_CHARS[letra]


# ---------------------------------------------------------------- extracao
def test_extract_candidates_prioriza_validos():
    cands = vu.extract_candidates(f"XX{VALID}YY")
    assert cands, "nenhum candidato extraido"
    assert cands[0] == VALID


def test_extract_candidates_ordena_por_validade():
    """Validos vem antes dos apenas estruturais."""
    invalido = "1HGCM82633A004353"
    cands = vu.extract_candidates(f"{invalido} lixo {VALID}", limit=50)
    assert cands[0] == VALID
    assert invalido in cands
    assert cands.index(VALID) < cands.index(invalido)


def test_extract_candidates_respeita_limit():
    cands = vu.extract_candidates(f"XX{VALID}YY", limit=1)
    assert cands == [VALID]
    assert vu.extract_candidates(f"XX{VALID}YY", limit=0) == []


@pytest.mark.parametrize("texto", ["", "abc", "12345", "!!!", None])
def test_extract_candidates_sem_match(texto):
    assert vu.extract_candidates(texto) == []


def test_extract_candidates_sem_duplicatas():
    cands = vu.extract_candidates(f"{VALID} {VALID}", limit=50)
    assert len(cands) == len(set(cands))

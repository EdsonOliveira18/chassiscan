import pytest

from chassiscan import vin_utils as vu

VALID = "1HGCM82633A004352"


@pytest.mark.parametrize("raw,expected", [
    ("1hg-cm 826", "1HGCM826"),
    ("IOQ123", "100123"),
    ("", ""),
])
def test_normalize(raw, expected):
    assert vu.normalize(raw) == expected


def test_checksum_digit_ok():
    assert vu.checksum_digit(VALID) == VALID[8]


def test_checksum_tamanho_invalido():
    assert vu.checksum_digit("ABC123") is None


def test_is_valid_true():
    assert vu.is_valid(VALID)


@pytest.mark.parametrize("vin", ["1HGCM82633A004353", "SHORT", "1HGCM82633A00435I"])
def test_is_valid_false(vin):
    assert not vu.is_valid(vin)


def test_extract_candidates_prioriza_validos():
    ruido = f"XX{VALID}YY"
    cands = vu.extract_candidates(ruido)
    assert cands[0] == VALID

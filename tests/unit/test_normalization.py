"""Unit testovi za normalization layer (TEST 5)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "document_engines" / "benchmark"))

from normalization import (
    parse_number,
    parse_percent,
    normalize_unit,
    normalize_currency,
    parse_tariff,
    ocr_correct_numeric,
    safe_ocr_correct,
    extract_numeric_candidates,
)


def test_parse_number_evropski():
    assert parse_number("1.234,56") == 1234.56
    assert parse_number("1234,56") == 1234.56
    assert parse_number("1 234,56") == 1234.56
    assert parse_number("1 234.56") == 1234.56


def test_parse_number_us():
    assert parse_number("1,234.56") == 1234.56
    assert parse_number("1234.56") == 1234.56
    assert parse_number("1,234.00") == 1234.00


def test_parse_number_both_separators():
    """'1.234.567,89' — evropski s više hiljadskih"""
    assert parse_number("1.234.567,89") == 1234567.89
    """'1,234,567.89' — US s više hiljadskih"""
    assert parse_number("1,234,567.89") == 1234567.89


def test_parse_number_edge_cases():
    assert parse_number("0") == 0
    assert parse_number("-3,14") == -3.14
    assert parse_number("0,5") == 0.5
    assert parse_number("") is None
    assert parse_number(None) is None
    assert parse_number("abc") is None


def test_parse_percent():
    assert parse_percent("10%") == 10.0
    assert parse_percent("10 %") == 10.0
    assert parse_percent("10,5 %") == 10.5
    assert parse_percent("0%") == 0.0
    assert parse_percent("100%") == 100.0
    assert parse_percent("") is None
    assert parse_percent("abc") is None


def test_normalize_unit_known():
    assert normalize_unit("kg") == "kg"
    assert normalize_unit("KOM") == "pcs"
    assert normalize_unit("kom.") == "pcs"
    assert normalize_unit("komada") == "pcs"
    assert normalize_unit("PCS") == "pcs"
    assert normalize_unit("piece") == "pcs"
    assert normalize_unit("pieces") == "pcs"
    assert normalize_unit("Stk.") == "pcs"
    assert normalize_unit("L") == "l"
    assert normalize_unit("m2") == "m2"


def test_normalize_unit_unknown_passthrough():
    assert normalize_unit("xyz") == "xyz"
    assert normalize_unit("") is None


def test_normalize_currency_known():
    assert normalize_currency("EUR") == "EUR"
    assert normalize_currency("€") == "EUR"
    assert normalize_currency("USD") == "USD"
    assert normalize_currency("$") == "USD"
    assert normalize_currency("KM") == "BAM"
    assert normalize_currency("BAM") == "BAM"


def test_normalize_currency_unknown_passthrough():
    assert normalize_currency("XYZ") == "XYZ"
    assert normalize_currency("") is None


def test_parse_tariff_valid():
    assert parse_tariff("38249993") == "38249993"  # 8 cifara
    assert parse_tariff("33049900") == "33049900"
    assert parse_tariff("3824.99.93") == "38249993"  # sa tačkama
    assert parse_tariff("3824 9993") == "38249993"  # sa razmakom
    assert parse_tariff("3824-9993") == "38249993"  # sa crtom
    assert parse_tariff("123456") == "123456"  # 6 cifara
    assert parse_tariff("1234567890") == "1234567890"  # 10 cifara


def test_parse_tariff_invalid():
    assert parse_tariff("12345") is None  # 5 cifara — premalo
    assert parse_tariff("12345678901") is None  # 11 cifara — previše
    assert parse_tariff("abc") is None
    assert parse_tariff("") is None


def test_ocr_correct_numeric_o_to_zero():
    """Kontekst numerički: '1O' → '10'."""
    r = ocr_correct_numeric("1O", field="numeric")
    assert r == "10"


def test_ocr_correct_numeric_i_to_one():
    """Kontekst numerički: 'I23' → '123'."""
    r = ocr_correct_numeric("I23", field="numeric")
    assert r == "123"


def test_ocr_correct_numeric_no_change_when_already_numeric():
    """'123' ostaje '123'."""
    r = ocr_correct_numeric("123", field="numeric")
    assert r == "123"


def test_ocr_correct_numeric_tariff():
    """Kontekst tarifa: '38O249993' → '380249993' (10 cifara — granica)."""
    # 10 cifara granica — može ili ne može; po specifikaciji 6-10 je OK
    r = ocr_correct_numeric("3824999O", field="tariff")
    assert r == "38249990"


def test_safe_ocr_correct_no_change_for_alphanumeric():
    """Ako tekst već sadrži mješovite znakove koji nisu numerički nakon korekcije, vrati None."""
    assert safe_ocr_correct("abc") is None
    assert safe_ocr_correct("") is None


def test_safe_ocr_correct_applies_only_when_meaningful():
    """'O23' → '023' (validan numerik)."""
    r = safe_ocr_correct("O23", expected_format="numeric")
    assert r == "023"


def test_extract_numeric_candidates_single():
    assert extract_numeric_candidates("100") == [100.0]
    assert extract_numeric_candidates("1.234,56") == [1234.56]
    assert extract_numeric_candidates("44,00") == [44.0]


def test_extract_numeric_candidates_multiple():
    """'10 kom 5,50' → [10, 5.50]."""
    result = extract_numeric_candidates("10 kom 5,50")
    assert 10.0 in result
    assert 5.50 in result


def test_extract_numeric_candidates_empty():
    assert extract_numeric_candidates("") == []
    assert extract_numeric_candidates(None) == []


def test_extract_numeric_candidates_garbage():
    assert extract_numeric_candidates("abc") == []

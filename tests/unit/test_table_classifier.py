"""Unit testovi za Table Classifier."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "document_engines" / "benchmark"))

from table_classifier import classify_physical_segment, classify_all_segments


def test_classify_item_table_typical_headers():
    headers = ["Description / Opis robe", "Quantity Kolicina", "Unit Price Cena", "Total Amount Iznos"]
    result = classify_physical_segment(headers, n_rows=20, n_cols=4)
    assert result["predicted_class"] == "ITEM_TABLE"
    assert result["confidence"] in ("HIGH", "REVIEW")


def test_classify_tariff_origin_headers():
    headers = ["Tariff heading", "Country", "Quantity", "Weight"]
    result = classify_physical_segment(headers, n_rows=10, n_cols=4)
    assert result["predicted_class"] == "TARIFF_ORIGIN_SUMMARY"


def test_classify_totals_table():
    headers = ["Total", "Bruto", "Neto", "Payment"]
    result = classify_physical_segment(headers, n_rows=2, n_cols=4)
    assert result["predicted_class"] == "TOTALS_TABLE"


def test_classify_other_unknown():
    headers = ["RandomColumn1", "RandomColumn2"]
    result = classify_physical_segment(headers, n_rows=10, n_cols=2)
    assert result["predicted_class"] in ("OTHER", "UNRESOLVED")


def test_classify_with_diacritics():
    """Dijakritika u hederu treba biti normalizovana."""
    headers = ["Opis robe", "Količina", "Cijena", "Iznos"]
    result = classify_physical_segment(headers, n_rows=15, n_cols=4)
    assert result["predicted_class"] == "ITEM_TABLE"


def test_classify_empty_headers():
    headers = []
    result = classify_physical_segment(headers, n_rows=10, n_cols=3)
    assert result["predicted_class"] == "OTHER"


def test_classify_structural_hint_for_item():
    """Strukturni signali: rows >= 5 AND cols >= 5 → ITEM_TABLE boost."""
    headers = []  # bez headera
    result = classify_physical_segment(headers, n_rows=10, n_cols=7)
    # Samo strukturni, score 0.5 — ali predicted treba biti ITEM_TABLE ili UNRESOLVED
    assert result["predicted_class"] in ("ITEM_TABLE", "OTHER", "UNRESOLVED")


def test_classify_short_table_for_totals():
    """rows <= 5 → TOTALS boost."""
    headers = []
    result = classify_physical_segment(headers, n_rows=3, n_cols=4)
    # TOTALS score dobija +0.3, ali bez headera score=0 → predicted OTHER/UNRESOLVED
    assert result["scores"]["TOTALS_TABLE"] >= 0.3


def test_classify_includes_page_in_structure():
    headers = ["Item Code", "Description"]
    result = classify_physical_segment(headers, n_rows=20, n_cols=2, page=3)
    assert result["structure"]["page"] == 3


def test_classify_confidence_categories():
    """HIGH/REVIEW/UNRESOLVED kategorije."""
    # Strong ITEM
    r = classify_physical_segment(["Description", "Quantity", "Unit Price", "Amount", "Item Code"], n_rows=20, n_cols=5)
    assert r["confidence"] == "HIGH"
    # Weak — nema headera, nema signala
    r = classify_physical_segment([], n_rows=3, n_cols=1)
    assert r["confidence"] == "UNRESOLVED"

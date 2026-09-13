"""Unit testovi za invoice_meta_extractor."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "document_engines" / "benchmark"))

from invoice_meta_extractor import extract_invoice_meta


def test_extract_exporter():
    text = "Izvoznik / Exporter\n\nPEKABESKO d.o.o."
    meta = extract_invoice_meta(text)
    assert meta["exporter"] is not None
    assert "PEKABESKO" in meta["exporter"]


def test_extract_importer():
    text = "Uvoznik / Importer\n\nLEBURIC KOMERC d.o.o."
    meta = extract_invoice_meta(text)
    assert meta["importer"] is not None
    assert "LEBURIC" in meta["importer"]


def test_extract_invoice_number():
    text = "Broj fakture / Invoice No.: 01-2025"
    meta = extract_invoice_meta(text)
    assert meta["invoice_number"] is not None


def test_extract_invoice_date():
    text = "Datum fakture / Invoice date: 04.09.2025."
    meta = extract_invoice_meta(text)
    assert meta["invoice_date"] is not None
    assert "2025" in meta["invoice_date"]


def test_extract_currency():
    text = "Valuta: EUR"
    meta = extract_invoice_meta(text)
    assert meta["currency"] == "EUR"


def test_extract_incoterm():
    text = "Paritet: EXW Kadino"
    meta = extract_invoice_meta(text)
    assert meta["incoterm"] == "EXW"


def test_extract_bruto_kg():
    text = "Ukupno bruto: 10,800.00 kg"
    meta = extract_invoice_meta(text)
    assert meta["total_bruto_kg"] is not None


def test_extract_neto_kg():
    text = "Ukupno neto: 9,560.712 kg"
    meta = extract_invoice_meta(text)
    assert meta["total_neto_kg"] is not None


def test_extract_origin_statement():
    text = "Izjava o porijeklu: Proizvodi su porijeklom iz Makedonije"
    meta = extract_invoice_meta(text)
    assert meta["has_origin_statement"] is True


def test_extract_missing_fields():
    text = "Bilo šta bez invoice podataka"
    meta = extract_invoice_meta(text)
    assert meta["exporter"] is None
    assert meta["importer"] is None
    assert meta["invoice_number"] is None


def test_status_flags():
    text = "Izvoznik / Exporter\nPEKABESKO d.o.o."
    meta = extract_invoice_meta(text)
    assert meta["status"]["exporter"] == "FOUND"
    assert meta["status"]["importer"] == "MISSING_IN_SOURCE"

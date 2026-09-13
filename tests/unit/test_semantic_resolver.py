"""Unit testovi za Semantic Column Resolver."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "document_engines" / "benchmark"))

from semantic_resolver import resolve_role, resolve_columns, header_synonym_score, normalize_header


def test_normalize_header_lowercase():
    assert normalize_header("Naziv Robe") == "naziv robe"


def test_normalize_header_diacritics():
    assert normalize_header("Količina") == "kolicina"
    assert normalize_header("Šifra") == "sifra"


def test_header_synonym_score_exact():
    assert header_synonym_score("Naziv robe", "DESCRIPTION") == 1.0


def test_header_synonym_score_partial():
    score = header_synonym_score("Item Code", "PRODUCT_CODE")
    assert score >= 0.6


def test_header_synonym_score_no_match():
    assert header_synonym_score("Random", "DESCRIPTION") == 0.0


def test_resolve_role_description_clear():
    result = resolve_role("Description", ["Widget A", "Widget B", "Widget C"])
    assert result["role"] == "DESCRIPTION"
    assert result["confidence"] in ("HIGH", "REVIEW")


def test_resolve_role_quantity_clear():
    result = resolve_role("Quantity", ["10", "20", "30", "5"])
    assert result["role"] == "QUANTITY"


def test_resolve_role_unit_price_clear():
    result = resolve_role("Unit Price", ["5.50", "3.20", "4.10"])
    assert result["role"] == "UNIT_PRICE"


def test_resolve_role_line_amount_clear():
    result = resolve_role("Amount", ["55.00", "48.00", "82.00"])
    assert result["role"] == "LINE_AMOUNT"


def test_resolve_role_origin_clear():
    result = resolve_role("Country", ["DE", "IT", "CN"])
    assert result["role"] == "ORIGIN"


def test_resolve_role_unknown_headers():
    result = resolve_role("FooBar", ["X", "Y"])
    assert result["role"] == "UNKNOWN"
    assert result["confidence"] == "UNRESOLVED"


def test_resolve_columns_with_neighbor_conflict():
    """Dvije kolone sa istim DESCRIPTION ulogom → REVIEW."""
    columns = [
        {"header_text": "Description 1", "cells": ["A", "B"]},
        {"header_text": "Description 2", "cells": ["C", "D"]},
    ]
    results = resolve_columns(columns)
    assert len(results) == 2
    # Obje bi dobile DESCRIPTION, pa bi trebale imati REVIEW
    assert results[0]["confidence"] == "REVIEW"
    assert results[1]["confidence"] == "REVIEW"


def test_resolve_columns_mixed():
    columns = [
        {"header_text": "Item Code", "cells": ["001-401", "00175"]},
        {"header_text": "Description", "cells": ["Widget A", "Widget B"]},
        {"header_text": "Quantity", "cells": ["5", "10"]},
        {"header_text": "Unit Price", "cells": ["8.80", "1.95"]},
        {"header_text": "Total Amount", "cells": ["44.00", "19.50"]},
    ]
    results = resolve_columns(columns)
    roles = [r["role"] for r in results]
    assert "PRODUCT_CODE" in roles
    assert "DESCRIPTION" in roles
    assert "QUANTITY" in roles
    assert "UNIT_PRICE" in roles
    assert "LINE_AMOUNT" in roles

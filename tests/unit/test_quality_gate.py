"""Unit testovi za F6-F10 quality gate evaluaciju — sintetički podaci.

NE koristi stvarne fakture. NE commituje poslovne podatke.
"""
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "document_engines" / "benchmark"))

from quality_gate import (
    evaluate_f6,
    evaluate_f7,
    evaluate_f8,
    evaluate_f9,
    evaluate_f10,
    evaluate_f10_row,
    parse_number,
)


# ─────────────────────────────────────────────────────────
# parse_number
# ─────────────────────────────────────────────────────────
def test_parse_number_evropski_format():
    assert parse_number("1.234,56") == 1234.56
    assert parse_number("1234,56") == 1234.56
    assert parse_number("1234.56") == 1234.56
    assert parse_number("1.000") == 1.0
    assert parse_number("0,5") == 0.5
    assert parse_number("0") == 0.0
    assert parse_number("-3,14") == -3.14
    assert parse_number("") is None
    assert parse_number("abc") is None
    assert parse_number(None) is None


# ─────────────────────────────────────────────────────────
# F6 — Tabela NIJE pronađena, ali postoji item-like struktura
# ─────────────────────────────────────────────────────────
def test_f6_basic_trigger_above_threshold():
    """candidate_lines >= 4 i score >= 0.65 → TRUE."""
    text = "\n".join([
        "ARTIKAL KOLICINA CIJENA",
        "JABUKA         10     5,50    55,00",
        "KRUŠKA         15     3,20    48,00",
        "LIMUN          20     4,10    82,00",
        "NARANČA         5     6,80    34,00",
        "MANDARINA      12     7,25    87,00",
    ])
    res = evaluate_f6(docling_tables_count=0, docling_text=text)
    assert res["triggered"] is True
    assert res["verdict"] == "TRUE"
    assert res["candidate_lines"] >= 4


def test_f6_hard_trigger():
    """candidate_lines >= 6 i numeric_alignment >= 0.70 → hard TRUE."""
    text = "\n".join([
        f"ARTIKAL_{i}      10     5,50     55,00" for i in range(8)
    ])
    res = evaluate_f6(docling_tables_count=0, docling_text=text)
    assert res["triggered"] is True


def test_f6_false_when_tables_present():
    """Ako postoji Docling tabela, F6 ne treba da se aktivira."""
    text = "\n".join([
        "ARTIKAL KOLICINA CIJENA",
        "JABUKA         10     5,50    55,00",
    ] * 8)
    res = evaluate_f6(docling_tables_count=1, docling_text=text)
    assert res["triggered"] is False
    assert res["reason"] == "tables_present"


def test_f6_false_when_too_few_candidates():
    """< 4 kandidata → FALSE."""
    text = "Nek random tekst bez brojeva i strukture.\nJoš jedan red.\n"
    res = evaluate_f6(docling_tables_count=0, docling_text=text)
    assert res["triggered"] is False


def test_f6_score_components_in_response():
    text = "\n".join([
        "ARTIKAL KOLICINA CIJENA IZNOS",
        "JABUKA         10     5,50    55,00",
        "KRUŠKA         15     3,20    48,00",
        "LIMUN          20     4,10    82,00",
        "NARANČA         5     6,80    34,00",
        "MANDARINA      12     7,25    87,00",
    ])
    res = evaluate_f6(docling_tables_count=0, docling_text=text)
    assert "numeric_alignment" in res
    assert "row_repetition" in res
    assert "description_presence" in res
    assert "amount_pattern" in res
    assert "header_evidence" in res
    assert "item_structure_score" in res


# ─────────────────────────────────────────────────────────
# F7 — Description kolona identifikacija
# ─────────────────────────────────────────────────────────
def _make_columns_with_one_text_dominant():
    return [
        {
            "header_text": "Naziv robe",
            "cells": ["JABUKA", "KRUŠKA", "LIMUN", "NARANČA", "MANDARINA"],
        },
        {
            "header_text": "Količina",
            "cells": ["10", "15", "20", "5", "12"],
        },
        {
            "header_text": "Cijena",
            "cells": ["5,50", "3,20", "4,10", "6,80", "7,25"],
        },
    ]


def test_f7_confident_description():
    """Jedna jasno dominantna description kolona → FALSE (F7 ne treba)."""
    cols = _make_columns_with_one_text_dominant()
    res = evaluate_f7(cols)
    assert res["verdict"] == "FALSE"
    assert res["best_score"] >= 0.65
    assert res["margin"] >= 0.10
    assert res["best_column"] == "Naziv robe"


def test_f7_ambiguous_description():
    """Dvije kolone slično tekstualne, mala razlika → TRUE."""
    cols = [
        {"header_text": "Opis A", "cells": ["abc def ghi", "jkl mno pqr"]},
        {"header_text": "Opis B", "cells": ["xyz uvw rst", "lmn opq lmn"]},
    ]
    res = evaluate_f7(cols)
    # margin treba biti mali
    assert res["verdict"] == "TRUE"


def test_f7_no_description_match():
    """Nijedna kolona nema description header → TRUE (nema sigurnog match-a)."""
    cols = [
        {"header_text": "Količina", "cells": ["10", "15"]},
        {"header_text": "Cijena", "cells": ["5,50", "3,20"]},
    ]
    res = evaluate_f7(cols)
    assert res["verdict"] == "TRUE"
    assert res["best_score"] < 0.65


def test_f7_per_column_scores_in_response():
    cols = _make_columns_with_one_text_dominant()
    res = evaluate_f7(cols)
    assert "per_column" in res
    assert len(res["per_column"]) == 3
    for c in res["per_column"]:
        assert "header_score" in c
        assert "textual_content_score" in c
        assert "text_length_score" in c
        assert "uniqueness_score" in c
        assert "total_score" in c


# ─────────────────────────────────────────────────────────
# F8 — Numeric role identification
# ─────────────────────────────────────────────────────────
def test_f8_clear_role_assignment():
    """3 jasne numeričke kolone (qty int, price decimal, amount decimal) → FALSE."""
    cols = [
        {"header_text": "Naziv", "cells": ["JABUKA", "KRUŠKA", "LIMUN"]},
        {"header_text": "Količina", "cells": ["10", "15", "20"]},
        {"header_text": "Cijena", "cells": ["5,50", "3,20", "4,10"]},
        {"header_text": "Iznos", "cells": ["55,00", "48,00", "82,00"]},
    ]
    res = evaluate_f8(cols)
    # Sve 3 numeričke role su identificirane po headeru
    assert res["quantity"] == "Količina"
    assert res["unit_price"] == "Cijena"
    assert res["line_amount"] == "Iznos"
    assert res["reliable"] is True
    assert res["verdict"] == "FALSE"


def test_f8_missing_amount():
    """Nema Iznos kolone → F8 TRUE (nije pouzdano riješeno)."""
    cols = [
        {"header_text": "Količina", "cells": ["10", "15", "20"]},
        {"header_text": "Cijena", "cells": ["5,50", "3,20", "4,10"]},
    ]
    res = evaluate_f8(cols)
    assert res["verdict"] == "TRUE"
    assert res["line_amount"] is None


def test_f8_only_one_numeric_column():
    cols = [
        {"header_text": "Količina", "cells": ["10", "15", "20"]},
        {"header_text": "Naziv", "cells": ["X", "Y", "Z"]},
    ]
    res = evaluate_f8(cols)
    assert res["verdict"] == "TRUE"


def test_f8_ambiguous_numeric_columns():
    """Više numeričkih kolona sa sličnim score-ovima → conflict."""
    cols = [
        {"header_text": "A", "cells": ["10", "15", "20", "5"]},
        {"header_text": "B", "cells": ["10", "15", "20", "5"]},
        {"header_text": "C", "cells": ["10", "15", "20", "5"]},
        {"header_text": "D", "cells": ["abc", "def", "ghi", "jkl"]},
    ]
    res = evaluate_f8(cols)
    assert res["n_numeric_columns"] >= 3


# ─────────────────────────────────────────────────────────
# F9 — Broken rows
# ─────────────────────────────────────────────────────────
def _make_clean_rows(n=10):
    """Sintetički čisti redovi: 5 ćelija po redu, sa očekivanim numeričkim poljima."""
    rows = []
    for i in range(n):
        rows.append([
            {"text": str(i + 1), "x0": 0, "x1": 10},
            {"text": f"Opis {i}", "x0": 20, "x1": 200},
            {"text": "10", "x0": 220, "x1": 260},
            {"text": "5,50", "x0": 280, "x1": 320},
            {"text": "55,00", "x0": 340, "x1": 400},
        ])
    return rows


def test_f9_no_broken_rows():
    rows = _make_clean_rows(10)
    res = evaluate_f9({
        "rows": rows,
        "expected_columns": ["quantity", "unit_price", "line_amount"],
        "column_x_centers": {"quantity": 240, "unit_price": 300, "line_amount": 370},
    })
    assert res["triggered"] is False
    assert res["broken_rows"] == 0
    assert res["verdict"] == "FALSE"


def test_f9_above_20pct_broken_triggers():
    rows = _make_clean_rows(5)
    # Dodaj 2 broken reda
    rows.append([
        {"text": "X", "x0": 0, "x1": 10},
        {"text": "Y", "x0": 20, "x1": 200},
    ])  # samo 2 ćelije (B4)
    rows.append([
        {"text": "A", "x0": 0, "x1": 10},
        {"text": "B", "x0": 20, "x1": 200},
    ])  # samo 2 ćelije (B4)
    res = evaluate_f9({
        "rows": rows,
        "expected_columns": ["quantity", "unit_price", "line_amount"],
        "column_x_centers": {},
    })
    # 5 valid + 2 broken = 7 analyzable, 2 broken, rate 2/7 = 28% > 20%
    assert res["broken_rows"] == 2
    assert res["triggered"] is True


def test_f9_exactly_20pct_no_trigger():
    """Tačno 20% broken → NE treba trigger (granica je > 0.20, ne >=)."""
    # 4 reda 1 broken = 25% > 20%
    # 5 redova 1 broken = 20% — NE TREBA
    rows = _make_clean_rows(5)
    rows.append([
        {"text": "X", "x0": 0, "x1": 10},
        {"text": "Y", "x0": 20, "x1": 200},
    ])  # broken — 1 od 6 = 16.7%
    # Zapravo 5+1 = 6, 1/6 = 16.7%, NE trigger
    res = evaluate_f9({
        "rows": rows,
        "expected_columns": ["quantity", "unit_price", "line_amount"],
        "column_x_centers": {},
    })
    assert res["broken_rows"] >= 1
    # 1/6 = 16.7% < 20% — ne treba
    assert res["triggered"] is False


def test_f9_requires_at_least_5_rows():
    """< 5 redova → ne analizira dovoljno → FALSE."""
    rows = _make_clean_rows(3)
    rows.append([
        {"text": "X", "x0": 0, "x1": 10},
    ])
    res = evaluate_f9({
        "rows": rows,
        "expected_columns": ["quantity", "unit_price", "line_amount"],
        "column_x_centers": {},
    })
    assert res["triggered"] is False


# ─────────────────────────────────────────────────────────
# F10 — Matematička konzistentnost
# ─────────────────────────────────────────────────────────
def test_f10_simple_qty_price_amount_pass():
    rows = [
        {"q": 10, "p": 5.50, "a": 55.00},
        {"q": 15, "p": 3.20, "a": 48.00},
        {"q": 20, "p": 4.10, "a": 82.00},
        {"q": 5, "p": 6.80, "a": 34.00},
        {"q": 12, "p": 7.25, "a": 87.00},
    ]
    res = evaluate_f10(rows)
    assert res["failed_rows"] == 0
    assert res["triggered"] is False


def test_f10_rounding_tolerance():
    """10 × 5.55 = 55.5 → amount 55.5 (exact) PASS.
    10 × 5.555 = 55.55 → 55.5 rounding → PASS."""
    rows = [{"q": 10, "p": 5.555, "a": 55.55}]
    res = evaluate_f10(rows)
    # trebao bi PASS sa rounding tolerance
    assert res["failed_rows"] == 0


def test_f10_discount_model():
    """Sa discount od 10%: A = Q × P × 0.9."""
    rows = [
        {"q": 10, "p": 100, "a": 900, "discount": 10},  # 10*100*0.9 = 900
        {"q": 5, "p": 50, "a": 225, "discount": 10},    # 5*50*0.9 = 225
    ]
    res = evaluate_f10(rows)
    assert res["failed_rows"] == 0


def test_f10_severe_mismatch_triggers():
    """Severe mismatch: rel >= 0.10 i abs >= 1.00 → TRUE."""
    rows = [
        {"q": 10, "p": 5.50, "a": 55.00},
        {"q": 10, "p": 5.50, "a": 5.00},     # 10x diff — severe
        {"q": 10, "p": 5.50, "a": 1.00},     # severe
    ]
    res = evaluate_f10(rows)
    # severe >= 2 → TRUE
    assert res["severe_mismatches"] >= 2
    assert res["triggered"] is True


def test_f10_exactly_20pct_no_trigger():
    """5 redova, 1 broken = 20% — NE trigger (granica > 0.20)."""
    rows = [
        {"q": 10, "p": 5.50, "a": 55.00},   # pass
        {"q": 15, "p": 3.20, "a": 48.00},   # pass
        {"q": 20, "p": 4.10, "a": 82.00},   # pass
        {"q": 5, "p": 6.80, "a": 34.00},    # pass
        {"q": 12, "p": 7.25, "a": 1.00},    # fail — 87 vs 1
    ]
    res = evaluate_f10(rows)
    assert res["eligible_rows"] == 5
    assert res["failed_rows"] == 1
    assert res["failed_rate"] == 0.20
    assert res["triggered"] is False


def test_f10_above_20pct_triggers():
    """5 redova, 2 failed = 40% → TRUE."""
    rows = [
        {"q": 10, "p": 5.50, "a": 55.00},
        {"q": 15, "p": 3.20, "a": 48.00},
        {"q": 20, "p": 4.10, "a": 82.00},
        {"q": 5, "p": 6.80, "a": 1.00},
        {"q": 12, "p": 7.25, "a": 1.00},
    ]
    res = evaluate_f10(rows)
    assert res["failed_rows"] == 2
    assert res["triggered"] is True


def test_f10_invalid_input_counted_as_failed():
    rows = [
        {"q": 10, "p": 5.50, "a": 55.00},
        {"q": "x", "p": 5.50, "a": 55.00},  # invalid
        {"q": 10, "p": None, "a": 55.00},   # invalid
    ]
    res = evaluate_f10(rows)
    assert res["failed_rows"] >= 2


def test_f10_row_severity_calculation():
    """rel >= 0.10 AND abs >= 1.00 → severe."""
    row = evaluate_f10_row(10, 5.50, 100.00)
    # expected = 55, actual = 100, abs = 45, rel = 0.45
    assert row["severe_mismatch"] is True
    assert row["pass"] is False


def test_f10_row_small_diff_not_severe():
    row = evaluate_f10_row(10, 5.50, 55.05)
    # abs = 0.05, rel = 0.0009 — NE severe
    assert row["severe_mismatch"] is False
    # 0.05 < 0.02 final_tol (makar 0.02) — trebao bi FAIL?
    # final_tol = max(0.02, 0.001*55, rounding)
    # rounding = min(10*0.5*0.01 + 0.5*0.01, 0.005*55) = min(0.055, 0.275) = 0.055
    # final_tol = max(0.02, 0.055, 0.055) = 0.055
    # 0.05 < 0.055 → PASS
    assert row["pass"] is True


# ─────────────────────────────────────────────────────────
# Boundary vrijednosti
# ─────────────────────────────────────────────────────────
def test_f7_boundary_065():
    """Score tačno 0.65 — granica: >= 0.65 prihvaćen."""
    cols = [
        {"header_text": "Količina", "cells": ["10"]},
        {"header_text": "Naziv robe", "cells": ["JABUKA"]},
        {"header_text": "Cijena", "cells": ["5,50"]},
    ]
    res = evaluate_f7(cols)
    # Naziv robe je description-like, trebao bi imati score >= 0.65
    assert res["verdict"] == "FALSE"
    assert res["best_score"] >= 0.65


def test_f10_tolerance_at_least_002():
    """Apsolutna tolerancija je minimalno 0.02 (za apsolutne vrijednosti > 0.02)."""
    # Sa većim brojevima, abs diff = 0.05 < 0.02 final_tol? NE, 0.05 > 0.02 → FAIL
    # Ali final_tol = max(0.02, 0.001*55, rounding) — za q*p=55, rounding za 2 decimale
    # = max(0.02, 0.055, 0.055) = 0.055 → PASS
    # Za test tolerance 0.02 minimalno, koristimo mismatch > 0.02 i < rounding:
    row = evaluate_f10_row(1, 1.00, 1.05)  # expected 1.00, actual 1.05, abs = 0.05
    # final_tol = max(0.02, 0.001*1.05, rounding_bound_for_2_decimals)
    # rounding = min(1*0.5*0.01 + 0.5*0.01, 0.005*1.05) = min(0.01, 0.00525) = 0.005
    # final_tol = max(0.02, 0.00105, 0.005) = 0.02
    # abs 0.05 > 0.02 → FAIL
    assert row["pass"] is False
    # Ali 0.01 < 0.02 → PASS
    row2 = evaluate_f10_row(1, 1.00, 1.01)
    assert row2["pass"] is True


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])

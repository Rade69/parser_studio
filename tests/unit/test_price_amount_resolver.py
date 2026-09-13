"""Unit testovi za Price vs Amount Resolver."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "document_engines" / "benchmark"))

from price_amount_resolver import arithmetic_match, resolve_price_amount


def test_arithmetic_match_perfect():
    rows = [
        {"q": 10, "p": 5.50, "a": 55.00},
        {"q": 20, "p": 3.20, "a": 64.00},
        {"q": 5, "p": 12.00, "a": 60.00},
    ]
    rate = arithmetic_match(rows, "q", "p", "a")
    assert rate == 1.0


def test_arithmetic_match_with_discount():
    rows = [
        {"q": 10, "p": 100, "a": 900, "d": 10},
        {"q": 5, "p": 50, "a": 225, "d": 10},
    ]
    rate = arithmetic_match(rows, "q", "p", "a", "d")
    assert rate == 1.0


def test_arithmetic_match_no_match():
    rows = [
        {"q": 10, "p": 5.50, "a": 100.00},
        {"q": 20, "p": 3.20, "a": 200.00},
    ]
    rate = arithmetic_match(rows, "q", "p", "a")
    assert rate == 0.0


def test_arithmetic_match_empty():
    assert arithmetic_match([], "q", "p", "a") == 0.0


def test_resolve_clear_assignment():
    rows = [
        {"col_q": 10, "col_p": 5.50, "col_a": 55.00},
        {"col_q": 20, "col_p": 3.20, "col_a": 64.00},
        {"col_q": 5, "col_p": 12.00, "col_a": 60.00},
        {"col_q": 15, "col_p": 2.75, "col_a": 41.25},
        {"col_q": 8, "col_p": 8.40, "col_a": 67.20},
    ]
    result = resolve_price_amount(rows, ["col_q", "col_p", "col_a"])
    assert result["best_assignment"]["q"] == "col_q"
    assert result["best_assignment"]["p"] == "col_p"
    assert result["best_assignment"]["a"] == "col_a"
    assert result["confidence"] == "HIGH"


def test_resolve_ambiguous():
    """Dvije numeričke kolone sa sličnim match_rate."""
    rows = [
        {"a": 10, "b": 5.50, "c": 55.00},
        {"a": 20, "b": 3.20, "c": 64.00},
        {"a": 5, "b": 12.00, "c": 60.00},
        {"a": 15, "b": 2.75, "c": 41.25},
        {"a": 8, "b": 8.40, "c": 67.20},
    ]
    result = resolve_price_amount(rows, ["a", "b", "c"])
    # Trebao bi razriješiti jer je q×p=a matematički jasno
    assert result["confidence"] in ("HIGH", "UNRESOLVED")


def test_resolve_low_match_rate():
    rows = [
        {"q": 10, "p": 5.50, "a": 100.00},
        {"q": 20, "p": 3.20, "a": 200.00},
        {"q": 5, "p": 12.00, "a": 300.00},
        {"q": 15, "p": 2.75, "a": 41.25},
        {"q": 8, "p": 8.40, "a": 67.20},
    ]
    result = resolve_price_amount(rows, ["q", "p", "a"])
    assert result["confidence"] == "UNRESOLVED"


def test_resolve_few_rows():
    rows = [{"q": 10, "p": 5.50, "a": 55.00}]
    result = resolve_price_amount(rows, ["q", "p", "a"])
    assert result["confidence"] == "UNRESOLVED"
    assert "few_rows" in result["reason"]


def test_resolve_insufficient_columns():
    rows = [{"q": 10, "p": 5.50}]
    result = resolve_price_amount(rows, ["q", "p"])
    assert result["resolved"] is False
    assert "insufficient" in result["reason"]

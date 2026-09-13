"""Unit testovi za Table Stitcher."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "document_engines" / "benchmark"))

from table_stitcher import (
    headers_match_strict,
    headers_match_fuzzy,
    can_stitch,
    stitch_physical_segments,
)


def test_headers_match_strict_identical():
    assert headers_match_strict(["Item", "Quantity"], ["Item", "Quantity"]) is True


def test_headers_match_strict_different():
    assert headers_match_strict(["Item", "Quantity"], ["Description", "Quantity"]) is False


def test_headers_match_strict_different_length():
    assert headers_match_strict(["Item", "Quantity"], ["Item"]) is False


def test_headers_match_fuzzy_partial():
    score = headers_match_fuzzy(["Item", "Quantity", "Price"], ["Item", "Quantity", "Cost"])
    assert score >= 0.6  # 2/3 match


def test_headers_match_fuzzy_zero():
    score = headers_match_fuzzy(["X", "Y"], ["A", "B"])
    assert score == 0.0


def test_can_stitch_same_class_same_headers():
    seg1 = {"predicted_class": "ITEM_TABLE", "headers_raw": ["Item", "Qty"], "structure": {"page": 1, "n_cols": 2}}
    seg2 = {"predicted_class": "ITEM_TABLE", "headers_raw": ["Item", "Qty"], "structure": {"page": 2, "n_cols": 2}}
    can, reason = can_stitch(seg1, seg2)
    assert can is True


def test_can_stitch_different_class():
    seg1 = {"predicted_class": "ITEM_TABLE", "headers_raw": ["Item", "Qty"], "structure": {"page": 1, "n_cols": 2}}
    seg2 = {"predicted_class": "TARIFF_ORIGIN_SUMMARY", "headers_raw": ["Tariff", "Country"], "structure": {"page": 2, "n_cols": 2}}
    can, reason = can_stitch(seg1, seg2)
    assert can is False
    assert "different_class" in reason


def test_can_stitch_different_headers():
    seg1 = {"predicted_class": "ITEM_TABLE", "headers_raw": ["Item", "Qty"], "structure": {"page": 1, "n_cols": 2}}
    seg2 = {"predicted_class": "ITEM_TABLE", "headers_raw": ["Description", "Quantity"], "structure": {"page": 2, "n_cols": 2}}
    can, reason = can_stitch(seg1, seg2)
    assert can is False
    assert "headers" in reason


def test_can_stitch_n_cols_mismatch():
    seg1 = {"predicted_class": "ITEM_TABLE", "headers_raw": ["Item", "Qty"], "structure": {"page": 1, "n_cols": 2}}
    seg2 = {"predicted_class": "ITEM_TABLE", "headers_raw": ["Item", "Qty"], "structure": {"page": 2, "n_cols": 5}}
    can, reason = can_stitch(seg1, seg2)
    assert can is False
    assert "n_cols_mismatch" in reason


def test_stitch_three_segments_into_one():
    segs = [
        {"segment_index": 0, "predicted_class": "ITEM_TABLE", "headers_raw": ["Item", "Qty"], "structure": {"page": 1, "n_cols": 2}, "reason": "ok"},
        {"segment_index": 1, "predicted_class": "ITEM_TABLE", "headers_raw": ["Item", "Qty"], "structure": {"page": 2, "n_cols": 2}, "reason": "ok"},
        {"segment_index": 2, "predicted_class": "ITEM_TABLE", "headers_raw": ["Item", "Qty"], "structure": {"page": 3, "n_cols": 2}, "reason": "ok"},
    ]
    logical = stitch_physical_segments(segs)
    assert len(logical) == 1
    assert logical[0]["segments"] == [0, 1, 2]


def test_stitch_split_at_class_change():
    segs = [
        {"segment_index": 0, "predicted_class": "ITEM_TABLE", "headers_raw": ["Item", "Qty"], "structure": {"page": 1, "n_cols": 2}, "reason": "ok"},
        {"segment_index": 1, "predicted_class": "TARIFF_ORIGIN_SUMMARY", "headers_raw": ["Tariff", "Country"], "structure": {"page": 3, "n_cols": 2}, "reason": "ok"},
    ]
    logical = stitch_physical_segments(segs)
    assert len(logical) == 2


def test_stitch_empty():
    assert stitch_physical_segments([]) == []


def test_stitch_single_segment():
    segs = [{"segment_index": 0, "predicted_class": "ITEM_TABLE", "headers_raw": ["Item"], "structure": {"page": 1, "n_cols": 1}, "reason": "ok"}]
    logical = stitch_physical_segments(segs)
    assert len(logical) == 1
    assert logical[0]["segments"] == [0]


def test_stitch_no_wrong_class_join():
    """ITEM i TARIFF_ORIGIN se NE smiju spojiti."""
    segs = [
        {"segment_index": 0, "predicted_class": "ITEM_TABLE", "headers_raw": ["Item", "Qty"], "structure": {"page": 1, "n_cols": 2}, "reason": "ok"},
        {"segment_index": 1, "predicted_class": "TARIFF_ORIGIN_SUMMARY", "headers_raw": ["Tariff", "Country"], "structure": {"page": 2, "n_cols": 2}, "reason": "ok"},
        {"segment_index": 2, "predicted_class": "TARIFF_ORIGIN_SUMMARY", "headers_raw": ["Tariff", "Country"], "structure": {"page": 3, "n_cols": 2}, "reason": "ok"},
    ]
    logical = stitch_physical_segments(segs)
    # 1 ITEM + 2 stitched TARIFF
    assert len(logical) == 2
    assert logical[0]["predicted_class"] == "ITEM_TABLE"
    assert logical[1]["predicted_class"] == "TARIFF_ORIGIN_SUMMARY"
    assert logical[1]["segments"] == [1, 2]


def test_page_continuity():
    """Susjedne stranice: 1->2 ok, 1->3 ok, ali 2->1 fail (regression), 1->1 fail."""
    seg1 = {"predicted_class": "ITEM_TABLE", "headers_raw": ["Item", "Qty"], "structure": {"page": 1, "n_cols": 2}}
    seg2 = {"predicted_class": "ITEM_TABLE", "headers_raw": ["Item", "Qty"], "structure": {"page": 2, "n_cols": 2}}
    can, _ = can_stitch(seg1, seg2)
    assert can is True
    seg3 = {"predicted_class": "ITEM_TABLE", "headers_raw": ["Item", "Qty"], "structure": {"page": 1, "n_cols": 2}}
    can, reason = can_stitch(seg1, seg3)
    assert can is False
    # Ista stranica ne znači progresiju; očekuj fail
    assert "page" in reason.lower() or "progression" in reason.lower()


def test_repeated_headers_across_pages():
    """Ponovljeni header je signal za stitch."""
    seg1 = {"predicted_class": "ITEM_TABLE", "headers_raw": ["Item Code", "Description", "Quantity"], "structure": {"page": 1, "n_cols": 3}}
    seg2 = {"predicted_class": "ITEM_TABLE", "headers_raw": ["Item Code", "Description", "Quantity"], "structure": {"page": 2, "n_cols": 3}}
    can, reason = can_stitch(seg1, seg2)
    assert can is True
    assert "headers_match" in reason

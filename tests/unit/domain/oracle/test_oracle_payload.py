"""Unit testovi za OraclePayload (vendor-agnostički)."""
from __future__ import annotations

import pytest

from parser_studio.domain.oracle import OracleItem, OraclePayload


class TestOracleItem:
    def test_minimal_item(self):
        item = OracleItem(line_no=1)
        assert item.line_no == 1
        assert item.description == ""
        assert item.quantity == 0.0
        assert item.line_amount == 0.0

    def test_full_item(self):
        item = OracleItem(
            line_no=5,
            description="Widget",
            quantity=10.0,
            unit_price=5.0,
            line_amount=50.0,
            hs_code="8473.30",
            origin_country="BA",
            uom="kom",
            gross_weight_kg=2.5,
            net_weight_kg=2.0,
            product_code="WID-001",
        )
        assert item.line_no == 5
        assert item.description == "Widget"
        assert item.line_amount == 50.0
        assert item.hs_code == "8473.30"

    def test_negative_line_no_raises(self):
        with pytest.raises(ValueError) as exc_info:
            OracleItem(line_no=-1)
        assert "line_no" in str(exc_info.value).lower()


class TestOraclePayload:
    def test_minimal_payload(self):
        payload = OraclePayload()
        assert payload.invoice_number == ""
        assert payload.items == ()
        assert payload.is_empty() is True

    def test_full_payload(self):
        items = (
            OracleItem(line_no=1, description="A", line_amount=10.0),
            OracleItem(line_no=2, description="B", line_amount=20.0),
        )
        payload = OraclePayload(
            invoice_number="INV-001",
            invoice_total=30.0,
            currency="EUR",
            items=items,
            source_strategy="ExcelStrategy",
            source_priority=10,
        )
        assert payload.invoice_number == "INV-001"
        assert payload.invoice_total == 30.0
        assert len(payload.items) == 2
        assert payload.is_empty() is False

    def test_negative_invoice_total_raises(self):
        with pytest.raises(ValueError) as exc_info:
            OraclePayload(invoice_total=-1.0)
        assert "invoice_total" in str(exc_info.value).lower()

    def test_is_empty_no_invoice_no_items_no_total(self):
        """is_empty=True kad nema invoice_number, items, ni total."""
        p = OraclePayload()
        assert p.is_empty() is True

    def test_is_empty_false_with_invoice_number(self):
        p = OraclePayload(invoice_number="X")
        assert p.is_empty() is False

    def test_is_empty_false_with_items(self):
        p = OraclePayload(items=(OracleItem(line_no=1),))
        assert p.is_empty() is False

    def test_is_empty_false_with_total(self):
        p = OraclePayload(invoice_total=1.0)
        assert p.is_empty() is False


class TestOraclePayloadGetField:
    def test_get_known_field(self):
        p = OraclePayload(invoice_number="INV-1", currency="EUR")
        assert p.get_field("invoice_number") == "INV-1"
        assert p.get_field("currency") == "EUR"

    def test_get_unknown_field_returns_none(self):
        p = OraclePayload()
        assert p.get_field("totally_unknown_field") is None

    def test_get_item_field_with_valid_item(self):
        items = (OracleItem(line_no=1, description="X"),)
        p = OraclePayload(items=items)
        assert p.get_item_field(1, "description") == "X"

    def test_get_item_field_missing_line_no(self):
        p = OraclePayload(items=(OracleItem(line_no=1),))
        assert p.get_item_field(99, "description") is None

    def test_get_item_field_missing_field(self):
        p = OraclePayload(items=(OracleItem(line_no=1, description="X"),))
        assert p.get_item_field(1, "totally_unknown") is None
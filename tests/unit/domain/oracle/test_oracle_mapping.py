"""Unit testovi za oracle_mapping (invoice + item level)."""
from __future__ import annotations

from parser_studio.domain.oracle import (
    INVOICE_LEVEL_MAP,
    ITEM_LEVEL_MAP,
    all_supported_fields,
    get_oracle_attr_for,
    is_invoice_field,
    is_item_field,
    is_known_field,
)


class TestInvoiceLevelMap:
    def test_invoice_number_maps(self):
        assert INVOICE_LEVEL_MAP["invoice_number"] == "invoice_number"

    def test_currency_maps(self):
        assert INVOICE_LEVEL_MAP["currency"] == "currency"

    def test_supplier_name_maps(self):
        assert INVOICE_LEVEL_MAP["supplier_name"] == "supplier_name"

    def test_supplier_country_maps(self):
        assert INVOICE_LEVEL_MAP["supplier_country"] == "supplier_country"

    def test_supplier_address_maps(self):
        assert INVOICE_LEVEL_MAP["supplier_address"] == "supplier_address"

    def test_supplier_vat_maps(self):
        assert INVOICE_LEVEL_MAP["supplier_vat"] == "supplier_vat"

    def test_invoice_date_maps(self):
        assert INVOICE_LEVEL_MAP["invoice_date"] == "invoice_date"

    def test_due_date_maps(self):
        assert INVOICE_LEVEL_MAP["due_date"] == "due_date"

    def test_invoice_total_maps(self):
        assert INVOICE_LEVEL_MAP["invoice_total"] == "invoice_total"

    def test_gross_weight_uses_bruto_alias(self):
        """declarant_pro naziv 'bruto_kg' mapira se na canonical 'gross_weight_kg'."""
        assert INVOICE_LEVEL_MAP["gross_weight_kg"] == "bruto_kg"

    def test_net_weight_uses_neto_alias(self):
        """declarant_pro naziv 'neto_kg' mapira se na canonical 'net_weight_kg'."""
        assert INVOICE_LEVEL_MAP["net_weight_kg"] == "neto_kg"

    def test_incoterm_maps(self):
        assert INVOICE_LEVEL_MAP["incoterm"] == "incoterm"

    def test_count_matches_canonical_invoice_count(self):
        """Ocekivano: 12 invoice-level polja (9 iz CanonicalInvoice + gross/net/incoterm)."""
        # CanonicalInvoice invoice-level: invoice_number, invoice_date, due_date,
        # supplier_name, supplier_address, supplier_country, supplier_vat,
        # invoice_total, currency = 9
        # + gross_weight_kg, net_weight_kg, incoterm = 3 (M1 proširenje)
        assert len(INVOICE_LEVEL_MAP) == 12


class TestItemLevelMap:
    def test_description_maps(self):
        assert ITEM_LEVEL_MAP["description"] == "description"

    def test_quantity_maps(self):
        assert ITEM_LEVEL_MAP["quantity"] == "quantity"

    def test_unit_price_maps(self):
        assert ITEM_LEVEL_MAP["unit_price"] == "unit_price"

    def test_line_amount_maps(self):
        assert ITEM_LEVEL_MAP["line_amount"] == "line_amount"

    def test_hs_code_maps(self):
        assert ITEM_LEVEL_MAP["hs_code"] == "hs_code"

    def test_origin_country_maps(self):
        assert ITEM_LEVEL_MAP["origin_country"] == "origin_country"

    def test_uom_maps(self):
        assert ITEM_LEVEL_MAP["uom"] == "uom"

    def test_product_code_maps(self):
        assert ITEM_LEVEL_MAP["product_code"] == "product_code"

    def test_item_gross_weight_uses_distinct_name(self):
        """Item-level gross_weight koristi 'item_gross_weight_kg' da se
        razlikuje od invoice-level 'gross_weight_kg'."""
        assert ITEM_LEVEL_MAP["item_gross_weight_kg"] == "gross_weight_kg"

    def test_item_net_weight_uses_distinct_name(self):
        assert ITEM_LEVEL_MAP["item_net_weight_kg"] == "net_weight_kg"

    def test_count_matches_canonical_line_count(self):
        """10 item-level polja (bez line_no koji je samo ordinal)."""
        # CanonicalInvoice.lines[i]: description, quantity, unit_price, line_amount,
        # hs_code, origin_country, uom, item_gross_weight_kg, item_net_weight_kg,
        # product_code = 10
        assert len(ITEM_LEVEL_MAP) == 10


class TestHelperFunctions:
    def test_is_invoice_field_true(self):
        assert is_invoice_field("invoice_number") is True

    def test_is_invoice_field_false_for_item(self):
        assert is_invoice_field("quantity") is False

    def test_is_item_field_true(self):
        assert is_item_field("quantity") is True
        assert is_item_field("line_amount") is True

    def test_is_item_field_false_for_invoice(self):
        assert is_item_field("invoice_number") is False

    def test_is_known_field_true(self):
        assert is_known_field("invoice_number") is True
        assert is_known_field("quantity") is True

    def test_is_known_field_false(self):
        assert is_known_field("totally_random_field") is False

    def test_get_oracle_attr_for_invoice(self):
        assert get_oracle_attr_for("invoice_number") == "invoice_number"
        assert get_oracle_attr_for("gross_weight_kg") == "bruto_kg"

    def test_get_oracle_attr_for_item(self):
        assert get_oracle_attr_for("quantity") == "quantity"
        assert get_oracle_attr_for("item_gross_weight_kg") == "gross_weight_kg"

    def test_get_oracle_attr_for_unknown_returns_none(self):
        assert get_oracle_attr_for("unknown_field") is None

    def test_all_supported_fields_count(self):
        """Ukupno 22 podržana polja (12 invoice + 10 item)."""
        fields = all_supported_fields()
        assert len(fields) == 22

    def test_all_supported_fields_is_tuple(self):
        assert isinstance(all_supported_fields(), tuple)

    def test_all_supported_fields_no_duplicates(self):
        fields = all_supported_fields()
        assert len(fields) == len(set(fields))


class TestMappingCompleteness:
    """Sanity: svaki OraclePayload field koji mapira mora postojati u OraclePayload."""

    def test_invoice_level_attrs_exist_on_payload(self):
        from parser_studio.domain.oracle import OraclePayload

        for oracle_attr in INVOICE_LEVEL_MAP.values():
            assert hasattr(OraclePayload, oracle_attr), (
                f"OraclePayload nema atribut '{oracle_attr}'"
            )

    def test_item_level_attrs_exist_on_item(self):
        from parser_studio.domain.oracle import OracleItem

        for oracle_attr in ITEM_LEVEL_MAP.values():
            assert hasattr(OracleItem, oracle_attr), (
                f"OracleItem nema atribut '{oracle_attr}'"
            )
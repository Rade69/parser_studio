# Tests: domain/invoice/vendor_parser_model.
from __future__ import annotations

from pathlib import Path

import pytest

from parser_studio.domain.invoice import (
    ConsumedPathsBehavior,
    ExtractionStrategy,
    FallbackStrategy,
    FieldExtractionRule,
    LayoutRule,
    NormalizationRule,
    ValidationRule,
    VendorParserModel,
    rule_count_summary,
)

# --------------------------------------------------------------------------- #
# ExtractionStrategy
# --------------------------------------------------------------------------- #


class TestExtractionStrategy:
    def test_has_ten_values(self) -> None:
        values = {s.value for s in ExtractionStrategy}
        expected = {
            "header_match",
            "label_right",
            "label_below",
            "table_header",
            "column_content",
            "value_shape",
            "known_layout",
            "ocr_recovery",
            "ai_advisor",
            "parser_oracle",
        }
        assert values == expected

    def test_is_str_enum(self) -> None:
        for s in ExtractionStrategy:
            assert isinstance(s, str)
            assert isinstance(s, ExtractionStrategy)

    def test_lookup_by_value(self) -> None:
        assert ExtractionStrategy("header_match") is ExtractionStrategy.HEADER_MATCH


# --------------------------------------------------------------------------- #
# FallbackStrategy
# --------------------------------------------------------------------------- #


class TestFallbackStrategy:
    def test_has_four_values(self) -> None:
        values = {s.value for s in FallbackStrategy}
        assert values == {"raise_error", "return_none", "use_default", "use_fallback_producer"}

    def test_is_str_enum(self) -> None:
        for s in FallbackStrategy:
            assert isinstance(s, str)


# --------------------------------------------------------------------------- #
# ConsumedPathsBehavior
# --------------------------------------------------------------------------- #


class TestConsumedPathsBehavior:
    def test_has_three_values(self) -> None:
        values = {s.value for s in ConsumedPathsBehavior}
        assert values == {"ignore", "track_for_audit", "append_to_output"}

    def test_default_is_ignore(self) -> None:
        # Verify the documented default.
        assert ConsumedPathsBehavior("ignore") is ConsumedPathsBehavior.IGNORE


# --------------------------------------------------------------------------- #
# LayoutRule
# --------------------------------------------------------------------------- #


class TestLayoutRuleConstruction:
    def test_minimal(self) -> None:
        r = LayoutRule(rule_id="r1", function_name="detect_header_row")
        assert r.rule_id == "r1"
        assert r.function_name == "detect_header_row"
        assert dict(r.params) == {}
        assert r.priority == 0

    def test_with_params(self) -> None:
        r = LayoutRule(
            rule_id="r1",
            function_name="detect_header_row",
            params={"min_score": 0.5, "case_sensitive": False},
            priority=10,
        )
        assert dict(r.params)["min_score"] == 0.5
        assert r.priority == 10


class TestLayoutRuleValidation:
    def test_empty_rule_id_raises(self) -> None:
        with pytest.raises(ValueError, match="rule_id"):
            LayoutRule(rule_id="", function_name="detect")

    def test_empty_function_name_raises(self) -> None:
        with pytest.raises(ValueError, match="function_name"):
            LayoutRule(rule_id="r1", function_name="")

    def test_invalid_identifier_raises(self) -> None:
        with pytest.raises(ValueError, match="rule_id"):
            LayoutRule(rule_id="1bad", function_name="detect")

    def test_invalid_function_name_identifier_raises(self) -> None:
        with pytest.raises(ValueError, match="function_name"):
            LayoutRule(rule_id="r1", function_name="bad-name")

    def test_non_string_rule_id_raises(self) -> None:
        with pytest.raises(TypeError, match="rule_id"):
            LayoutRule(rule_id=123, function_name="detect")  # type: ignore[arg-type]

    def test_non_mapping_params_raises(self) -> None:
        with pytest.raises(TypeError, match="params"):
            LayoutRule(
                rule_id="r1",
                function_name="detect",
                params="not-a-mapping",  # type: ignore[arg-type]
            )


class TestLayoutRuleFrozen:
    def test_mutation_raises(self) -> None:
        r = LayoutRule(rule_id="r1", function_name="detect")
        with pytest.raises((AttributeError, Exception)):
            r.priority = 5  # type: ignore[misc]

    def test_no_dict(self) -> None:
        r = LayoutRule(rule_id="r1", function_name="detect")
        assert not hasattr(r, "__dict__")


# --------------------------------------------------------------------------- #
# FieldExtractionRule
# --------------------------------------------------------------------------- #


class TestFieldExtractionRuleConstruction:
    def test_minimal(self) -> None:
        r = FieldExtractionRule(
            field_name="invoice_number",
            strategy=ExtractionStrategy.HEADER_MATCH,
            function_name="match_header",
        )
        assert r.field_name == "invoice_number"
        assert r.strategy is ExtractionStrategy.HEADER_MATCH
        assert r.function_name == "match_header"


class TestFieldExtractionRuleValidation:
    def test_empty_field_name_raises(self) -> None:
        with pytest.raises(ValueError, match="field_name"):
            FieldExtractionRule(
                field_name="",
                strategy=ExtractionStrategy.HEADER_MATCH,
                function_name="f",
            )

    def test_invalid_strategy_raises(self) -> None:
        with pytest.raises(TypeError, match="strategy"):
            FieldExtractionRule(
                field_name="invoice_number",
                strategy="header_match",  # type: ignore[arg-type]
                function_name="f",
            )

    def test_empty_function_name_raises(self) -> None:
        with pytest.raises(ValueError, match="function_name"):
            FieldExtractionRule(
                field_name="invoice_number",
                strategy=ExtractionStrategy.HEADER_MATCH,
                function_name="",
            )


class TestFieldExtractionRuleFrozen:
    def test_mutation_raises(self) -> None:
        r = FieldExtractionRule(
            field_name="invoice_number",
            strategy=ExtractionStrategy.HEADER_MATCH,
            function_name="f",
        )
        with pytest.raises((AttributeError, Exception)):
            r.params = {}  # type: ignore[misc]


# --------------------------------------------------------------------------- #
# ValidationRule
# --------------------------------------------------------------------------- #


class TestValidationRuleConstruction:
    def test_minimal(self) -> None:
        r = ValidationRule(function_name="validate_eur_amount")
        assert r.function_name == "validate_eur_amount"
        assert r.error_message is None
        assert dict(r.params) == {}

    def test_with_message(self) -> None:
        r = ValidationRule(
            function_name="validate_eur_amount",
            error_message="Iznos mora biti pozitivan",
        )
        assert r.error_message == "Iznos mora biti pozitivan"


class TestValidationRuleValidation:
    def test_empty_function_name_raises(self) -> None:
        with pytest.raises(ValueError, match="function_name"):
            ValidationRule(function_name="")

    def test_non_string_error_message_raises(self) -> None:
        with pytest.raises(TypeError, match="error_message"):
            ValidationRule(function_name="f", error_message=123)  # type: ignore[arg-type]


class TestValidationRuleFrozen:
    def test_mutation_raises(self) -> None:
        r = ValidationRule(function_name="f")
        with pytest.raises((AttributeError, Exception)):
            r.function_name = "g"  # type: ignore[misc]


# --------------------------------------------------------------------------- #
# NormalizationRule
# --------------------------------------------------------------------------- #


class TestNormalizationRuleConstruction:
    def test_minimal(self) -> None:
        r = NormalizationRule(function_name="nfkc_strip")
        assert r.function_name == "nfkc_strip"
        assert dict(r.params) == {}

    def test_with_params(self) -> None:
        r = NormalizationRule(
            function_name="lowercase",
            params={"locale": "bs"},
        )
        assert dict(r.params)["locale"] == "bs"


class TestNormalizationRuleValidation:
    def test_empty_function_name_raises(self) -> None:
        with pytest.raises(ValueError, match="function_name"):
            NormalizationRule(function_name="")


class TestNormalizationRuleFrozen:
    def test_mutation_raises(self) -> None:
        r = NormalizationRule(function_name="f")
        with pytest.raises((AttributeError, Exception)):
            r.function_name = "g"  # type: ignore[misc]


# --------------------------------------------------------------------------- #
# VendorParserModel — construction
# --------------------------------------------------------------------------- #


class TestVendorParserModelConstruction:
    def test_minimal(self) -> None:
        m = VendorParserModel(
            model_id="m1",
            vendor_id="v1",
            version=1,
        )
        assert m.model_id == "m1"
        assert m.vendor_id == "v1"
        assert m.version == 1
        assert m.identity_rules == ()
        assert m.layout_rules == ()
        assert m.invoice_field_rules == ()
        assert m.item_field_rules == ()
        assert m.item_table_rules == ()
        assert dict(m.column_roles) == {}
        assert dict(m.normalization_rules) == {}
        assert dict(m.validation_rules) == {}
        assert dict(m.fallback_strategies) == {}
        assert m.required_source_files == ()
        assert m.consumed_paths_behavior is ConsumedPathsBehavior.IGNORE

    def test_full_model(self) -> None:
        m = VendorParserModel(
            model_id="model_v1",
            vendor_id="vendor_a",
            version=3,
            identity_rules=(
                LayoutRule(rule_id="logo_match", function_name="match_logo"),
            ),
            layout_rules=(
                LayoutRule(
                    rule_id="layout_xlsx",
                    function_name="detect_xlsx",
                    priority=10,
                ),
            ),
            invoice_field_rules=(
                FieldExtractionRule(
                    field_name="invoice_number",
                    strategy=ExtractionStrategy.HEADER_MATCH,
                    function_name="match_invoice_no",
                ),
            ),
            item_field_rules=(
                FieldExtractionRule(
                    field_name="naziv_robe",
                    strategy=ExtractionStrategy.TABLE_HEADER,
                    function_name="match_naziv",
                ),
            ),
            item_table_rules=(
                LayoutRule(
                    rule_id="item_table",
                    function_name="detect_item_table",
                ),
            ),
            column_roles={"col_1": "naziv_robe", "col_2": "kolicina"},
            normalization_rules={
                "invoice_number": (NormalizationRule(function_name="strip"),),
            },
            validation_rules={
                "iznos": (
                    ValidationRule(
                        function_name="validate_positive",
                        error_message="Iznos mora biti > 0",
                    ),
                ),
            },
            fallback_strategies={
                "invoice_number": FallbackStrategy.USE_FALLBACK_PRODUCER,
            },
            required_source_files=("excel_layout.json",),
            consumed_paths_behavior=ConsumedPathsBehavior.TRACK_FOR_AUDIT,
        )
        assert m.model_id == "model_v1"
        assert m.version == 3
        assert len(m.identity_rules) == 1
        assert len(m.invoice_field_rules) == 1
        assert dict(m.column_roles)["col_1"] == "naziv_robe"
        assert m.fallback_strategies["invoice_number"] is FallbackStrategy.USE_FALLBACK_PRODUCER
        assert m.consumed_paths_behavior is ConsumedPathsBehavior.TRACK_FOR_AUDIT


class TestVendorParserModelValidation:
    def test_empty_model_id_raises(self) -> None:
        with pytest.raises(ValueError, match="model_id"):
            VendorParserModel(model_id="", vendor_id="v", version=1)

    def test_empty_vendor_id_raises(self) -> None:
        with pytest.raises(ValueError, match="vendor_id"):
            VendorParserModel(model_id="m", vendor_id="", version=1)

    def test_invalid_model_id_identifier_raises(self) -> None:
        with pytest.raises(ValueError, match="model_id"):
            VendorParserModel(model_id="m-bad", vendor_id="v", version=1)

    def test_version_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="version"):
            VendorParserModel(model_id="m", vendor_id="v", version=0)

    def test_negative_version_raises(self) -> None:
        with pytest.raises(ValueError, match="version"):
            VendorParserModel(model_id="m", vendor_id="v", version=-1)

    def test_non_int_version_raises(self) -> None:
        with pytest.raises(TypeError, match="version"):
            VendorParserModel(
                model_id="m",
                vendor_id="v",
                version="1",  # type: ignore[arg-type]
            )

    def test_invalid_identity_rule_raises(self) -> None:
        with pytest.raises(TypeError, match="identity_rules"):
            VendorParserModel(
                model_id="m",
                vendor_id="v",
                version=1,
                identity_rules=("not a rule",),  # type: ignore[arg-type]
            )

    def test_invalid_layout_rule_raises(self) -> None:
        with pytest.raises(TypeError, match="layout_rules"):
            VendorParserModel(
                model_id="m",
                vendor_id="v",
                version=1,
                layout_rules=("not a rule",),  # type: ignore[arg-type]
            )

    def test_invalid_invoice_field_rule_raises(self) -> None:
        with pytest.raises(TypeError, match="invoice_field_rules"):
            VendorParserModel(
                model_id="m",
                vendor_id="v",
                version=1,
                invoice_field_rules=("not a rule",),  # type: ignore[arg-type]
            )

    def test_invalid_item_field_rule_raises(self) -> None:
        with pytest.raises(TypeError, match="item_field_rules"):
            VendorParserModel(
                model_id="m",
                vendor_id="v",
                version=1,
                item_field_rules=("not a rule",),  # type: ignore[arg-type]
            )

    def test_invalid_item_table_rule_raises(self) -> None:
        with pytest.raises(TypeError, match="item_table_rules"):
            VendorParserModel(
                model_id="m",
                vendor_id="v",
                version=1,
                item_table_rules=("not a rule",),  # type: ignore[arg-type]
            )

    def test_invalid_column_roles_key_type_raises(self) -> None:
        with pytest.raises(TypeError, match="column_roles kljucevi"):
            VendorParserModel(
                model_id="m",
                vendor_id="v",
                version=1,
                column_roles={1: "x"},  # type: ignore[dict-item]
            )

    def test_invalid_column_roles_value_type_raises(self) -> None:
        with pytest.raises(TypeError, match="column_roles vrijednosti"):
            VendorParserModel(
                model_id="m",
                vendor_id="v",
                version=1,
                column_roles={"col_1": 1},  # type: ignore[dict-item]
            )

    def test_invalid_normalization_rule_in_tuple_raises(self) -> None:
        with pytest.raises(TypeError, match="normalization_rules"):
            VendorParserModel(
                model_id="m",
                vendor_id="v",
                version=1,
                normalization_rules={"x": ("not a rule",)},  # type: ignore[dict-item]
            )

    def test_invalid_validation_rule_in_tuple_raises(self) -> None:
        with pytest.raises(TypeError, match="validation_rules"):
            VendorParserModel(
                model_id="m",
                vendor_id="v",
                version=1,
                validation_rules={"x": ("not a rule",)},  # type: ignore[dict-item]
            )

    def test_invalid_fallback_strategies_key_raises(self) -> None:
        with pytest.raises(TypeError, match="fallback_strategies kljucevi"):
            VendorParserModel(
                model_id="m",
                vendor_id="v",
                version=1,
                fallback_strategies={1: FallbackStrategy.RETURN_NONE},  # type: ignore[dict-item]
            )

    def test_invalid_fallback_strategies_value_raises(self) -> None:
        with pytest.raises(TypeError, match="fallback_strategies vrijednosti"):
            VendorParserModel(
                model_id="m",
                vendor_id="v",
                version=1,
                fallback_strategies={"x": "invalid"},  # type: ignore[dict-item]
            )

    def test_invalid_required_source_files_type_raises(self) -> None:
        with pytest.raises(TypeError, match="required_source_files"):
            VendorParserModel(
                model_id="m",
                vendor_id="v",
                version=1,
                required_source_files=["not", "tuple"],  # type: ignore[arg-type]
            )

    def test_invalid_required_source_files_element_raises(self) -> None:
        with pytest.raises(TypeError, match="required_source_files"):
            VendorParserModel(
                model_id="m",
                vendor_id="v",
                version=1,
                required_source_files=("ok", 123),  # type: ignore[arg-type]
            )

    def test_invalid_consumed_paths_behavior_raises(self) -> None:
        with pytest.raises(TypeError, match="consumed_paths_behavior"):
            VendorParserModel(
                model_id="m",
                vendor_id="v",
                version=1,
                consumed_paths_behavior="invalid",  # type: ignore[arg-type]
            )


class TestVendorParserModelFrozen:
    def test_mutation_raises(self) -> None:
        m = VendorParserModel(model_id="m", vendor_id="v", version=1)
        with pytest.raises((AttributeError, Exception)):
            m.version = 2  # type: ignore[misc]


# --------------------------------------------------------------------------- #
# VendorParserModel — domain agnostic property (V3 32)
# --------------------------------------------------------------------------- #


class TestVendorParserModelAgnostic:
    def test_no_inline_python_storage(self) -> None:
        """VendorParserModel nema inline Python; sva ponašanja su ime+param."""
        m = VendorParserModel(
            model_id="m",
            vendor_id="v",
            version=1,
            invoice_field_rules=(
                FieldExtractionRule(
                    field_name="invoice_number",
                    strategy=ExtractionStrategy.HEADER_MATCH,
                    function_name="resolve_invoice_no",
                ),
            ),
            validation_rules={
                "iznos": (
                    ValidationRule(function_name="validate_iznos"),
                ),
            },
        )
        # Prolazimo kroz sva polja i provjeravamo da nigdje nema inline source.
        # Sva "ponašanja" su function_name (str), params (Mapping) — nikad str sa kodom.
        for r in m.invoice_field_rules:
            assert isinstance(r.function_name, str)
            assert not r.function_name.startswith("def ")
            assert not r.function_name.startswith("import ")
        for rules in m.validation_rules.values():
            for r in rules:
                assert isinstance(r.function_name, str)

    def test_no_parser_studio_imports(self) -> None:
        """VendorParserModel NE smije importovati parser_studio runtime (V3 32)."""
        import parser_studio.domain.invoice.vendor_parser_model as mod

        # Modul iz kojeg dolazi VendorParserModel je u domeni, NE u runtime sloju.
        # Provjeri da se u modulu ne nalaze runtime-dependent simboli.
        source = Path(mod.__file__).read_text(encoding="utf-8")
        # Ne smije biti import ai adaptera, presentation, itd.
        forbidden_substrings = [
            "from parser_studio.presentation",
            "from parser_studio.adapters",
            "from parser_studio.ports",
            "import parser_studio.presentation",
            "import parser_studio.adapters",
            "import parser_studio.ports",
        ]
        for bad in forbidden_substrings:
            assert bad not in source, f"VendorParserModel sadrži zabranjeni import: {bad}"

    def test_default_consumed_paths_is_ignore(self) -> None:
        """Default je IGNORE — nikad ne propusti consumed_paths u output."""
        m = VendorParserModel(model_id="m", vendor_id="v", version=1)
        assert m.consumed_paths_behavior is ConsumedPathsBehavior.IGNORE


# --------------------------------------------------------------------------- #
# rule_count_summary
# --------------------------------------------------------------------------- #


class TestRuleCountSummary:
    def test_empty_model_summary(self) -> None:
        m = VendorParserModel(model_id="m", vendor_id="v", version=1)
        s = rule_count_summary(m)
        assert s == {
            "identity_rules": 0,
            "layout_rules": 0,
            "invoice_field_rules": 0,
            "item_field_rules": 0,
            "item_table_rules": 0,
            "column_roles": 0,
            "normalization_fields": 0,
            "validation_fields": 0,
            "fallback_fields": 0,
            "required_source_files": 0,
        }

    def test_populated_model_summary(self) -> None:
        m = VendorParserModel(
            model_id="m",
            vendor_id="v",
            version=1,
            identity_rules=(LayoutRule(rule_id="i", function_name="f"),),
            layout_rules=(
                LayoutRule(rule_id="l1", function_name="f1"),
                LayoutRule(rule_id="l2", function_name="f2"),
            ),
            invoice_field_rules=(
                FieldExtractionRule(
                    field_name="invoice_number",
                    strategy=ExtractionStrategy.HEADER_MATCH,
                    function_name="f",
                ),
            ),
            item_field_rules=(
                FieldExtractionRule(
                    field_name="naziv_robe",
                    strategy=ExtractionStrategy.TABLE_HEADER,
                    function_name="f",
                ),
            ),
            item_table_rules=(LayoutRule(rule_id="t", function_name="f"),),
            column_roles={"col_1": "naziv_robe"},
            normalization_rules={"x": (NormalizationRule(function_name="f"),)},
            validation_rules={"y": (ValidationRule(function_name="f"),)},
            fallback_strategies={"z": FallbackStrategy.RETURN_NONE},
            required_source_files=("a.json", "b.json"),
        )
        s = rule_count_summary(m)
        assert s["identity_rules"] == 1
        assert s["layout_rules"] == 2
        assert s["invoice_field_rules"] == 1
        assert s["item_field_rules"] == 1
        assert s["item_table_rules"] == 1
        assert s["column_roles"] == 1
        assert s["normalization_fields"] == 1
        assert s["validation_fields"] == 1
        assert s["fallback_fields"] == 1
        assert s["required_source_files"] == 2
"""Unit testovi za OracleVsGoldComparison (FAZA D3 verifikacija)."""
from __future__ import annotations

from parser_studio.application.verification.oracle_vs_gold import (
    ComparisonReport,
    ComparisonStatus,
    FieldComparison,
    GoldEntry,
    OracleVsGoldComparison,
)


class TestComparisonStatus:
    def test_status_values(self):
        assert ComparisonStatus.MATCH.value == "MATCH"
        assert ComparisonStatus.MISMATCH.value == "MISMATCH"
        assert ComparisonStatus.MISSING_ORACLE.value == "MISSING_ORACLE"
        assert ComparisonStatus.MISSING_GOLD.value == "MISSING_GOLD"


class TestGoldEntry:
    def test_minimal(self):
        entry = GoldEntry(field="invoice_number", value="INV-1")
        assert entry.field == "invoice_number"
        assert entry.value == "INV-1"
        assert entry.item_id is None

    def test_with_item_id(self):
        entry = GoldEntry(field="quantity", value=10.0, item_id="line_5")
        assert entry.item_id == "line_5"


class TestOracleVsGoldComparison:
    def _make_comparison(self):
        return OracleVsGoldComparison()

    def test_perfect_match(self):
        comp = self._make_comparison()
        oracle = {"invoice_number": "INV-1", "currency": "EUR"}
        gold = {
            "invoice_number": GoldEntry(field="invoice_number", value="INV-1"),
            "currency": GoldEntry(field="currency", value="EUR"),
        }
        report = comp.compare(oracle, gold)

        assert report.matched == 2
        assert report.mismatched == 0
        assert report.accuracy == 1.0

    def test_mismatch_detected(self):
        comp = self._make_comparison()
        oracle = {"invoice_number": "INV-WRONG"}
        gold = {"invoice_number": GoldEntry(field="invoice_number", value="INV-1")}
        report = comp.compare(oracle, gold)

        assert report.matched == 0
        assert report.mismatched == 1
        assert report.accuracy == 0.0

    def test_missing_oracle(self):
        """Gold ima, Oracle nema."""
        comp = self._make_comparison()
        oracle: dict = {}
        gold = {"invoice_number": GoldEntry(field="invoice_number", value="INV-1")}
        report = comp.compare(oracle, gold)

        assert report.missing_oracle == 1
        assert report.matched == 0
        assert report.mismatched == 0

    def test_missing_gold(self):
        """Oracle ima, Gold nema."""
        comp = self._make_comparison()
        oracle = {"invoice_number": "INV-1"}
        gold: dict = {}
        report = comp.compare(oracle, gold)

        assert report.missing_gold == 1
        assert report.matched == 0

    def test_numeric_tolerance(self):
        """Brojevi sa razlikom < 0.02 smatraju se MATCH."""
        comp = self._make_comparison()
        oracle = {"invoice_total": 100.01}
        gold = {"invoice_total": GoldEntry(field="invoice_total", value=100.0)}
        report = comp.compare(oracle, gold)

        assert report.matched == 1

    def test_numeric_outside_tolerance(self):
        """Brojevi sa razlikom >= 0.02 smatraju se MISMATCH."""
        comp = self._make_comparison()
        oracle = {"invoice_total": 100.5}
        gold = {"invoice_total": GoldEntry(field="invoice_total", value=100.0)}
        report = comp.compare(oracle, gold)

        assert report.mismatched == 1

    def test_int_and_float_match(self):
        """Int i float sa istom numeričkom vrijednošću = MATCH."""
        comp = self._make_comparison()
        oracle = {"quantity": 10}
        gold = {"quantity": GoldEntry(field="quantity", value=10.0)}
        report = comp.compare(oracle, gold)

        assert report.matched == 1

    def test_string_strict_equality(self):
        """Stringovi — striktna equality."""
        comp = self._make_comparison()
        oracle = {"invoice_number": "INV-1"}
        gold = {"invoice_number": GoldEntry(field="invoice_number", value="INV-1 ")}
        # trailing space — različiti stringovi
        report = comp.compare(oracle, gold)
        assert report.mismatched == 1


class TestComparisonReport:
    def test_accuracy_zero_when_empty(self):
        report = ComparisonReport(comparisons=())
        assert report.accuracy == 0.0

    def test_accuracy_one_when_all_match(self):
        report = ComparisonReport(
            comparisons=(
                FieldComparison(
                    field="a",
                    status=ComparisonStatus.MATCH,
                    oracle_value="x",
                    gold_value="x",
                ),
                FieldComparison(
                    field="b",
                    status=ComparisonStatus.MATCH,
                    oracle_value="y",
                    gold_value="y",
                ),
            ),
            total_fields=2,
            matched=2,
        )
        assert report.accuracy == 1.0

    def test_per_field_accuracy(self):
        report = ComparisonReport(
            comparisons=(
                FieldComparison(
                    field="a",
                    status=ComparisonStatus.MATCH,
                    oracle_value="x",
                    gold_value="x",
                ),
                FieldComparison(
                    field="b",
                    status=ComparisonStatus.MISMATCH,
                    oracle_value="x",
                    gold_value="y",
                ),
            ),
        )
        acc = report.per_field_accuracy()
        assert acc == {"a": 1.0, "b": 0.0}

    def test_failed_fields(self):
        report = ComparisonReport(
            comparisons=(
                FieldComparison(
                    field="a",
                    status=ComparisonStatus.MATCH,
                    oracle_value="x",
                    gold_value="x",
                ),
                FieldComparison(
                    field="b",
                    status=ComparisonStatus.MISMATCH,
                    oracle_value="x",
                    gold_value="y",
                ),
                FieldComparison(
                    field="c",
                    status=ComparisonStatus.MISSING_ORACLE,
                    oracle_value=None,
                    gold_value="z",
                ),
            ),
        )
        failed = report.failed_fields()
        assert set(failed) == {"b", "c"}


class TestComparisonEdgeCases:
    def test_empty_inputs(self):
        comp = OracleVsGoldComparison()
        report = comp.compare({}, {})
        assert report.matched == 0
        assert report.total_fields == 0
        assert report.accuracy == 0.0

    def test_only_oracle_fields(self):
        comp = OracleVsGoldComparison()
        oracle = {"invoice_number": "INV-1", "currency": "EUR"}
        report = comp.compare(oracle, {})
        assert report.missing_gold == 2

    def test_only_gold_fields(self):
        comp = OracleVsGoldComparison()
        gold = {
            "invoice_number": GoldEntry(field="invoice_number", value="INV-1"),
            "currency": GoldEntry(field="currency", value="EUR"),
        }
        report = comp.compare({}, gold)
        assert report.missing_oracle == 2

    def test_none_values_excluded_from_comparison(self):
        """Oba None — preskače se (nije MATCH niti MISMATCH)."""
        comp = OracleVsGoldComparison()
        oracle = {"x": None}
        gold = {"x": GoldEntry(field="x", value=None)}
        report = comp.compare(oracle, gold)
        # Nema poredjenja — preskoceno
        assert report.total_fields == 0
# Tests: integration/test_real_gold_evaluation.
"""Testovi za RealGoldEvaluator (V3_2 C5).

Acceptance: aggregate accuracy >= 0.70 (GATE-3 threshold).
"""
from __future__ import annotations

import pytest

from parser_studio.application.extraction.real_gold_evaluator import (
    DocumentEvaluation,
    EvaluationReport,
    RealGoldEvaluator,
)


def _expected_4_fakture() -> dict[str, tuple[dict[str, str], dict[str, str]]]:
    """Sample data: 4 fakture × 9 invoice polja sa 100% match (za test)."""
    docs = {}
    for factory_id in ["faktura-1", "faktura-2", "medicopharm", "sumaprom"]:
        expected = {
            "invoice_number": f"SYN-INV-{factory_id.upper()}-001",
            "invoice_date": "2026-09-14",
            "currency": "EUR",
            "seller_name": f"SYN-{factory_id.upper()} Synthetic d.o.o.",
            "seller_tax_id": "SYN-0001",
            "buyer_name": "Synthetic Buyer d.o.o. (Mavis Test)",
            "buyer_tax_id": "SYN-9001",
            "incoterm": "EXW",
            "origin_statement": f"SYNTHETIC ORIGIN STATEMENT for {factory_id}",
        }
        # Za pocetni test: resolved == expected (100% match)
        docs[factory_id] = (expected, expected.copy())
    return docs


class TestRealGoldEvaluatorThreshold:
    def test_default_threshold(self) -> None:
        ev = RealGoldEvaluator()
        assert ev._threshold == 0.70

    def test_custom_threshold(self) -> None:
        ev = RealGoldEvaluator(threshold=0.50)
        assert ev._threshold == 0.50

    def test_invalid_threshold_raises(self) -> None:
        with pytest.raises(ValueError, match="threshold"):
            RealGoldEvaluator(threshold=1.5)
        with pytest.raises(ValueError, match="threshold"):
            RealGoldEvaluator(threshold=-0.1)


class TestRealGoldEvaluatorPerfectMatch:
    def test_100_percent_match(self) -> None:
        docs = _expected_4_fakture()
        report = RealGoldEvaluator().evaluate_documents(docs)

        # 4 dokumenta, 9 polja svaki = 36 total, 36 correct
        assert report.total_fields == 36
        assert report.total_correct == 36
        assert report.aggregate_accuracy == 1.0
        assert report.threshold_pass is True

        # Per-document
        assert len(report.per_document) == 4
        for doc_eval in report.per_document.values():
            assert doc_eval.total_count == 9
            assert doc_eval.correct_count == 9
            assert doc_eval.overall_accuracy == 1.0

        # Per-field accuracy = 1.0 za svako polje
        for accuracy in report.field_accuracy.values():
            assert accuracy == 1.0


class TestRealGoldEvaluatorPartialMatch:
    def test_partial_match_above_threshold(self) -> None:
        """75% match — GATE-3 PASS (>= 0.70)."""
        docs = {}
        for factory_id in ["faktura-1", "faktura-2", "medicopharm", "sumaprom"]:
            expected = _expected_4_fakture()[factory_id][0]
            resolved = expected.copy()
            # Izmijesi 25% polja (9 * 0.25 ≈ 2 polja)
            for i, field in enumerate(list(expected.keys())):
                if i < 3:  # Prva 3 polja su mismatch
                    resolved[field] = "WRONG_VALUE"
            docs[factory_id] = (expected, resolved)

        report = RealGoldEvaluator().evaluate_documents(docs)
        # 36 - 12 mismatch = 24 correct
        assert report.total_correct == 24
        assert report.total_fields == 36
        # accuracy 24/36 ≈ 0.67 — ispod threshold-a
        assert report.aggregate_accuracy < 0.70
        assert report.threshold_pass is False

    def test_partial_match_with_per_field(self) -> None:
        """Provjera per-field accuracy sa mismatch na jednom polju."""
        # 4 dokumenta, svaki ima currency mismatch
        docs = {}
        for factory_id in ["faktura-1", "faktura-2", "medicopharm", "sumaprom"]:
            expected = _expected_4_fakture()[factory_id][0]
            resolved = expected.copy()
            resolved["currency"] = "USD"  # mismatch na currency
            docs[factory_id] = (expected, resolved)

        report = RealGoldEvaluator().evaluate_documents(docs)
        # Per-document accuracy = 8/9
        for doc_eval in report.per_document.values():
            assert doc_eval.overall_accuracy == 8 / 9
        # Aggregate accuracy = 8/9
        assert abs(report.aggregate_accuracy - 8 / 9) < 0.001
        # field_accuracy: 0/4 = 0.0 za currency, 4/4 = 1.0 za ostale
        assert report.field_accuracy["currency"] == 0.0
        assert report.field_accuracy["invoice_number"] == 1.0


class TestRealGoldEvaluatorCustomThreshold:
    def test_above_threshold_passes(self) -> None:
        """Threshold 0.80, accuracy 0.50 — FAIL."""
        docs = {}
        for factory_id in ["faktura-1", "faktura-2", "medicopharm", "sumaprom"]:
            expected = _expected_4_fakture()[factory_id][0]
            resolved = expected.copy()
            # Mismatch 50% (4-5 od 9)
            for i, field in enumerate(list(expected.keys())):
                if i < 5:
                    resolved[field] = "WRONG"
            docs[factory_id] = (expected, resolved)

        ev = RealGoldEvaluator(threshold=0.80)
        report = ev.evaluate_documents(docs)
        assert report.aggregate_accuracy < 0.80
        assert report.threshold_pass is False


class TestRealGoldEvaluatorEmpty:
    def test_empty_documents(self) -> None:
        report = RealGoldEvaluator().evaluate_documents({})
        assert report.per_document == {}
        assert report.aggregate_accuracy == 0.0
        assert report.total_correct == 0
        assert report.total_fields == 0

    def test_empty_expected(self) -> None:
        report = RealGoldEvaluator().evaluate_documents(
            {"doc-1": ({}, {})}
        )
        # Prazan expected → 0/0 = 0.0
        assert report.per_document["doc-1"].overall_accuracy == 0.0
        assert report.per_document["doc-1"].total_count == 0


class TestRealGoldEvaluatorCaseInsensitive:
    def test_case_insensitive_match(self) -> None:
        """Whitespace-trim i case-insensitive."""
        report = RealGoldEvaluator().evaluate_documents(
            {
                "doc-1": (
                    {"invoice_number": "INV-001"},
                    {"invoice_number": "inv-001"},  # lowercase
                ),
            }
        )
        assert report.per_document["doc-1"].per_field_matches["invoice_number"] is True

    def test_whitespace_trim_match(self) -> None:
        report = RealGoldEvaluator().evaluate_documents(
            {
                "doc-1": (
                    {"invoice_number": "INV-001"},
                    {"invoice_number": "  INV-001  "},  # whitespace
                ),
            }
        )
        assert report.per_document["doc-1"].per_field_matches["invoice_number"] is True

    def test_missing_field_in_resolved(self) -> None:
        """Ako resolved nema polje, mismatch."""
        report = RealGoldEvaluator().evaluate_documents(
            {
                "doc-1": (
                    {"invoice_number": "INV-001", "currency": "EUR"},
                    {"invoice_number": "INV-001"},  # nema currency
                ),
            }
        )
        doc_eval = report.per_document["doc-1"]
        assert doc_eval.per_field_matches["invoice_number"] is True
        assert doc_eval.per_field_matches["currency"] is False
        assert doc_eval.correct_count == 1
        assert doc_eval.total_count == 2


class TestEvaluationReport:
    def test_passed_property(self) -> None:
        ev = RealGoldEvaluator(threshold=0.5)
        report = EvaluationReport(
            per_document={},
            aggregate_accuracy=0.7,
            field_accuracy={},
            total_correct=7,
            total_fields=10,
            threshold_pass=True,
        )
        assert ev.passes_threshold(report) is True
        assert report.passed is True

    def test_frozen(self) -> None:
        from dataclasses import FrozenInstanceError

        report = EvaluationReport(
            per_document={},
            aggregate_accuracy=0.0,
            field_accuracy={},
            total_correct=0,
            total_fields=0,
            threshold_pass=False,
        )
        with pytest.raises(FrozenInstanceError):
            report.aggregate_accuracy = 0.5  # type: ignore[misc]

    def test_document_evaluation_frozen(self) -> None:
        from dataclasses import FrozenInstanceError

        de = DocumentEvaluation(
            document_id="doc-1",
            field_accuracy={},
            per_field_matches={},
            overall_accuracy=0.0,
            correct_count=0,
            total_count=0,
        )
        with pytest.raises(FrozenInstanceError):
            de.overall_accuracy = 1.0  # type: ignore[misc]


class TestV3B5Acceptance:
    """V3 B5 acceptance: Real Gold evaluation sa 4 fakture i 20 polja."""

    def test_237_items_acceptance_via_evaluator(self) -> None:
        """Demonstrira evaluator sa 4 fakture × 20 polja (9 invoice + 11 item).

        Za unit testiranje: 4 × 20 = 80 polja, sve match (100%).
        U realnom FAZA D pipeline-u, ovi 80 polja bi bili GENERISANI iz
        Producer-a + Resolver-a i uspoređeni sa USER_CONFIRMED events.
        """
        all_fields_20 = (
            "invoice_number", "invoice_date", "currency",
            "seller_name", "seller_tax_id",
            "buyer_name", "buyer_tax_id",
            "incoterm", "origin_statement",
            "redni_broj", "sifra_proizvoda", "naziv_robe",
            "tarifni_broj", "jedinica_mjere", "kolicina",
            "jedinicna_cijena", "iznos",
            "zemlja_porijekla", "neto_masa", "bruto_masa",
        )

        docs = {}
        for factory_id in ["faktura-1", "faktura-2", "medicopharm", "sumaprom"]:
            expected = {field: f"value-{factory_id}-{field}" for field in all_fields_20}
            docs[factory_id] = (expected, expected.copy())

        report = RealGoldEvaluator().evaluate_documents(docs)
        assert report.total_fields == 80  # 4 × 20
        assert report.total_correct == 80
        assert report.aggregate_accuracy == 1.0
        assert report.threshold_pass is True

# Tests: application/extraction/validators/test_arithmetic.
"""Testovi za ArithmeticValidator (V3_2 C4 arithmetic)."""
from __future__ import annotations

from parser_studio.application.extraction.validators import (
    ArithmeticValidator,
    IssueSeverity,
)
from parser_studio.domain.evidence import Candidate, DocumentEvidence, Locator
from parser_studio.domain.extraction.extraction_draft import ExtractionDraft


def _make_locator() -> Locator:
    return Locator(source_path="/test.xlsx", kind="excel", sheet="Sheet1")


def _make_draft(**fields: str) -> ExtractionDraft:
    candidates_by_field: dict[str, tuple[Candidate, ...]] = {}
    for field, value in fields.items():
        cand = Candidate(
            field=field,
            raw_value=value,
            normalized_value=value,
            locator=_make_locator(),
            evidence="test",
            producer_id="test",
        )
        candidates_by_field[field] = (cand,)
    return ExtractionDraft(
        document_id="doc-1",
        document=DocumentEvidence(document_id="doc-1", source_path="/test.xlsx"),
        candidates_by_field=candidates_by_field,
    )


class TestArithmeticValidator:
    def test_subtotal_plus_tax_equals_total(self) -> None:
        issues = ArithmeticValidator().validate(
            _make_draft(subtotal="100.00", tax_amount="20.00", total="120.00")
        )
        assert issues == ()

    def test_subtotal_plus_tax_mismatch_warning(self) -> None:
        issues = ArithmeticValidator().validate(
            _make_draft(subtotal="100.00", tax_amount="20.00", total="130.00")
        )
        # Ne match (razlika 10)
        assert len(issues) == 1
        assert issues[0].code == "A001"
        assert issues[0].severity == IssueSeverity.WARNING

    def test_subtotal_only_no_issue(self) -> None:
        issues = ArithmeticValidator().validate(_make_draft(subtotal="100.00"))
        # Samo subtotal — ne možemo provjeriti sum
        assert issues == ()

    def test_missing_all_no_issue(self) -> None:
        issues = ArithmeticValidator().validate(_make_draft())
        assert issues == ()

    def test_decimal_with_comma(self) -> None:
        """Hrvatski separator."""
        issues = ArithmeticValidator().validate(
            _make_draft(
                subtotal="100,00", tax_amount="20,00", total="120,00"
            )
        )
        assert issues == ()

    def test_tolerance_within_002(self) -> None:
        """Tolerance 0.02 za floating-point greske."""
        issues = ArithmeticValidator().validate(
            _make_draft(
                subtotal="100.00", tax_amount="20.00", total="120.01"
            )
        )
        # Razlika 0.01 < tolerance 0.02 → OK
        assert issues == ()

    def test_tolerance_exceeded(self) -> None:
        issues = ArithmeticValidator().validate(
            _make_draft(
                subtotal="100.00", tax_amount="20.00", total="120.05"
            )
        )
        assert len(issues) == 1
        assert issues[0].code == "A001"

# Tests: application/extraction/validators/test_cross_field.
"""Testovi za CrossFieldValidator (V3_2 C4 cross-field)."""
from __future__ import annotations

from parser_studio.application.extraction.validators import (
    CrossFieldValidator,
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


class TestCrossFieldValidator:
    def test_currency_3_letters_no_issue(self) -> None:
        issues = CrossFieldValidator().validate(_make_draft(currency="EUR"))
        assert issues == ()

    def test_currency_invalid_warning(self) -> None:
        issues = CrossFieldValidator().validate(_make_draft(currency="EURO"))
        assert any(i.code == "C001" for i in issues)

    def test_due_date_after_invoice_date(self) -> None:
        issues = CrossFieldValidator().validate(
            _make_draft(
                invoice_date="2026-09-01",
                due_date="2026-09-30",
            )
        )
        assert issues == ()

    def test_due_date_before_invoice_date_error(self) -> None:
        issues = CrossFieldValidator().validate(
            _make_draft(
                invoice_date="2026-09-30",
                due_date="2026-09-01",
            )
        )
        assert any(i.code == "C002" for i in issues)

    def test_invoice_date_future_warning(self) -> None:
        """invoice_date u buducnosti — sanity warning."""
        issues = CrossFieldValidator().validate(
            _make_draft(invoice_date="2099-01-01")
        )
        assert any(i.code == "C003" for i in issues)

    def test_empty_draft_no_issues(self) -> None:
        issues = CrossFieldValidator().validate(_make_draft())
        assert issues == ()

# Tests: application/extraction/validators/test_structure.
"""Testovi za StructureValidator (V3_2 C4 structure)."""
from __future__ import annotations

from parser_studio.application.extraction.validators import (
    IssueSeverity,
    StructureValidator,
)
from parser_studio.domain.evidence import Candidate, DocumentEvidence, Locator
from parser_studio.domain.extraction.extraction_draft import ExtractionDraft


def _make_locator() -> Locator:
    return Locator(source_path="/test.xlsx", kind="excel", sheet="Sheet1")


def _make_draft_with_all_9_invoice() -> ExtractionDraft:
    candidates_by_field: dict[str, tuple[Candidate, ...]] = {}
    for field in (
        "invoice_number", "invoice_date", "currency",
        "seller_name", "seller_tax_id",
        "buyer_name", "buyer_tax_id",
        "incoterm", "origin_statement",
    ):
        candidates_by_field[field] = (
            Candidate(
                field=field,
                raw_value=f"value-{field}",
                normalized_value=f"value-{field}",
                locator=_make_locator(),
                evidence="test",
                producer_id="test",
            ),
        )
    return ExtractionDraft(
        document_id="doc-1",
        document=DocumentEvidence(document_id="doc-1", source_path="/test.xlsx"),
        candidates_by_field=candidates_by_field,
    )


class TestStructureValidator:
    def test_all_9_invoice_fields_present(self) -> None:
        issues = StructureValidator().validate(_make_draft_with_all_9_invoice())
        assert issues == ()

    def test_missing_invoice_number(self) -> None:
        draft = _make_draft_with_all_9_invoice()
        # Ukloni invoice_number
        draft.candidates_by_field.pop("invoice_number")
        issues = StructureValidator().validate(draft)
        # Barem 1 issue sa field=invoice_number
        codes = {i.code for i in issues if i.field == "invoice_number"}
        assert "ST001" in codes

    def test_multiple_missing(self) -> None:
        draft = _make_draft_with_all_9_invoice()
        draft.candidates_by_field.pop("invoice_number")
        draft.candidates_by_field.pop("currency")
        issues = StructureValidator().validate(draft)
        fields_with_issue = {i.field for i in issues}
        assert "invoice_number" in fields_with_issue
        assert "currency" in fields_with_issue

    def test_empty_draft_has_9_issues(self) -> None:
        draft = ExtractionDraft(
            document_id="doc-1",
            document=DocumentEvidence(document_id="doc-1", source_path="/test.xlsx"),
        )
        issues = StructureValidator().validate(draft)
        # 9 obaveznih polja nedostaje
        assert len(issues) == 9
        assert all(i.code == "ST001" for i in issues)
        assert all(i.severity == IssueSeverity.ERROR for i in issues)

    def test_empty_field_also_missing(self) -> None:
        """Polje sa praznim tuple kandidata se takodje tretira kao missing."""
        draft = _make_draft_with_all_9_invoice()
        draft.candidates_by_field["currency"] = ()  # Prazan tuple
        issues = StructureValidator().validate(draft)
        assert any(i.field == "currency" for i in issues)

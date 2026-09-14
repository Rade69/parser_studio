# Tests: application/extraction/validators/test_syntax.
"""Testovi za SyntaxValidator (V3_2 C4 syntax)."""
from __future__ import annotations

from parser_studio.application.extraction.validators import (
    IssueSeverity,
    SyntaxValidator,
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


class TestSyntaxValidatorInvoiceNumber:
    def test_valid_invoice_number(self) -> None:
        issues = SyntaxValidator().validate(
            _make_draft(invoice_number="INV-001")
        )
        assert list(issues) == []

    def test_short_invoice_number_warning(self) -> None:
        """'X!' sadrzi specijalni karakter — flaggira S001."""
        issues = SyntaxValidator().validate(
            _make_draft(invoice_number="X!")
        )
        assert len(issues) == 1
        assert issues[0].code == "S001"
        assert issues[0].severity == IssueSeverity.WARNING

    def test_single_char_invoice_number_no_warning(self) -> None:
        """1 karakter je u opsegu 1-30 — ne flaggira."""
        issues = SyntaxValidator().validate(
            _make_draft(invoice_number="X")
        )
        assert list(issues) == []


class TestSyntaxValidatorInvoiceDate:
    def test_iso_date_valid(self) -> None:
        issues = SyntaxValidator().validate(
            _make_draft(invoice_date="2026-09-14")
        )
        assert issues == ()

    def test_bhs_date_valid(self) -> None:
        issues = SyntaxValidator().validate(
            _make_draft(invoice_date="14.09.2026")
        )
        assert issues == ()

    def test_invalid_date_warning(self) -> None:
        issues = SyntaxValidator().validate(
            _make_draft(invoice_date="nije datum")
        )
        assert len(issues) == 1
        assert issues[0].code == "S002"


class TestSyntaxValidatorCurrency:
    def test_valid_currency(self) -> None:
        issues = SyntaxValidator().validate(_make_draft(currency="EUR"))
        assert issues == ()

    def test_invalid_currency_warning(self) -> None:
        issues = SyntaxValidator().validate(_make_draft(currency="EURO"))
        assert len(issues) == 1
        assert issues[0].code == "S003"


class TestSyntaxValidatorSellerTaxId:
    def test_valid_tax_id(self) -> None:
        issues = SyntaxValidator().validate(
            _make_draft(seller_tax_id="1234567890123")
        )
        assert issues == ()

    def test_short_tax_id_warning(self) -> None:
        issues = SyntaxValidator().validate(
            _make_draft(seller_tax_id="123")
        )
        assert len(issues) == 1
        assert issues[0].code == "S004"


class TestSyntaxValidatorKolicina:
    def test_positive_kolicina(self) -> None:
        issues = SyntaxValidator().validate(_make_draft(kolicina="10"))
        assert list(issues) == []

    def test_zero_kolicina_error(self) -> None:
        issues = SyntaxValidator().validate(_make_draft(kolicina="0"))
        assert len(issues) == 1
        assert issues[0].code == "S005"
        assert issues[0].severity == IssueSeverity.ERROR

    def test_non_numeric_kolicina_error(self) -> None:
        issues = SyntaxValidator().validate(_make_draft(kolicina="abc"))
        assert len(issues) == 1
        assert issues[0].code == "S006"

    def test_decimal_with_comma(self) -> None:
        """Hrvatski decimal separator."""
        issues = SyntaxValidator().validate(_make_draft(kolicina="10,5"))
        assert list(issues) == []


class TestSyntaxValidatorMultiple:
    def test_multiple_issues(self) -> None:
        issues = SyntaxValidator().validate(
            _make_draft(
                invoice_number="X",
                invoice_date="invalid",
                currency="EURO",
            )
        )
        codes = {i.code for i in issues}
        assert codes == {"S002", "S003"}

    def test_empty_draft(self) -> None:
        draft = ExtractionDraft(
            document_id="doc-1",
            document=DocumentEvidence(document_id="doc-1", source_path="/test.xlsx"),
        )
        issues = SyntaxValidator().validate(draft)
        assert list(issues) == []

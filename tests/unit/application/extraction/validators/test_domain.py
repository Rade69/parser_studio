# Tests: application/extraction/validators/test_domain.
"""Testovi za DomainValidator (V3_2 C4 domain)."""
from __future__ import annotations

from parser_studio.application.extraction.validators import (
    DomainValidator,
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


class TestDomainValidator:
    def test_valid_combo_no_issues(self) -> None:
        issues = DomainValidator().validate(
            _make_draft(
                seller_name="Pekabesko AD",
                buyer_name="Leburic Komerc",
                seller_tax_id="1234567890123",
                incoterm="EXW",
                origin_statement="Origin: BiH",
            )
        )
        assert issues == ()

    def test_seller_equals_buyer_warning(self) -> None:
        issues = DomainValidator().validate(
            _make_draft(
                seller_name="Isti Naziv",
                buyer_name="isti naziv",
            )
        )
        assert any(i.code == "D001" for i in issues)

    def test_invalid_tax_id(self) -> None:
        issues = DomainValidator().validate(
            _make_draft(seller_tax_id="abc123")
        )
        assert any(i.code == "D002" for i in issues)

    def test_valid_incoterm(self) -> None:
        issues = DomainValidator().validate(
            _make_draft(incoterm="EXW", origin_statement="Origin: BiH")
        )
        assert list(issues) == []

    def test_invalid_incoterm(self) -> None:
        issues = DomainValidator().validate(
            _make_draft(incoterm="NOTREAL", origin_statement="Origin: BiH")
        )
        assert any(i.code == "D003" for i in issues)

    def test_empty_origin_error(self) -> None:
        issues = DomainValidator().validate(
            _make_draft(origin_statement="")
        )
        assert any(i.code == "D004" and i.severity == IssueSeverity.ERROR for i in issues)

    def test_empty_draft_no_issues(self) -> None:
        """Prazan draft — nema seller_name/buyer_name za usporedbu (D001), origin prazan flaggira D004."""
        issues = DomainValidator().validate(_make_draft())
        # Samo D004 (origin_statement prazan)
        codes = {i.code for i in issues}
        assert codes == {"D004"}

# Tests: application/extraction/producers/test_value_shape.
"""Testovi za ValueShapeProducer (V3_2 C2)."""
from __future__ import annotations

from parser_studio.application.extraction.producers.value_shape import ValueShapeProducer
from parser_studio.domain.evidence import DocumentEvidence, Evidence, Locator
from parser_studio.ports.candidate_producer import CandidateProducer, FieldContext


def _make_locator(sheet: str = "Sheet1", row: int = 1, col: int = 1) -> Locator:
    return Locator(source_path="/test.xlsx", kind="excel", sheet=sheet, row=row, col=col)


def _make_cell(value: object, sheet: str = "Sheet1", row: int = 1, col: int = 1) -> Evidence:
    return Evidence(
        raw_value=value,
        raw_text=str(value) if value is not None else "",
        locator=_make_locator(sheet, row, col),
        element_type="excel_cell",
        source_id="excel",
    )


def _make_context(field: str) -> FieldContext:
    return FieldContext(document_id="doc-1", field=field)


class TestValueShapeBasics:
    def test_producer_id(self) -> None:
        assert ValueShapeProducer().producer_id == "value_shape"

    def test_satisfies_protocol(self) -> None:
        assert isinstance(ValueShapeProducer(), CandidateProducer)


class TestValueShapeSupports:
    def test_supports_pattern_field(self) -> None:
        producer = ValueShapeProducer()
        for field in ("invoice_number", "invoice_date", "currency",
                      "kolicina", "jedinicna_cijena", "iznos",
                      "tarifni_broj", "zemlja_porijekla"):
            assert producer.supports(_make_context(field)), (
                f"ValueShapeProducer should support {field}"
            )

    def test_does_not_support_text_field(self) -> None:
        producer = ValueShapeProducer()
        for field in ("seller_name", "buyer_name", "naziv_robe"):
            assert not producer.supports(_make_context(field))


class TestValueShapePropose:
    def test_invoice_number_pattern(self) -> None:
        """Pattern 'INV-001', 'FA-1', '12345' match-a invoice_number."""
        doc = DocumentEvidence(
            document_id="doc-1",
            source_path="/test.xlsx",
            cells=[
                _make_cell("INV-001"),
                _make_cell("FA-1"),
                _make_cell("12345"),
                _make_cell("Pekabesko"),  # tekst - NE match-a
            ],
        )
        cands = ValueShapeProducer().propose(doc, _make_context("invoice_number"))
        values = {c.raw_value for c in cands}
        assert values == {"INV-001", "FA-1", "12345"}
        assert "Pekabesko" not in values

    def test_currency_pattern(self) -> None:
        """3 velika slova."""
        doc = DocumentEvidence(
            document_id="doc-1",
            source_path="/test.xlsx",
            cells=[
                _make_cell("EUR"),
                _make_cell("USD"),
                _make_cell("BAM"),
                _make_cell("EURX"),  # 4 slova - NE match-a
                _make_cell("eur"),  # lowercase - NE match-a
            ],
        )
        cands = ValueShapeProducer().propose(doc, _make_context("currency"))
        values = {c.raw_value for c in cands}
        assert values == {"EUR", "USD", "BAM"}

    def test_kolicina_numeric_pattern(self) -> None:
        """Decimal ili integer."""
        doc = DocumentEvidence(
            document_id="doc-1",
            source_path="/test.xlsx",
            cells=[
                _make_cell("10"),
                _make_cell("10.5"),
                _make_cell("120,5"),  # hrvatski separator
                _make_cell("abc"),  # tekst
            ],
        )
        cands = ValueShapeProducer().propose(doc, _make_context("kolicina"))
        values = {c.raw_value for c in cands}
        assert "10" in values
        assert "abc" not in values

    def test_zemlja_iso_alpha2(self) -> None:
        """2 velika slova."""
        doc = DocumentEvidence(
            document_id="doc-1",
            source_path="/test.xlsx",
            cells=[
                _make_cell("MK"),  # Makedonija
                _make_cell("BA"),  # BiH
                _make_cell("HR"),  # Hrvatska
                _make_cell("MKD"),  # 3 slova - NE match-a
                _make_cell("mk"),  # lowercase - NE match-a
            ],
        )
        cands = ValueShapeProducer().propose(doc, _make_context("zemlja_porijekla"))
        values = {c.raw_value for c in cands}
        assert values == {"MK", "BA", "HR"}

    def test_unsupported_field(self) -> None:
        """seller_name nema shape pattern — vrati prazno."""
        doc = DocumentEvidence(
            document_id="doc-1",
            source_path="/test.xlsx",
            cells=[_make_cell("Pekabesko")],
        )
        cands = ValueShapeProducer().propose(doc, _make_context("seller_name"))
        assert cands == []

    def test_empty_document(self) -> None:
        doc = DocumentEvidence(document_id="doc-1", source_path="/test.xlsx")
        cands = ValueShapeProducer().propose(doc, _make_context("invoice_number"))
        assert cands == []

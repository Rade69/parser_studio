# Tests: application/extraction/producers/test_table_header.
"""Testovi za TableHeaderProducer (V3_2 C2)."""
from __future__ import annotations

from parser_studio.application.extraction.producers.table_header import TableHeaderProducer
from parser_studio.domain.evidence import DocumentEvidence, Evidence, Locator
from parser_studio.ports.candidate_producer import CandidateProducer, FieldContext


def _make_locator(sheet: str = "Sheet1", row: int = 1, col: int = 1) -> Locator:
    return Locator(source_path="/test.xlsx", kind="excel", sheet=sheet, row=row, col=col)


def _make_cell(value: object, sheet: str, row: int, col: int) -> Evidence:
    return Evidence(
        raw_value=value,
        raw_text=str(value) if value is not None else "",
        locator=_make_locator(sheet, row, col),
        element_type="excel_cell",
        source_id="excel",
    )


def _make_context(field: str) -> FieldContext:
    return FieldContext(document_id="doc-1", field=field)


class TestTableHeaderBasics:
    def test_producer_id(self) -> None:
        assert TableHeaderProducer().producer_id == "table_header"

    def test_satisfies_protocol(self) -> None:
        assert isinstance(TableHeaderProducer(), CandidateProducer)


class TestTableHeaderPropose:
    def test_header_row1_items_2_to_4(self) -> None:
        """Header u redu 1, items u redovima 2-4. Vraca 3 Kandidata za svaku kolonu."""
        doc = DocumentEvidence(
            document_id="doc-1",
            source_path="/test.xlsx",
            cells=[
                _make_cell("Šifra", "Sheet1", 1, 1),
                _make_cell("Naziv", "Sheet1", 1, 2),
                _make_cell("Količina", "Sheet1", 1, 3),
                _make_cell("S-001", "Sheet1", 2, 1),
                _make_cell("Item A", "Sheet1", 2, 2),
                _make_cell("10", "Sheet1", 2, 3),
                _make_cell("S-002", "Sheet1", 3, 1),
                _make_cell("Item B", "Sheet1", 3, 2),
                _make_cell("20", "Sheet1", 3, 3),
                _make_cell("S-003", "Sheet1", 4, 1),
                _make_cell("Item C", "Sheet1", 4, 2),
                _make_cell("30", "Sheet1", 4, 3),
            ],
        )
        producer = TableHeaderProducer()

        # Test za sifra_proizvoda
        cands = producer.propose(doc, _make_context("sifra_proizvoda"))
        assert len(cands) == 3
        assert {c.raw_value for c in cands} == {"S-001", "S-002", "S-003"}

        # Test za naziv_robe
        cands = producer.propose(doc, _make_context("naziv_robe"))
        assert len(cands) == 3
        assert {c.raw_value for c in cands} == {"Item A", "Item B", "Item C"}

        # Test za kolicina
        cands = producer.propose(doc, _make_context("kolicina"))
        assert len(cands) == 3
        assert {c.raw_value for c in cands} == {"10", "20", "30"}

    def test_no_header_found(self) -> None:
        doc = DocumentEvidence(
            document_id="doc-1",
            source_path="/test.xlsx",
            cells=[_make_cell("x", "Sheet1", 1, 1)],
        )
        cands = TableHeaderProducer().propose(doc, _make_context("invoice_number"))
        assert cands == []

    def test_unknown_field(self) -> None:
        doc = DocumentEvidence(
            document_id="doc-1",
            source_path="/test.xlsx",
            cells=[
                _make_cell("Broj fakture", "Sheet1", 1, 1),
                _make_cell("INV-001", "Sheet1", 2, 1),
            ],
        )
        cands = TableHeaderProducer().propose(doc, _make_context("unknown"))
        assert cands == []

    def test_english_header(self) -> None:
        """Engleski 'Invoice No' match-a invoice_number."""
        doc = DocumentEvidence(
            document_id="doc-1",
            source_path="/test.xlsx",
            cells=[
                _make_cell("Invoice No", "Sheet1", 1, 1),
                _make_cell("INV-001", "Sheet1", 2, 1),
                _make_cell("INV-002", "Sheet1", 3, 1),
            ],
        )
        ctx = FieldContext(document_id="doc-1", field="invoice_number", language="en")
        cands = TableHeaderProducer().propose(doc, ctx)
        assert len(cands) == 2
        assert {c.raw_value for c in cands} == {"INV-001", "INV-002"}

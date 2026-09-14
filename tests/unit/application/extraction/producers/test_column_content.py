# Tests: application/extraction/producers/test_column_content.
"""Testovi za ColumnContentProducer (V3_2 C2)."""
from __future__ import annotations

from parser_studio.application.extraction.producers.column_content import (
    ColumnContentProducer,
)
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


class TestColumnContentBasics:
    def test_producer_id(self) -> None:
        assert ColumnContentProducer().producer_id == "column_content"

    def test_satisfies_protocol(self) -> None:
        assert isinstance(ColumnContentProducer(), CandidateProducer)


class TestColumnContentPropose:
    def test_column_all_values(self) -> None:
        """Svi elementi u koloni match-a field."""
        doc = DocumentEvidence(
            document_id="doc-1",
            source_path="/test.xlsx",
            cells=[
                _make_cell("Šifra", "Sheet1", 1, 1),
                _make_cell("S-001", "Sheet1", 2, 1),
                _make_cell("S-002", "Sheet1", 3, 1),
                _make_cell("S-003", "Sheet1", 4, 1),
            ],
        )
        cands = ColumnContentProducer().propose(doc, _make_context("sifra_proizvoda"))
        assert len(cands) == 4  # header + 3 items

    def test_no_header_match(self) -> None:
        doc = DocumentEvidence(
            document_id="doc-1",
            source_path="/test.xlsx",
            cells=[_make_cell("x", "Sheet1", 1, 1)],
        )
        cands = ColumnContentProducer().propose(doc, _make_context("invoice_number"))
        assert cands == []

    def test_columns_mix(self) -> None:
        """Identificiraj pravu kolonu, vrati samo nju."""
        doc = DocumentEvidence(
            document_id="doc-1",
            source_path="/test.xlsx",
            cells=[
                _make_cell("Šifra", "Sheet1", 1, 1),
                _make_cell("Naziv", "Sheet1", 1, 2),
                _make_cell("S-001", "Sheet1", 2, 1),
                _make_cell("Item A", "Sheet1", 2, 2),
            ],
        )
        cands = ColumnContentProducer().propose(doc, _make_context("naziv_robe"))
        values = {c.raw_value for c in cands}
        assert values == {"Naziv", "Item A"}
        # NE sadrzi Sifra/S-001
        assert "S-001" not in values

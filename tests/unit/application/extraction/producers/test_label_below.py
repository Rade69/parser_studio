# Tests: application/extraction/producers/test_label_below.
"""Testovi za LabelBelowProducer (V3_2 C2)."""
from __future__ import annotations

from parser_studio.application.extraction.producers.label_below import LabelBelowProducer
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


def _make_context(field: str = "invoice_number") -> FieldContext:
    return FieldContext(document_id="doc-1", field=field)


def _make_doc(*cells: Evidence) -> DocumentEvidence:
    return DocumentEvidence(document_id="doc-1", source_path="/test.xlsx", cells=list(cells))


class TestLabelBelowBasics:
    def test_producer_id(self) -> None:
        assert LabelBelowProducer().producer_id == "label_below"

    def test_satisfies_protocol(self) -> None:
        assert isinstance(LabelBelowProducer(), CandidateProducer)


class TestLabelBelowPropose:
    def test_label_a1_value_a2(self) -> None:
        """Labela u A1, vrijednost u A2."""
        doc = _make_doc(
            _make_cell("Broj fakture", "Sheet1", 1, 1),
            _make_cell("INV-001", "Sheet1", 2, 1),
        )
        cands = LabelBelowProducer().propose(doc, _make_context("invoice_number"))
        assert len(cands) == 1
        assert cands[0].raw_value == "INV-001"

    def test_no_value_below(self) -> None:
        doc = _make_doc(
            _make_cell("Broj fakture", "Sheet1", 1, 1),
        )
        cands = LabelBelowProducer().propose(doc, _make_context("invoice_number"))
        assert cands == []

    def test_no_match(self) -> None:
        doc = _make_doc(
            _make_cell("Datum", "Sheet1", 1, 1),
            _make_cell("2026-09-14", "Sheet1", 2, 1),
        )
        cands = LabelBelowProducer().propose(doc, _make_context("invoice_number"))
        assert cands == []

    def test_unknown_field(self) -> None:
        doc = _make_doc(
            _make_cell("Broj fakture", "Sheet1", 1, 1),
            _make_cell("INV-001", "Sheet1", 2, 1),
        )
        cands = LabelBelowProducer().propose(doc, _make_context("unknown"))
        assert cands == []

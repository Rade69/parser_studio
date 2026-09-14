# Tests: application/extraction/producers/test_label_right.
"""Testovi za LabelRightProducer (V3_2 C2)."""
from __future__ import annotations

from parser_studio.application.extraction.producers.label_right import LabelRightProducer
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


def _make_context(field: str = "invoice_number", language: str = "bs") -> FieldContext:
    return FieldContext(document_id="doc-1", field=field, language=language)


def _make_doc(*cells: Evidence) -> DocumentEvidence:
    return DocumentEvidence(
        document_id="doc-1",
        source_path="/test.xlsx",
        cells=list(cells),
    )


class TestLabelRightBasics:
    def test_producer_id(self) -> None:
        producer = LabelRightProducer()
        assert producer.producer_id == "label_right"

    def test_supports_any_field(self) -> None:
        producer = LabelRightProducer()
        for field in ("invoice_number", "currency", "iznos"):
            assert producer.supports(_make_context(field=field))

    def test_satisfies_protocol(self) -> None:
        producer = LabelRightProducer()
        assert isinstance(producer, CandidateProducer)


class TestLabelRightPropose:
    def test_label_in_a1_value_in_b1(self) -> None:
        """Klasičan slučaj: 'Broj fakture' u A1, 'INV-001' u B1."""
        doc = _make_doc(
            _make_cell("Broj fakture", "Sheet1", 1, 1),
            _make_cell("INV-001", "Sheet1", 1, 2),
        )
        producer = LabelRightProducer()
        candidates = producer.propose(doc, _make_context("invoice_number"))

        assert len(candidates) == 1
        assert candidates[0].raw_value == "INV-001"
        assert candidates[0].field == "invoice_number"
        assert candidates[0].producer_id == "label_right"

    def test_no_match(self) -> None:
        doc = _make_doc(
            _make_cell("Datum", "Sheet1", 1, 1),
            _make_cell("2026-09-14", "Sheet1", 1, 2),
        )
        producer = LabelRightProducer()
        candidates = producer.propose(doc, _make_context("invoice_number"))
        assert candidates == []

    def test_no_value_right_of_label(self) -> None:
        """Labela na A1, ali B1 prazan."""
        doc = _make_doc(
            _make_cell("Broj fakture", "Sheet1", 1, 1),
        )
        producer = LabelRightProducer()
        candidates = producer.propose(doc, _make_context("invoice_number"))
        assert candidates == []

    def test_unknown_field(self) -> None:
        """Field koji nije u ConceptLibrary — vrati prazno."""
        doc = _make_doc(
            _make_cell("Broj fakture", "Sheet1", 1, 1),
            _make_cell("INV-001", "Sheet1", 1, 2),
        )
        producer = LabelRightProducer()
        candidates = producer.propose(
            doc, _make_context("nonexistent_field_xyz")
        )
        assert candidates == []

    def test_multiple_labels_same_field(self) -> None:
        """Više redova sa istom labelom — svaki daje kandidata."""
        doc = _make_doc(
            _make_cell("Broj fakture", "Sheet1", 1, 1),
            _make_cell("INV-001", "Sheet1", 1, 2),
            _make_cell("Broj fakture", "Sheet1", 3, 1),
            _make_cell("INV-002", "Sheet1", 3, 2),
        )
        producer = LabelRightProducer()
        candidates = producer.propose(doc, _make_context("invoice_number"))
        assert len(candidates) == 2
        values = {c.raw_value for c in candidates}
        assert values == {"INV-001", "INV-002"}

    def test_english_alias(self) -> None:
        """Engleski alias 'Invoice No' match-a invoice_number."""
        doc = _make_doc(
            _make_cell("Invoice No", "Sheet1", 1, 1),
            _make_cell("INV-001", "Sheet1", 1, 2),
        )
        producer = LabelRightProducer()
        candidates = producer.propose(
            doc, _make_context("invoice_number", language="en")
        )
        assert len(candidates) == 1
        assert candidates[0].raw_value == "INV-001"

    def test_empty_document(self) -> None:
        producer = LabelRightProducer()
        doc = _make_doc()
        candidates = producer.propose(doc, _make_context("invoice_number"))
        assert candidates == []

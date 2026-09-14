# Tests: extraction/producers/excel_header.
from __future__ import annotations

from pathlib import Path

import pytest
from openpyxl import Workbook

from parser_studio.adapters.documents.excel_reader import ExcelDocumentReader
from parser_studio.application.extraction.producers.excel_header import (
    ExcelHeaderProducer,
)
from parser_studio.ports.candidate_producer import (
    CandidateProducer,
    FieldContext,
)


@pytest.fixture
def sample_invoice_xlsx(tmp_path: Path) -> Path:
    """Inicijalni redovi + header red + stavke."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Faktura"
    ws.append(["SUMAPROM DOO", None, None, "Faktura br.", "059/2022"])
    ws.append([])
    ws.append(["Pos.", "Item Code", "Description", "U.M.", "Quantity", "Unit Price", "Amount"])
    ws.append([1, "A-100", "STARTNO UZE 4mm", "KOM", 5, 8.80, 44.00])
    ws.append([2, "B-200", "NOZ KOSILICE", "KOM", 10, 6.30, 63.00])
    ws.append([3, "C-300", "LANAC", "KOM", 3, 12.50, 37.50])
    path = tmp_path / "invoice.xlsx"
    wb.save(path)
    wb.close()
    return path


@pytest.fixture
def document_evidence(sample_invoice_xlsx: Path):
    """DocumentEvidence od sample invoice."""
    reader = ExcelDocumentReader()
    return reader.read(sample_invoice_xlsx)


class TestExcelHeaderProducerConstruction:
    def test_producer_id(self) -> None:
        producer = ExcelHeaderProducer()
        assert producer.producer_id == "excel_header"

    def test_implements_protocol(self) -> None:
        producer = ExcelHeaderProducer()
        assert isinstance(producer, CandidateProducer)


class TestSupports:
    def test_supports_any_context(self) -> None:
        producer = ExcelHeaderProducer()
        ctx = FieldContext(document_id="d1", field="quantity")
        assert producer.supports(ctx) is True


class TestProposeForQuantity:
    def test_returns_candidates_for_quantity(
        self, document_evidence
    ) -> None:
        producer = ExcelHeaderProducer()
        ctx = FieldContext(document_id=document_evidence.document_id, field="kolicina")
        candidates = producer.propose(document_evidence, ctx)
        assert len(candidates) == 3
        quantities = [c.raw_value for c in candidates]
        assert 5 in quantities
        assert 10 in quantities
        assert 3 in quantities

    def test_candidate_has_correct_locator(self, document_evidence) -> None:
        producer = ExcelHeaderProducer()
        ctx = FieldContext(document_id=document_evidence.document_id, field="kolicina")
        candidates = producer.propose(document_evidence, ctx)
        for cand in candidates:
            assert cand.locator.kind == "excel"
            assert cand.locator.sheet == "Faktura"
            assert cand.locator.row is not None
            assert cand.locator.col is not None

    def test_candidate_field_matches_context(self, document_evidence) -> None:
        producer = ExcelHeaderProducer()
        ctx = FieldContext(document_id=document_evidence.document_id, field="kolicina")
        candidates = producer.propose(document_evidence, ctx)
        for cand in candidates:
            assert cand.field == "kolicina"
            assert cand.producer_id == "excel_header"


class TestProposeForDescription:
    def test_returns_descriptions(self, document_evidence) -> None:
        producer = ExcelHeaderProducer()
        ctx = FieldContext(document_id=document_evidence.document_id, field="naziv_robe")
        candidates = producer.propose(document_evidence, ctx)
        assert len(candidates) == 3
        descriptions = [c.raw_value for c in candidates]
        assert "STARTNO UZE 4mm" in descriptions
        assert "NOZ KOSILICE" in descriptions
        assert "LANAC" in descriptions


class TestProposeForUnknownField:
    def test_unknown_field_returns_empty(self, document_evidence) -> None:
        producer = ExcelHeaderProducer()
        ctx = FieldContext(
            document_id=document_evidence.document_id,
            field="non_existent_field",
        )
        candidates = producer.propose(document_evidence, ctx)
        assert candidates == []


class TestEmptyDocument:
    def test_empty_document_returns_empty(self) -> None:
        from parser_studio.domain.evidence import DocumentEvidence

        producer = ExcelHeaderProducer()
        empty_doc = DocumentEvidence(document_id="empty", source_path="none")
        ctx = FieldContext(document_id="empty", field="kolicina")
        candidates = producer.propose(empty_doc, ctx)
        assert candidates == []

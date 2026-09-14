# Tests: extraction/analyze_invoice.
from __future__ import annotations

from pathlib import Path

import pytest
from openpyxl import Workbook

from parser_studio.adapters.documents.excel_reader import ExcelDocumentReader
from parser_studio.application.extraction.analyze_invoice import (
    AnalyzeInvoice,
    AnalyzeRequest,
)
from parser_studio.application.extraction.producers.excel_header import (
    ExcelHeaderProducer,
)
from parser_studio.application.ingest.import_document import (
    ImportDocument,
    ImportRequest,
)


@pytest.fixture
def invoice_xlsx(tmp_path: Path) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.title = "Faktura"
    ws.append(["SUMAPROM DOO", None, None, "Faktura br.", "059/2022"])
    ws.append([])
    ws.append(["Pos.", "Description", "Quantity", "Unit Price", "Amount"])
    ws.append([1, "Proizvod A", 5, 8.80, 44.00])
    ws.append([2, "Proizvod B", 10, 6.30, 63.00])
    path = tmp_path / "invoice.xlsx"
    wb.save(path)
    wb.close()
    return path


@pytest.fixture
def document_evidence(invoice_xlsx: Path):
    reader = ExcelDocumentReader()
    return reader.read(invoice_xlsx)


class TestAnalyzeInvoiceConstruction:
    def test_requires_at_least_one_producer(self) -> None:
        with pytest.raises(ValueError, match="bar jedan CandidateProducer"):
            AnalyzeInvoice(producers=())


class TestAnalyzeInvoiceExecute:
    def test_returns_extraction_draft(self, document_evidence) -> None:
        producer = ExcelHeaderProducer()
        use_case = AnalyzeInvoice(producers=(producer,))
        request = AnalyzeRequest(
            document=document_evidence,
            target_fields=("kolicina",),
        )
        draft = use_case.execute(request)
        assert draft.document_id == document_evidence.document_id
        assert "kolicina" in draft.candidates_by_field

    def test_aggregates_candidates_for_field(
        self, document_evidence
    ) -> None:
        producer = ExcelHeaderProducer()
        use_case = AnalyzeInvoice(producers=(producer,))
        request = AnalyzeRequest(
            document=document_evidence,
            target_fields=("kolicina",),
        )
        draft = use_case.execute(request)
        candidates = draft.candidates_for("kolicina")
        assert len(candidates) == 2

    def test_empty_target_fields(self, document_evidence) -> None:
        producer = ExcelHeaderProducer()
        use_case = AnalyzeInvoice(producers=(producer,))
        request = AnalyzeRequest(
            document=document_evidence,
            target_fields=(),
        )
        draft = use_case.execute(request)
        assert draft.candidates_by_field == {}

    def test_unknown_target_field_returns_empty(self, document_evidence) -> None:
        producer = ExcelHeaderProducer()
        use_case = AnalyzeInvoice(producers=(producer,))
        request = AnalyzeRequest(
            document=document_evidence,
            target_fields=("nonexistent_field",),
        )
        draft = use_case.execute(request)
        assert draft.candidates_for("nonexistent_field") == ()

    def test_integration_with_import_use_case(self, invoice_xlsx: Path) -> None:
        """Test: ImportDocument + AnalyzeInvoice end-to-end (bez GUI)."""
        reader = ExcelDocumentReader()
        import_uc = ImportDocument(readers=(reader,))
        producer = ExcelHeaderProducer()
        analyze_uc = AnalyzeInvoice(producers=(producer,))

        import_result = import_uc.execute(ImportRequest(path=invoice_xlsx))
        analyze_request = AnalyzeRequest(
            document=import_result.document,
            target_fields=("kolicina", "naziv_robe"),
        )
        draft = analyze_uc.execute(analyze_request)
        assert "kolicina" in draft.candidates_by_field
        assert "naziv_robe" in draft.candidates_by_field

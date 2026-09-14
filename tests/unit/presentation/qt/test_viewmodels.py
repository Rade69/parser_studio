# Tests: presentation/qt/test_viewmodels.
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
from parser_studio.presentation.qt.viewmodels import ReviewInvoiceViewModel


@pytest.fixture
def draft(tmp_path: Path):
    wb = Workbook()
    ws = wb.active
    ws.title = "Faktura"
    ws.append(["Naziv", "Kolicina"])
    ws.append(["Proizvod A", 5])
    path = tmp_path / "vm_test.xlsx"
    wb.save(path)
    wb.close()

    reader = ExcelDocumentReader()
    producer = ExcelHeaderProducer()
    import_doc = ImportDocument(readers=(reader,))
    analyze_uc = AnalyzeInvoice(producers=(producer,))

    import_result = import_doc.execute(ImportRequest(path=path))
    return analyze_uc.execute(
        AnalyzeRequest(
            document=import_result.document,
            target_fields=("kolicina", "naziv_robe"),
        )
    )


class TestReviewInvoiceViewModel:
    def test_construction(self) -> None:
        vm = ReviewInvoiceViewModel()
        assert vm.draft is None
        assert vm.selected_field is None
        assert vm.confirmed_values == {}

    def test_load_draft(self, draft) -> None:
        vm = ReviewInvoiceViewModel()
        vm.load_draft(draft)
        assert vm.draft is draft

    def test_candidates_for_without_draft(self) -> None:
        vm = ReviewInvoiceViewModel()
        candidates = vm.candidates_for("kolicina")
        assert candidates == ()

    def test_candidates_for_with_draft(self, draft) -> None:
        vm = ReviewInvoiceViewModel()
        vm.load_draft(draft)
        candidates = vm.candidates_for("kolicina")
        assert len(candidates) >= 1

    def test_confirm_field(self) -> None:
        vm = ReviewInvoiceViewModel()
        vm.confirm_field("kolicina", 10)
        assert vm.confirmed_values["kolicina"] == 10

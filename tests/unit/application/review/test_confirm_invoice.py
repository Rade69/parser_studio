# Tests: review/confirm_invoice.
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
from parser_studio.application.review.confirm_invoice import (
    ConfirmInvoice,
    ConfirmRequest,
    FieldConfirmation,
)
from parser_studio.domain.evidence.locator import Locator
from parser_studio.domain.learning.learning_event import EventType


@pytest.fixture
def invoice_xlsx(tmp_path: Path) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.title = "Faktura"
    ws.append(["Quantity", "Unit Price"])
    ws.append([5, 8.80])
    path = tmp_path / "invoice.xlsx"
    wb.save(path)
    wb.close()
    return path


@pytest.fixture
def draft(invoice_xlsx: Path):
    reader = ExcelDocumentReader()
    import_uc = ImportDocument(readers=(reader,))
    producer = ExcelHeaderProducer()
    analyze_uc = AnalyzeInvoice(producers=(producer,))
    import_result = import_uc.execute(ImportRequest(path=invoice_xlsx))
    return analyze_uc.execute(
        AnalyzeRequest(
            document=import_result.document,
            target_fields=("kolicina",),
        )
    )


class TestConfirmInvoiceConstruction:
    def test_with_none_repo(self) -> None:
        # MVP: bez LearningRepository
        use_case = ConfirmInvoice(learning_repo=None)
        assert use_case is not None


class TestConfirmInvoiceExecute:
    def test_empty_confirmations_returns_empty(self, draft) -> None:
        use_case = ConfirmInvoice(learning_repo=None)
        request = ConfirmRequest(
            draft=draft,
            confirmations=(),
            actor="user:radovan",
        )
        events = use_case.execute(request)
        assert events == []

    def test_single_confirmation_generates_event(self, draft) -> None:
        use_case = ConfirmInvoice(learning_repo=None)
        confirmation = FieldConfirmation(
            field="kolicina",
            raw_value=5,
            normalized_value=5.0,
            locator=Locator(
                source_path="f.xlsx", kind="excel", sheet="Faktura"
            ),
            confirmed=True,
        )
        request = ConfirmRequest(
            draft=draft,
            confirmations=(confirmation,),
            actor="user:radovan",
        )
        events = use_case.execute(request)
        assert len(events) == 1
        assert events[0].event_type == EventType.USER_CONFIRMED
        assert events[0].document_id == draft.document_id
        assert events[0].field_name == "kolicina"
        assert events[0].new_value == 5.0
        assert events[0].old_value == 5
        assert events[0].source == "user:radovan"

    def test_multiple_confirmations(self, draft) -> None:
        use_case = ConfirmInvoice(learning_repo=None)
        conf1 = FieldConfirmation(
            field="kolicina",
            raw_value=5,
            normalized_value=5.0,
            locator=Locator(source_path="f.xlsx", kind="excel"),
            confirmed=True,
        )
        conf2 = FieldConfirmation(
            field="cijena_jed",
            raw_value=8.80,
            normalized_value=8.80,
            locator=Locator(source_path="f.xlsx", kind="excel"),
            confirmed=True,
        )
        request = ConfirmRequest(
            draft=draft,
            confirmations=(conf1, conf2),
            actor="user:radovan",
        )
        events = use_case.execute(request)
        assert len(events) == 2
        assert events[0].field_name == "kolicina"
        assert events[1].field_name == "cijena_jed"

    def test_with_learning_repo_stores_events(self, draft) -> None:
        """Ako repo postoji, ConfirmInvoice pohranjuje event-e."""

        class FakeRepo:
            def __init__(self) -> None:
                self.stored: list = []

            def append(self, event) -> None:
                self.stored.append(event)

        repo = FakeRepo()
        use_case = ConfirmInvoice(learning_repo=repo)
        confirmation = FieldConfirmation(
            field="kolicina",
            raw_value=5,
            normalized_value=5.0,
            locator=Locator(source_path="f.xlsx", kind="excel"),
            confirmed=True,
        )
        request = ConfirmRequest(
            draft=draft,
            confirmations=(confirmation,),
            actor="user:radovan",
        )
        events = use_case.execute(request)
        assert len(events) == 1
        assert len(repo.stored) == 1
        assert repo.stored[0] is events[0]

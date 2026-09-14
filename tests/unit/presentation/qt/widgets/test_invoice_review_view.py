# Tests: presentation/qt/widgets/test_invoice_review_view.
# Pokriva: InvoiceReviewView layout, draft binding, candidate prikaz, confirm signal.
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")

from parser_studio.domain.evidence import Candidate, DocumentEvidence, Evidence, Locator
from parser_studio.domain.extraction.extraction_draft import ExtractionDraft
from parser_studio.presentation.qt.viewmodels import ReviewInvoiceViewModel
from parser_studio.presentation.qt.widgets.invoice_review_view import InvoiceReviewView


def make_candidate(field: str, value: object, row: int = 0, col: int = 0) -> Candidate:
    return Candidate(
        field=field,
        raw_value=value,
        normalized_value=value,
        locator=Locator(
            source_path="a.xlsx",
            kind="excel",
            sheet="Sheet1",
            row=row,
            col=col,
        ),
        evidence="cell",
        producer_id="test-producer",
    )


def make_draft() -> ExtractionDraft:
    cell = Evidence(
        raw_value="42",
        raw_text="42",
        locator=Locator(
            source_path="a.xlsx",
            kind="excel",
            sheet="Sheet1",
            row=0,
            col=0,
        ),
        element_type="cell",
    )
    document = DocumentEvidence(
        document_id="d1",
        source_path="a.xlsx",
        cells=[cell],
    )
    return ExtractionDraft(
        document_id="d1",
        document=document,
        candidates_by_field={
            "kolicina": (make_candidate("kolicina", "42", row=0, col=0),),
            "naziv_robe": (make_candidate("naziv_robe", "Proizvod A", row=1, col=0),),
        },
    )


def make_view(qtbot, viewmodel: ReviewInvoiceViewModel | None = None) -> InvoiceReviewView:
    view = InvoiceReviewView(viewmodel=viewmodel or ReviewInvoiceViewModel())
    qtbot.addWidget(view)
    return view


def test_construction(qtbot) -> None:
    view = make_view(qtbot)
    assert view.cell_table is not None
    assert view.field_selector is not None
    assert view.candidate_list is not None
    assert view.value_input is not None
    assert view.confirm_button is not None
    assert view.confirm_button.text() == "Confirm"


def test_load_draft_populates_fields(qtbot) -> None:
    view = make_view(qtbot)
    view.load_draft(make_draft())
    items = [view.field_selector.itemText(i) for i in range(view.field_selector.count())]
    assert items == ["kolicina", "naziv_robe"]


def test_load_draft_populates_cell_table(qtbot) -> None:
    view = make_view(qtbot)
    view.load_draft(make_draft())
    assert view.cell_table.rowCount() == 1


def test_candidates_displayed_for_default_field(qtbot) -> None:
    view = make_view(qtbot)
    view.load_draft(make_draft())
    # default field je prvi sortirani: "kolicina" (1 kandidat)
    assert view.candidate_list.count() == 1


def test_confirm_emits_signal(qtbot) -> None:
    view = make_view(qtbot)
    view.load_draft(make_draft())
    view.field_selector.setCurrentText("kolicina")
    view.value_input.setText("99")
    with qtbot.waitSignal(view.confirmed, timeout=2000) as blocker:
        view.confirm_button.click()
    assert blocker.args == ["kolicina", "99"]


def test_confirm_updates_viewmodel(qtbot) -> None:
    viewmodel = ReviewInvoiceViewModel()
    view = make_view(qtbot, viewmodel=viewmodel)
    view.load_draft(make_draft())
    view.field_selector.setCurrentText("kolicina")
    view.value_input.setText("99")
    view.confirm_button.click()
    assert viewmodel.confirmed_values["kolicina"] == "99"


def test_confirm_without_draft_no_crash(qtbot) -> None:
    viewmodel = ReviewInvoiceViewModel()
    view = make_view(qtbot, viewmodel=viewmodel)
    view.confirm_button.click()
    assert viewmodel.confirmed_values == {}

# Tests: presentation/qt/widgets/test_cell_table_view.
# Pokriva: CellTableView read-only ponasanje + load_document + highlight.
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QTableWidget

from parser_studio.domain.evidence import DocumentEvidence, Evidence, Locator
from parser_studio.presentation.qt.widgets.cell_table_view import CellTableView

_HIGHLIGHT_COLOR = "#ffe08a"


def make_evidence(
    row: int,
    col: int,
    *,
    sheet: str = "Sheet1",
    value: object = "x",
    element_type: str = "cell",
) -> Evidence:
    return Evidence(
        raw_value=value,
        raw_text=str(value),
        locator=Locator(
            source_path="a.xlsx",
            kind="excel",
            sheet=sheet,
            row=row,
            col=col,
        ),
        element_type=element_type,
    )


def make_document(*cells: Evidence) -> DocumentEvidence:
    return DocumentEvidence(
        document_id="doc-1",
        source_path="a.xlsx",
        cells=list(cells),
    )


def test_construction_is_read_only(qtbot) -> None:
    view = CellTableView()
    qtbot.addWidget(view)
    assert view.editTriggers() == QTableWidget.NoEditTriggers


def test_load_document_populates_rows(qtbot) -> None:
    view = CellTableView()
    qtbot.addWidget(view)
    view.load_document(make_document(make_evidence(0, 0), make_evidence(0, 1)))
    assert view.rowCount() == 2
    assert view.columnCount() == 5


def test_load_document_cell_content(qtbot) -> None:
    view = CellTableView()
    qtbot.addWidget(view)
    view.load_document(make_document(make_evidence(3, 2, sheet="List", value="42")))
    assert view.rowCount() == 1
    assert view.item(0, 0).text() == "List"
    assert view.item(0, 1).text() == "3"
    assert view.item(0, 2).text() == "2"
    assert view.item(0, 3).text() == "42"
    assert view.item(0, 4).text() == "cell"


def test_load_document_clears_previous(qtbot) -> None:
    view = CellTableView()
    qtbot.addWidget(view)
    view.load_document(
        make_document(make_evidence(0, 0), make_evidence(0, 1), make_evidence(0, 2))
    )
    assert view.rowCount() == 3
    view.load_document(make_document(make_evidence(0, 0)))
    assert view.rowCount() == 1


def test_load_document_empty(qtbot) -> None:
    view = CellTableView()
    qtbot.addWidget(view)
    view.load_document(make_document())
    assert view.rowCount() == 0


def test_highlight_locator(qtbot) -> None:
    view = CellTableView()
    qtbot.addWidget(view)
    view.load_document(
        make_document(make_evidence(0, 0, value="a"), make_evidence(1, 0, value="b"))
    )
    view.highlight_locator(
        Locator(source_path="a.xlsx", kind="excel", sheet="Sheet1", row=1, col=0)
    )
    assert view.item(1, 0).background().color().name() == _HIGHLIGHT_COLOR
    assert view.item(0, 0).background().color().name() != _HIGHLIGHT_COLOR


def test_clear_highlights(qtbot) -> None:
    view = CellTableView()
    qtbot.addWidget(view)
    view.load_document(make_document(make_evidence(0, 0, value="a")))
    view.highlight_locator(
        Locator(source_path="a.xlsx", kind="excel", sheet="Sheet1", row=0, col=0)
    )
    assert view.item(0, 0).background().color().name() == _HIGHLIGHT_COLOR
    view.clear_highlights()
    assert view.item(0, 0).background().color().name() != _HIGHLIGHT_COLOR

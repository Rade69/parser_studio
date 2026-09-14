# Tests: cell_compat.
from __future__ import annotations

from dataclasses import dataclass

from parser_studio.domain.evidence import cell_to_evidence


@dataclass
class FakeCell:
    """Mimic legacy Cell iz core/documents/base.py za testiranje adaptera."""

    value: object
    row: int
    col: int
    page: int | None = None
    x0: float | None = None
    x1: float | None = None
    top: float | None = None
    sheet: str | None = None

    @property
    def text(self) -> str:
        return "" if self.value is None else str(self.value).strip()


class TestCellCompatExcel:
    def test_excel_cell_full(self) -> None:
        cell = FakeCell(
            value=42,
            row=3,
            col=5,
            sheet="Sheet1",
        )
        ev = cell_to_evidence(cell, source_id="src-1")
        assert ev.raw_value == 42
        assert ev.raw_text == "42"
        assert ev.element_type == "excel_cell"
        assert ev.source_id == "src-1"
        assert ev.locator.sheet == "Sheet1"
        assert ev.locator.row == 3
        assert ev.locator.col == 5
        assert ev.locator.kind == "excel"

    def test_excel_cell_text_value(self) -> None:
        cell = FakeCell(
            value="Product A",
            row=1,
            col=1,
            sheet="Sheet1",
        )
        ev = cell_to_evidence(cell)
        assert ev.raw_value == "Product A"
        assert ev.raw_text == "Product A"


class TestCellCompatPdf:
    def test_pdf_cell_full(self) -> None:
        cell = FakeCell(
            value="100.50",
            row=0,
            col=0,
            page=2,
            x0=0.1,
            x1=0.5,
            top=0.8,
        )
        ev = cell_to_evidence(cell)
        assert ev.element_type == "pdf_cell"
        assert ev.locator.kind == "pdf"
        assert ev.locator.page == 2
        assert ev.locator.bbox is not None
        assert ev.locator.bbox[0] == 0.1
        assert ev.locator.bbox[2] == 0.5

    def test_pdf_cell_no_bbox(self) -> None:
        cell = FakeCell(value="x", row=0, col=0, page=1)
        ev = cell_to_evidence(cell)
        assert ev.locator.bbox is None


class TestCellCompatOptional:
    def test_none_source_id(self) -> None:
        cell = FakeCell(value=1, row=0, col=0, sheet="S")
        ev = cell_to_evidence(cell)
        assert ev.source_id is None

    def test_round_trip_no_loss_excel(self) -> None:
        cell = FakeCell(value="ABC123", row=5, col=7, sheet="Data")
        ev = cell_to_evidence(cell)
        assert ev.raw_value == "ABC123"
        assert ev.raw_text == "ABC123"
        assert ev.locator.sheet == "Data"
        assert ev.locator.row == 5
        assert ev.locator.col == 7

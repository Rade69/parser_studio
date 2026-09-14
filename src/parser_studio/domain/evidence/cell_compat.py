# Domain: cell_compat.
# Posjeduje: cell_to_evidence(Cell) -> Evidence adapter.
# Ne zna za: SQLite, PySide6, Docling, contract (TYPE_CHECKING za legacy Cell).
"""Compatibility adapter: legacy Cell -> novi Evidence.

Cell: value, row, col, page, x0, x1, top, sheet (iz core/documents/base.py)
Evidence: raw_value, raw_text, locator, element_type, source_id

Legacy `core/` ostaje netaknut do A3 (Excel adapter). Ovaj adapter je
READ-ONLY u odnosu na Cell: ne mijenja Cell, samo ga prevodi u Evidence.

Koristimo TYPE_CHECKING import za Cell da izbjegnemo runtime ciklicnu
zavisnost izmedju `src/parser_studio/domain/evidence/` i `core/`.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from .evidence import Evidence
from .locator import Locator

if TYPE_CHECKING:
    from core.documents.base import Cell  # type: ignore[import-not-found]


def cell_to_evidence(cell: Cell, source_id: str | None = None) -> Evidence:
    """Pretvori legacy Cell u novi Evidence bez gubitka informacije.

    Mapping:
        Cell.value           -> Evidence.raw_value
        Cell.text            -> Evidence.raw_text (computed property)
        Cell.sheet, row, col -> Locator(sheet, row, col)
        Cell.page, x0..top   -> Locator(page, bbox) ako je page None ili bbox None, ostaje None

    Napomena: Cell koristi zasebna polja (x0, x1, top) za PDF bbox,
    a Evidence Locator ocekuje tuple (x0, y0, x1, y1). Pretpostavljamo
    da Cell.x0/x1/top odgovaraju redom (x0, x1, top) gdje je top = y1.
    Ako Cell ima razlicit layout, adapter treba prilagoditi.
    """
    if cell.sheet is not None:
        bbox = None
        if cell.x0 is not None and cell.x1 is not None and cell.top is not None:
            bbox = (float(cell.x0), float(cell.top), float(cell.x1), float(cell.top))
        locator = Locator(
            source_path="",
            kind="excel" if cell.sheet else "pdf",
            page=cell.page,
            bbox=bbox,
            sheet=cell.sheet,
            row=cell.row,
            col=cell.col,
        )
    else:
        bbox = None
        if cell.x0 is not None and cell.x1 is not None and cell.top is not None:
            bbox = (float(cell.x0), float(cell.top), float(cell.x1), float(cell.top))
        locator = Locator(
            source_path="",
            kind="pdf",
            page=cell.page,
            bbox=bbox,
            row=cell.row,
            col=cell.col,
        )

    return Evidence(
        raw_value=cell.value,
        raw_text=cell.text,
        locator=locator,
        element_type="excel_cell" if cell.sheet else "pdf_cell",
        source_id=source_id,
    )

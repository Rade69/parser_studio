# Application helper: _sheet_utils.
# Posjeduje: extract_rows_from_document helper.
# Zna za: domain.evidence.DocumentEvidence.
# Ne zna za: SQLite, PySide6, Docling, openpyxl/xlrd, contract.
"""Helper za parsiranje DocumentEvidence u row matricu.

Internal helper za ExcelHeaderProducer i druge Excel-based producer-e.
Nije dio javnog API-ja; privremeno u istom paketu zbog jednostavnosti.
"""
from __future__ import annotations

from typing import Any

from parser_studio.domain.evidence import DocumentEvidence


def extract_rows_from_document(
    document: DocumentEvidence, sheet_name: str
) -> list[list[Any]]:
    """Izvuci 2D matricu redova iz DocumentEvidence za dati sheet.

    - Koristi cells sa Locator.row i Locator.col za pozicioniranje
    - Popunjava prazne celije sa None
    - Redovi sortirani po row indeksu (1-based)
    - Kolone sortirane po col indeksu (1-based)
    """
    sheet_cells = [c for c in document.cells if c.locator.sheet == sheet_name]
    if not sheet_cells:
        return []

    max_row = max(c.locator.row for c in sheet_cells)
    max_col = max(c.locator.col for c in sheet_cells)

    rows: list[list[Any]] = [[None for _ in range(max_col)] for _ in range(max_row)]
    for cell in sheet_cells:
        r = cell.locator.row - 1  # 0-based
        c = cell.locator.col - 1
        if 0 <= r < max_row and 0 <= c < max_col:
            rows[r][c] = cell.raw_value
    return rows

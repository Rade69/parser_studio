# Presentation: qt/widgets/cell_table_view.
# Posjeduje: CellTableView (read-only prikaz DocumentEvidence celija).
# Zna za: domain.evidence (DocumentEvidence/Evidence/Locator) + PySide6.
# Ne zna za: SQLite, Docling, openpyxl, contract.

"""CellTableView — read-only prikaz celija DocumentEvidence (V3 B4).

Prikazuje sheet/row/col/value/type za svaku Evidence celiju dokumenta.
Nije editable (review-only). Podrzava highlight pojedinacnih redova
prema Locator-u kandidata.
"""
from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem

from parser_studio.domain.evidence import DocumentEvidence, Evidence, Locator

_COLUMNS: tuple[str, ...] = ("Sheet", "Row", "Col", "Value", "Type")
_DEFAULT_COLOR = QColor("#ffffff")
_HIGHLIGHT_COLOR = QColor("#ffe08a")


class CellTableView(QTableWidget):
    """Read-only prikaz DocumentEvidence celija (sheet/row/col/value/type)."""

    def __init__(self, parent: QTableWidget | None = None) -> None:
        super().__init__(parent)
        self.setColumnCount(len(_COLUMNS))
        self.setHorizontalHeaderLabels(list(_COLUMNS))
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self._cells: list[Evidence] = []
        self._highlighted_rows: set[int] = set()

    def load_document(self, document: DocumentEvidence) -> None:
        """Popuni tabelu iz DocumentEvidence.cells (sheet/row/col/value/type)."""
        self._cells = list(document.cells)
        self._highlighted_rows.clear()
        self.setRowCount(len(self._cells))
        for row, evidence in enumerate(self._cells):
            locator = evidence.locator
            texts = (
                locator.sheet or "",
                "" if locator.row is None else str(locator.row),
                "" if locator.col is None else str(locator.col),
                self._value_text(evidence),
                evidence.element_type,
            )
            for col, text in enumerate(texts):
                item = QTableWidgetItem(text)
                item.setBackground(_DEFAULT_COLOR)
                self.setItem(row, col, item)

    @staticmethod
    def _value_text(evidence: Evidence) -> str:
        if evidence.raw_text:
            return evidence.raw_text
        return str(evidence.raw_value)

    def highlight_locator(self, locator: Locator) -> None:
        """Oznaci redove cije celije odgovaraju datom Locator-u (sheet/row/col)."""
        self._highlighted_rows = {
            row
            for row, evidence in enumerate(self._cells)
            if self._locator_matches(evidence.locator, locator)
        }
        self._apply_highlights()

    def clear_highlights(self) -> None:
        """Ukloni sve highlight oznake i vrati default pozadinu."""
        self._highlighted_rows.clear()
        self._apply_highlights()

    @staticmethod
    def _locator_matches(a: Locator, b: Locator) -> bool:
        return a.sheet == b.sheet and a.row == b.row and a.col == b.col

    def _apply_highlights(self) -> None:
        for row in range(self.rowCount()):
            color = _HIGHLIGHT_COLOR if row in self._highlighted_rows else _DEFAULT_COLOR
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item is not None:
                    item.setBackground(color)

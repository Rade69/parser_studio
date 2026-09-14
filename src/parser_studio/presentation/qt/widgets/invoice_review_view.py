# Presentation: qt/widgets/invoice_review_view.
# Posjeduje: InvoiceReviewView (glavni Review GUI widget, V3 B4).
# Zna za: domain.extraction (ExtractionDraft) + ReviewInvoiceViewModel + PySide6.
# Ne zna za: SQLite, Docling, openpyxl, contract.

"""InvoiceReviewView — glavni widget za review jedne fakture (V3 B4).

Sastoji se od:
- CellTableView (read-only prikaz celija dokumenta)
- field selector (QComboBox sa poljima draft-a)
- candidate list (QListWidget kandidata za selektovano polje)
- confirm panel (QLineEdit za vrijednost + "Confirm" dugme)

Emituje `confirmed(str, object)` signal kada korisnik potvrdi vrijednost.
"""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from parser_studio.domain.evidence import Candidate
from parser_studio.domain.extraction.extraction_draft import ExtractionDraft
from parser_studio.presentation.qt.viewmodels.review_invoice_viewmodel import (
    ReviewInvoiceViewModel,
)
from parser_studio.presentation.qt.widgets.cell_table_view import CellTableView


class InvoiceReviewView(QWidget):
    """Glavni view za Review Invoice GUI."""

    confirmed = Signal(str, object)  # field, value

    def __init__(
        self,
        viewmodel: ReviewInvoiceViewModel,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._viewmodel = viewmodel
        self._current_candidates: tuple[Candidate, ...] = ()
        self._init_ui()
        self._bind_viewmodel()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Celije dokumenta", self))
        self.cell_table = CellTableView(self)
        layout.addWidget(self.cell_table)

        layout.addWidget(QLabel("Polje", self))
        self.field_selector = QComboBox(self)
        layout.addWidget(self.field_selector)

        layout.addWidget(QLabel("Kandidati", self))
        self.candidate_list = QListWidget(self)
        layout.addWidget(self.candidate_list)

        confirm_row = QHBoxLayout()
        confirm_row.addWidget(QLabel("Vrijednost:", self))
        self.value_input = QLineEdit(self)
        confirm_row.addWidget(self.value_input)
        self.confirm_button = QPushButton("Confirm", self)
        confirm_row.addWidget(self.confirm_button)
        layout.addLayout(confirm_row)

    def _bind_viewmodel(self) -> None:
        self.field_selector.currentTextChanged.connect(self._on_field_changed)
        self.candidate_list.currentItemChanged.connect(self._on_candidate_selected)
        self.confirm_button.clicked.connect(self._on_confirm_clicked)
        if self._viewmodel.draft is not None:
            self._populate(self._viewmodel.draft)

    def load_draft(self, draft: ExtractionDraft) -> None:
        """Postavi draft u viewmodel i popuni view."""
        self._viewmodel.load_draft(draft)
        self._populate(draft)

    def _populate(self, draft: ExtractionDraft) -> None:
        self.cell_table.load_document(draft.document)
        fields = sorted(draft.candidates_by_field)
        self.field_selector.blockSignals(True)
        self.field_selector.clear()
        self.field_selector.addItems(fields)
        if fields:
            self.field_selector.setCurrentIndex(0)
        self.field_selector.blockSignals(False)
        if fields:
            self._on_field_changed(fields[0])
        else:
            self.candidate_list.clear()
            self._current_candidates = ()

    def _on_field_changed(self, field: str) -> None:
        self.candidate_list.clear()
        if not field:
            self._current_candidates = ()
            return
        self._current_candidates = self._viewmodel.candidates_for(field)
        for candidate in self._current_candidates:
            self.candidate_list.addItem(self._candidate_label(candidate))

    def _on_candidate_selected(
        self, current: QListWidgetItem | None, previous: QListWidgetItem | None
    ) -> None:
        if current is None:
            self.cell_table.clear_highlights()
            return
        index = self.candidate_list.row(current)
        if 0 <= index < len(self._current_candidates):
            self.cell_table.highlight_locator(self._current_candidates[index].locator)

    def _on_confirm_clicked(self) -> None:
        field = self.field_selector.currentText()
        if not field:
            return
        value = self.value_input.text().strip()
        self._viewmodel.confirm_field(field, value)
        self.confirmed.emit(field, value)

    @staticmethod
    def _candidate_label(candidate: Candidate) -> str:
        return f"{candidate.normalized_value} [{candidate.producer_id}]"

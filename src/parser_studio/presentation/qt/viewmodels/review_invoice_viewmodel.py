# Presentation: qt/viewmodels/review_invoice_viewmodel.
# Posjeduje: ReviewInvoiceViewModel placeholder (FAZA B / M4).
# Zna za: domain.evidence (Display Evidence u GUI).
# Ne zna za: SQLite, Docling, contract.

"""Review Invoice ViewModel — MVVM binding za Review GUI (FAZA B / M4).

MVP placeholder. Pravi ViewModel bude:
- Subscribe na ExtractionDraft iz AnalyzeInvoice use case
- Drzi state za UI (selektovani field, mode, itd.)
- Emit signale za View (dataChanged, itd.)

Za sada: samo konstrukcija i minimalan state.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from parser_studio.domain.evidence import Candidate
from parser_studio.domain.extraction.extraction_draft import ExtractionDraft


@dataclass
class ReviewInvoiceViewModel:
    """ViewModel za Review Invoice GUI.

    MVP placeholder: samo konstrukcija.
    FAZA B / M4 ce dodati Qt signal/slot binding.
    """

    draft: ExtractionDraft | None = None
    selected_field: str | None = None
    confirmed_values: dict[str, object] = field(default_factory=dict)

    def load_draft(self, draft: ExtractionDraft) -> None:
        """Postavi ExtractionDraft za prikaz."""
        self.draft = draft

    def candidates_for(self, field: str) -> tuple[Candidate, ...]:
        """Vrati kandidate za dato polje."""
        if self.draft is None:
            return ()
        return self.draft.candidates_for(field)

    def confirm_field(self, field: str, value: object) -> None:
        """Korisnik potvrdio vrijednost za polje."""
        self.confirmed_values[field] = value

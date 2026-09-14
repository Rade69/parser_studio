# Domain: extraction/extraction_draft.
# Posjeduje: ExtractionDraft dataclass.
# Ne zna za: SQLite, PySide6, Docling, openpyxl/xlrd, contract.
"""ExtractionDraft — rezultat AnalyzeInvoice: skup kandidata po polju.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from parser_studio.domain.evidence import Candidate, DocumentEvidence


@dataclass(frozen=True, slots=True)
class ExtractionDraft:
    """Agregat kandidata, konflikata i nepotpuno ekstrakovanih polja."""

    document_id: str
    document: DocumentEvidence
    candidates_by_field: dict[str, tuple[Candidate, ...]] = field(
        default_factory=dict
    )
    conflicts: tuple[tuple[str, Candidate, Candidate], ...] = ()
    unresolved: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.document_id:
            raise ValueError("document_id ne može biti prazan string")

    def candidates_for(self, field: str) -> tuple[Candidate, ...]:
        """Vrati sve kandidate za dato polje."""
        return self.candidates_by_field.get(field, ())

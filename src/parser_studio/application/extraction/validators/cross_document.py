# Application: extraction/validators/cross_document.
# Posjeduje: CrossDocumentValidator implementacija Validator.
# Zna za: domain.evidence, domain.extraction.extraction_draft.
# Ne zna za: SQLite, PySide6, Docling, contract, adapters.
"""CrossDocumentValidator — NO_MATCH provjera sa drugim dokumentima (V3_2 C4).

PLACEHOLDER: Puni implementation zahtijeva pristup drugim dokumentima
(via Profile Repository ili sl.). Za M3 (FAZA C/C4), ovaj validator
vraća INFO Issue koji signalizira da cross-document comparison
NIJE izvršen u ovom trenutku.

FAZA D (Oracle bootstrap) i FAZA E (Layout Learning) će implementirati
potpunu logiku koristeći LayoutProfile / LayoutFingerprint.
"""
from __future__ import annotations

from parser_studio.application.extraction.validators.base import (
    Issue,
    IssueSeverity,
)
from parser_studio.domain.extraction.extraction_draft import ExtractionDraft


class CrossDocumentValidator:
    """Cross-document comparison (placeholder za FAZA D)."""

    name: str = "cross_document"

    def validate(self, draft: ExtractionDraft) -> tuple[Issue, ...]:
        # Placeholder: FAZA D ce implementirati pravu cross-document logiku
        return (
            Issue(
                severity=IssueSeverity.INFO,
                field="",
                message=(
                    "Cross-document comparison nije izvrsen u ovoj verziji; "
                    "FAZA D (Oracle bootstrap) ce dodati pravu logiku"
                ),
                code="CD001",
            ),
        )


__all__ = ["CrossDocumentValidator"]

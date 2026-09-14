# Application: extraction/validators/structure.
# Posjeduje: StructureValidator implementacija Validator.
# Zna za: domain.evidence, domain.extraction.extraction_draft.
# Ne zna za: SQLite, PySide6, Docling, contract, adapters.
"""StructureValidator — provjera prisutnosti invoice/item polja (V3_2 C4 structure)."""
from __future__ import annotations

from parser_studio.application.extraction.validators.base import (
    Issue,
    IssueSeverity,
)
from parser_studio.domain.extraction.extraction_draft import ExtractionDraft

# 9 invoice polja po V3 B5 spec
REQUIRED_INVOICE_FIELDS = (
    "invoice_number",
    "invoice_date",
    "currency",
    "seller_name",
    "seller_tax_id",
    "buyer_name",
    "buyer_tax_id",
    "incoterm",
    "origin_statement",
)


class StructureValidator:
    """Provjera da draft sadrzi sva 9 invoice polja."""

    name: str = "structure"

    def validate(self, draft: ExtractionDraft) -> tuple[Issue, ...]:
        issues: list[Issue] = []
        present_fields = set(draft.candidates_by_field.keys())

        for required in REQUIRED_INVOICE_FIELDS:
            if required not in present_fields or not draft.candidates_by_field.get(required):
                issues.append(
                    Issue(
                        severity=IssueSeverity.ERROR,
                        field=required,
                        message=f"Obavezno invoice polje '{required}' nedostaje ili prazno",
                        code="ST001",
                    )
                )

        # Provjeri da draft ima bar jedan item kandidat (za items extraction)
        # ALI ExtractionDraft nema items — placeholder INFO
        if "lines" in draft.candidates_by_field:
            # Provjeri items count > 0
            item_lines = draft.candidates_by_field.get("lines", ())
            if not item_lines:
                issues.append(
                    Issue(
                        severity=IssueSeverity.WARNING,
                        field="lines",
                        message="Faktura nema items (lines prazan)",
                        code="ST002",
                    )
                )

        return tuple(issues)


__all__ = ["StructureValidator"]

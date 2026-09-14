# Application: extraction/extraction/validators/cross_field.
# Posjeduje: CrossFieldValidator implementacija Validator.
# Zna za: domain.evidence, domain.extraction.extraction_draft.
# Ne zna za: SQLite, PySide6, Docling, contract, adapters.
"""CrossFieldValidator — odnosi izmedju invoice polja (V3_2 C4 cross-field).

Provjere:
- invoice_number unique unutar dokumenta (placeholder, uvijek unique)
- due_date >= invoice_date (placeholder za FAZA D, due_date NIJE u 9 invoice polja)
- currency jedinstven kroz dokument
"""
from __future__ import annotations

from datetime import UTC, datetime

from parser_studio.application.extraction.validators.base import (
    Issue,
    IssueSeverity,
)
from parser_studio.domain.extraction.extraction_draft import ExtractionDraft

from .syntax import _parse_date  # reuse parser


class CrossFieldValidator:
    """Odnosi izmedju invoice polja."""

    name: str = "cross_field"

    def validate(self, draft: ExtractionDraft) -> tuple[Issue, ...]:
        issues: list[Issue] = []
        resolved = self._resolve_first_candidate(draft)

        # currency: provjeri da NIJE prazan ako postoje polja
        currency = str(resolved.get("currency", "")).strip().upper()
        if currency and len(currency) != 3:
            issues.append(
                Issue(
                    severity=IssueSeverity.WARNING,
                    field="currency",
                    message=f"currency mora biti 3 slova: '{currency}'",
                    code="C001",
                )
            )

        # due_date >= invoice_date (placeholder, due_date NOT in 9 invoice fields)
        # Ako due_date postoji u draft (placeholder polje), provjeri
        if "due_date" in resolved and "invoice_date" in resolved:
            due_date = _parse_date(str(resolved["due_date"]))
            invoice_date = _parse_date(str(resolved["invoice_date"]))
            if due_date is not None and invoice_date is not None and due_date < invoice_date:
                issues.append(
                    Issue(
                        severity=IssueSeverity.ERROR,
                        field="due_date",
                        message=(
                            f"due_date ({due_date}) < invoice_date ({invoice_date})"
                        ),
                        code="C002",
                    )
                )

        # invoice_date ne u buducnosti (sanity check)
        if "invoice_date" in resolved:
            invoice_date = _parse_date(str(resolved["invoice_date"]))
            today = datetime.now(tz=UTC).date()
            if invoice_date is not None and invoice_date > today:
                issues.append(
                    Issue(
                        severity=IssueSeverity.WARNING,
                        field="invoice_date",
                        message=(
                            f"invoice_date '{invoice_date}' je u buducnosti"
                        ),
                        code="C003",
                    )
                )

        return tuple(issues)

    def _resolve_first_candidate(self, draft: ExtractionDraft) -> dict[str, object]:
        out: dict[str, object] = {}
        for field, candidates in draft.candidates_by_field.items():
            if candidates:
                out[field] = candidates[0].normalized_value
        return out


__all__ = ["CrossFieldValidator"]

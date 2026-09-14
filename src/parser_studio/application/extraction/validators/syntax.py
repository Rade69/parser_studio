# Application: extraction/validators/syntax.
# Posjeduje: SyntaxValidator implementacija Validator.
# Zna za: domain.evidence, domain.extraction.extraction_draft.
# Ne zna za: SQLite, PySide6, Docling, contract, adapters.
"""SyntaxValidator — provjera formata invoice polja (V3_2 C4 syntax)."""
from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from parser_studio.application.extraction.validators.base import (
    Issue,
    IssueSeverity,
)
from parser_studio.domain.extraction.extraction_draft import ExtractionDraft

_DATE_PATTERNS = (
    "%Y-%m-%d",       # ISO 8601
    "%d.%m.%Y",       # BHS standard
    "%d/%m/%Y",
    "%Y/%m/%d",
)


def _parse_date(value: str) -> date | None:
    """Parsiraj string u date, vrati None ako ne uspije."""
    for fmt in _DATE_PATTERNS:
        try:
            # strptime returns naive datetime; convert to date.
            # Naive datetime je namjerno (invoice_date je samo datum, bez TZ)
            return datetime.strptime(value, fmt).date()  # noqa: DTZ007
        except ValueError:
            continue
    return None


class SyntaxValidator:
    """Validacija formata invoice polja."""

    name: str = "syntax"

    def validate(self, draft: ExtractionDraft) -> tuple[Issue, ...]:
        issues: list[Issue] = []
        resolved = _resolve_first_candidate(draft)

        # invoice_number: pattern (1-30 chars, alphanumeric + -/_)
        if "invoice_number" in resolved:
            v = str(resolved["invoice_number"]).strip()
            if not re.match(r"^[A-Z0-9\-_/]{1,30}$", v, re.IGNORECASE):
                issues.append(
                    Issue(
                        severity=IssueSeverity.WARNING,
                        field="invoice_number",
                        message=f"invoice_number format neocekivan: '{v}'",
                        code="S001",
                    )
                )

        # invoice_date: parsabilan datum
        if "invoice_date" in resolved:
            v = str(resolved["invoice_date"]).strip()
            parsed = _parse_date(v)
            if parsed is None:
                issues.append(
                    Issue(
                        severity=IssueSeverity.WARNING,
                        field="invoice_date",
                        message=f"invoice_date format neprepoznat: '{v}'",
                        code="S002",
                    )
                )

        # currency: 3 velika slova
        if "currency" in resolved:
            v = str(resolved["currency"]).strip().upper()
            if not re.match(r"^[A-Z]{3}$", v):
                issues.append(
                    Issue(
                        severity=IssueSeverity.WARNING,
                        field="currency",
                        message=f"currency mora biti 3 slova ISO 4217: '{v}'",
                        code="S003",
                    )
                )

        # seller_tax_id: digits-only 8-15 chars
        if "seller_tax_id" in resolved:
            v = str(resolved["seller_tax_id"]).strip()
            if not re.match(r"^\d{8,15}$", v):
                issues.append(
                    Issue(
                        severity=IssueSeverity.WARNING,
                        field="seller_tax_id",
                        message=f"seller_tax_id mora biti 8-15 cifara: '{v}'",
                        code="S004",
                    )
                )

        # kolicina: > 0 (numeric)
        if "kolicina" in resolved:
            v = str(resolved["kolicina"]).strip()
            try:
                num = Decimal(v.replace(",", "."))
                if num <= 0:
                    issues.append(
                        Issue(
                            severity=IssueSeverity.ERROR,
                            field="kolicina",
                            message=f"kolicina mora biti > 0: '{v}'",
                            code="S005",
                        )
                    )
            except InvalidOperation:
                issues.append(
                    Issue(
                        severity=IssueSeverity.ERROR,
                        field="kolicina",
                        message=f"kolicina nije numericka: '{v}'",
                        code="S006",
                    )
                )

        return tuple(issues)


def _resolve_first_candidate(draft: ExtractionDraft) -> dict[str, object]:
    """Vrati dict {field: normalized_value} koristeci prvi kandidat po polju.

    Validator uzima prvi kandidat kao 'resolved' vrijednost. Za kompleksniji
    resolution koristiti ResolveCandidates (FAZA C/C3).
    """
    out: dict[str, object] = {}
    for field, candidates in draft.candidates_by_field.items():
        if candidates:
            out[field] = candidates[0].normalized_value
    return out


__all__ = ["SyntaxValidator"]

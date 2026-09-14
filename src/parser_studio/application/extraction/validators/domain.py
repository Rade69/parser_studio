# Application: extraction/validators/domain.
# Posjeduje: DomainValidator implementacija Validator.
# Zna za: domain.evidence, domain.extraction.extraction_draft.
# Ne zna za: SQLite, PySide6, Docling, contract, adapters.
"""DomainValidator — domain-specific pravila (V3_2 C4 domain).

Provjere:
- seller_tax_id format po drzavi (placeholder za FAZA D, trenutno samo length)
- seller_name i buyer_name nisu isti
"""
from __future__ import annotations

import re

from parser_studio.application.extraction.validators.base import (
    Issue,
    IssueSeverity,
)
from parser_studio.domain.extraction.extraction_draft import ExtractionDraft


class DomainValidator:
    """Domain-specific pravila."""

    name: str = "domain"

    def validate(self, draft: ExtractionDraft) -> tuple[Issue, ...]:
        issues: list[Issue] = []
        resolved = self._resolve_first_candidate(draft)

        # seller_name == buyer_name (logic error)
        seller_name = str(resolved.get("seller_name", "")).strip()
        buyer_name = str(resolved.get("buyer_name", "")).strip()
        if seller_name and buyer_name and seller_name.lower() == buyer_name.lower():
            issues.append(
                Issue(
                    severity=IssueSeverity.WARNING,
                    field="seller_name",
                    message=(
                        f"seller_name i buyer_name su isti: '{seller_name}'"
                    ),
                    code="D001",
                )
            )

        # seller_tax_id: digits-only length validation
        seller_tax_id = str(resolved.get("seller_tax_id", "")).strip()
        if seller_tax_id and not re.match(r"^\d{8,15}$", seller_tax_id):
            issues.append(
                Issue(
                    severity=IssueSeverity.WARNING,
                    field="seller_tax_id",
                    message=(
                        f"seller_tax_id format neocekivan: '{seller_tax_id}'"
                    ),
                    code="D002",
                )
            )

        # incoterm: mora biti u listi poznatih (EXW, FOB, CIF, ...)
        incoterm = str(resolved.get("incoterm", "")).strip().upper()
        if incoterm and incoterm not in _VALID_INCOTERMS:
            issues.append(
                Issue(
                    severity=IssueSeverity.WARNING,
                    field="incoterm",
                    message=(
                        f"incoterm '{incoterm}' nije u standardnoj listi "
                        f"{_VALID_INCOTERMS}"
                    ),
                    code="D003",
                )
            )

        # origin_statement ne smije biti prazan (pravno znacajno)
        origin = str(resolved.get("origin_statement", "")).strip()
        if not origin:
            issues.append(
                Issue(
                    severity=IssueSeverity.ERROR,
                    field="origin_statement",
                    message="origin_statement prazan (pravno znacajno)",
                    code="D004",
                )
            )

        return tuple(issues)

    def _resolve_first_candidate(self, draft: ExtractionDraft) -> dict[str, object]:
        out: dict[str, object] = {}
        for field, candidates in draft.candidates_by_field.items():
            if candidates:
                out[field] = candidates[0].normalized_value
        return out


_VALID_INCOTERMS = frozenset({
    "EXW", "FCA", "CPT", "CIP", "DAP", "DPU", "DDP",
    "FAS", "FOB", "CFR", "CIF",
})


__all__ = ["DomainValidator"]

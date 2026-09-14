# Application: extraction/validators/arithmetic.
# Posjeduje: ArithmeticValidator implementacija Validator.
# Zna za: domain.evidence, domain.extraction.extraction_draft.
# Ne zna za: SQLite, PySide6, Docling, contract, adapters.
"""ArithmeticValidator — matematicka konzistentnost (V3_2 C4 arithmetic).

V3 ARCH-009: Pravno znacajne vrijednosti se ne izmisljaju.
Ovaj validator SAMO FLAGGIRA nekonzistentnost, NE ispravlja vrijednosti.

Provjere:
- subtotal + tax_amount = total (ako su poznati)
- items.sum(kolicina * cijena) ~ total (placeholder, FAZA D)
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from parser_studio.application.extraction.validators.base import (
    Issue,
    IssueSeverity,
)
from parser_studio.domain.extraction.extraction_draft import ExtractionDraft


def _to_decimal(value: object) -> Decimal | None:
    """Parsiraj value u Decimal. Vrati None ako ne moze."""
    try:
        if value is None:
            return None
        text = str(value).strip().replace(",", ".")
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return None


class ArithmeticValidator:
    """Matematicka konzistentnost invoice polja."""

    name: str = "arithmetic"

    # Tolerance za floating-point greske
    _TOLERANCE = Decimal("0.02")

    def validate(self, draft: ExtractionDraft) -> tuple[Issue, ...]:
        issues: list[Issue] = []
        resolved = self._resolve_first_candidate(draft)

        subtotal = _to_decimal(resolved.get("subtotal"))
        tax_amount = _to_decimal(resolved.get("tax_amount"))
        total = _to_decimal(resolved.get("total"))

        # subtotal + tax = total
        if subtotal is not None and tax_amount is not None and total is not None:
            computed = subtotal + tax_amount
            diff = abs(computed - total)
            if diff > self._TOLERANCE:
                issues.append(
                    Issue(
                        severity=IssueSeverity.WARNING,
                        field="total",
                        message=(
                            f"subtotal + tax = {computed}, ali total = {total} "
                            f"(razlika: {diff})"
                        ),
                        code="A001",
                    )
                )

        # items sum (placeholder — draft nema items direktno)
        # Ako draft ima 'lines' sa kandidatima, sumiraj (kolicina * cijena)
        if "lines" in draft.candidates_by_field:
            line_candidates = draft.candidates_by_field.get("lines", ())
            # lines su kandidati sa structured data (NE parsiramo ovdje)
            # Samo flag ako lines prazno
            if not line_candidates:
                issues.append(
                    Issue(
                        severity=IssueSeverity.INFO,
                        field="lines",
                        message="Nema items (lines) za provjeru sume",
                        code="A002",
                    )
                )

        return tuple(issues)

    def _resolve_first_candidate(self, draft: ExtractionDraft) -> dict[str, object]:
        out: dict[str, object] = {}
        for field, candidates in draft.candidates_by_field.items():
            if candidates:
                out[field] = candidates[0].normalized_value
        return out


__all__ = ["ArithmeticValidator"]

# Domain: Candidate.
# Posjeduje: field, raw_value, normalized_value, locator, evidence, producer_id, ai_assisted, issues.
# Ne zna za: SQLite, PySide6, Docling, openpyxl, contract.
"""Candidate — prijedlog vrijednosti od strane extractora ili AI advisor.

Candidate NIJE istina. Predstavlja samo prijedlog sa provenance i eventuelnim
problemima. Resolver bira izmedju kandidata na osnovu dodatnih dokaza.

AI kandidat bez deterministicki provjerljivog izvora/lokacije se ODBACUJE.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .locator import Locator


@dataclass(frozen=True, slots=True)
class Candidate:
    """Prijedlog vrijednosti od strane extractora ili AI advisor. Nije istina."""

    field: str
    raw_value: Any
    normalized_value: Any
    locator: Locator
    evidence: str
    producer_id: str
    ai_assisted: bool = False
    issues: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.field:
            raise ValueError("field ne može biti prazan string")
        if not isinstance(self.locator, Locator):
            raise TypeError(
                f"locator mora biti Locator instanca, dobijeno {type(self.locator).__name__}"
            )
        if not self.producer_id:
            raise ValueError("producer_id ne može biti prazan string")

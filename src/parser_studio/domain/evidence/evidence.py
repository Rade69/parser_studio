# Domain: Evidence.
# Posjeduje: raw_value, raw_text, locator, element_type, source_id.
# Ne zna za: SQLite, PySide6, Docling, openpyxl, contract.
"""Evidence — nesto sto je stvarno vidjeno u dokumentu.

Immutable value object. Sva polja su frozen=True, slots=True.
Evidence predstavlja jedan element iz dokumenta: Excel cell, PDF rijec,
PDF table cell, Docling paragraph, text span, itd.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .locator import Locator


@dataclass(frozen=True, slots=True)
class Evidence:
    """Nesto sto je stvarno vidjeno u dokumentu."""

    raw_value: Any
    raw_text: str
    locator: Locator
    element_type: str
    source_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.locator, Locator):
            raise TypeError(
                f"locator mora biti Locator instanca, dobijeno {type(self.locator).__name__}"
            )
        if not self.element_type:
            raise ValueError("element_type ne može biti prazan string")

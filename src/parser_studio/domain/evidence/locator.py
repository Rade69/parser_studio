# Domain: Locator.
# Posjeduje: source_path, kind, page, bbox, sheet, row, col, char_span.
# Ne zna za: SQLite, PySide6, Docling, openpyxl, contract.
"""Locator — gdje u izvornom dokumentu se nalazi vrijednost.

Immutable value object. Sva polja su frozen=True, slots=True.
Koordinate (bbox) se u canonical sloju normalizuju na [0,1], origin top-left,
osim ako adapter ima razlog da privremeno čuva native koordinate.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class Locator:
    """Gdje u izvornom dokumentu se nalazi vrijednost."""

    source_path: str
    kind: Literal["pdf", "excel", "text"]

    page: int | None = None
    bbox: tuple[float, float, float, float] | None = None

    sheet: str | None = None
    row: int | None = None
    col: int | None = None

    char_span: tuple[int, int] | None = None

    def __post_init__(self) -> None:
        valid_kinds = ("pdf", "excel", "text")
        if self.kind not in valid_kinds:
            raise ValueError(
                f"kind mora biti jedan od {valid_kinds}, dobijeno {self.kind!r}"
            )
        if self.bbox is not None and len(self.bbox) != 4:
            raise ValueError(
                f"bbox mora imati 4 vrijednosti (x0, y0, x1, y1), dobijeno {len(self.bbox)}"
            )
        if self.page is not None and self.page < 0:
            raise ValueError(f"page ne može biti negativan, dobijeno {self.page}")
        if self.row is not None and self.row < 0:
            raise ValueError(f"row ne može biti negativan, dobijeno {self.row}")
        if self.col is not None and self.col < 0:
            raise ValueError(f"col ne može biti negativan, dobijeno {self.col}")
        if self.char_span is not None and (
            len(self.char_span) != 2
            or self.char_span[0] < 0
            or self.char_span[1] <= self.char_span[0]
        ):
            raise ValueError(
                f"char_span mora biti (start, end) sa start >= 0 i end >= start, "
                f"dobijeno {self.char_span!r}"
            )

"""
Document protokol — jedinstven pristup izvornom dokumentu (PDF/Excel/XML).

Zašto postoji: engine-i (core/engines/) ne smiju znati da li čitaju .xlsx ili
.xls, niti smiju sami otvarati fajl. Document je jedina tačka koja dodiruje disk,
i on kešira rezultat — bez toga bi live preview otvarao isti PDF desetak puta na
svaku izmjenu profila.

Pravilo: NULA PySide6 importa u ovom paketu (headless testabilnost).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class Cell:
    """Jedna ćelija sa provenancom — odakle je vrijednost došla.

    Provenanca je ono što omogućava da preview pokaže korisniku "ova vrijednost
    dolazi odavde", i što kasnije omogućava vizuelnu korekciju. Bez nje bi alat
    bio crna kutija isto kao ručno pisan parser.
    """

    value: Any
    row: int
    col: int
    # PDF-specifično (None za Excel); Excel-specifično: sheet
    page: int | None = None
    x0: float | None = None
    x1: float | None = None
    top: float | None = None
    sheet: str | None = None

    @property
    def text(self) -> str:
        return "" if self.value is None else str(self.value).strip()


@dataclass
class ExtractionTable:
    """Sirov rezultat engine-a: redovi ćelija + dijagnostika.

    KLJUČNA ODLUKA (plan, sekcija "Engine vraća sirove ćelije"): engine NE vraća
    InvoiceLine. Mapiranje na model je zaseban sloj (core/mapping/), da bi se
    mapiranje i transformacije mogli mijenjati bez ponovnog parsiranja dokumenta.
    """

    # Redovi: svaki red je dict {ime_kolone: Cell}
    rows: list[dict[str, Cell]] = field(default_factory=list)
    # Koje kolone je engine prepoznao
    columns: list[str] = field(default_factory=list)
    # Redovi koje je engine odbacio + razlog (za preview: "zašto ovaj red nije stavka")
    rejected: list[tuple[int, str]] = field(default_factory=list)
    # Slobodna dijagnostika engine-a (header red, score, itd.)
    diagnostics: dict[str, Any] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.rows)


@runtime_checkable
class Document(Protocol):
    """Zajednički interfejs nad izvornim fajlom."""

    @property
    def path(self) -> Path: ...

    def full_text(self) -> str:
        """Cijeli tekst dokumenta (za detekciju formata i regex nad headerom)."""
        ...

    def close(self) -> None:
        """Oslobodi resurse (fajl handle, keš)."""
        ...

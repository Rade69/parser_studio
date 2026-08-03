"""
Engine protokol.

Engine ima dvije uloge:
  - `probe()`  — "koliko sam siguran da mogu pročitati ovaj dokument?" Koristi se
                 u wizardu (korak 3) da alat sam predloži engine, umjesto da
                 korisnik bira iz liste pojmova koje ne razumije.
  - `extract()` — izvuci ExtractionTable prema konfiguraciji iz profila.

KLJUČNO: engine ne vraća InvoiceLine. Vraća sirove ćelije + provenancu; mapiranje
je zaseban sloj (core/mapping/). Razlog: mapiranje i transformacije se mijenjaju
mnogo češće nego parsiranje, i ne smiju tražiti ponovno čitanje dokumenta.

Pravilo: NULA PySide6 importa.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from core.documents.base import ExtractionTable


@dataclass
class ProbeResult:
    """Koliko engine "vjeruje" da može pročitati dokument."""

    score: float  # 0.0-1.0
    reason: str  # objašnjenje na srpskom, prikazuje se korisniku
    # Prijedlog konfiguracije koji je engine sam izveo (upisuje se u profil)
    suggested_config: dict[str, Any] = field(default_factory=dict)
    # Koliko redova bi izvukao sa tim prijedlogom
    estimated_rows: int = 0

    def __bool__(self) -> bool:
        return self.score > 0


class Engine(Protocol):
    """Interfejs koji svaki engine implementira."""

    name: str

    def probe(self, document: Any) -> ProbeResult:
        """Procijeni da li i koliko dobro ovaj engine može pročitati dokument."""
        ...

    def extract(self, document: Any, config: dict[str, Any]) -> ExtractionTable:
        """Izvuci tabelu prema konfiguraciji iz profila."""
        ...

"""
VENDOROVANA kopija ugovora iz deklarant_pro/importers/import_result.py.

NE UREĐIVATI RUČNO — kopija, ne original. Izvor: deklarant_pro/importers/import_result.py

`validate()` je kopiran DOSLOVNO jer se koristi kao mjerilo verifikacije (nivo 3):
poruke koje alat prikazuje korisniku moraju biti identične onima koje će vidjeti
u deklarant_pro.

Provjera odstupanja: `contract/drift_check.py`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from contract.draft_types import InvoiceLine, Party


@dataclass
class ImportResult:
    """Rezultat importa fakture sa dodatnim metadata podacima."""

    items: List[InvoiceLine] = field(default_factory=list)
    bruto_kg: float = 0.0
    neto_kg: float = 0.0
    invoice_name: str = ""
    currency: str = "EUR"
    is_combined: bool = False
    import_type: str = "invoice"
    has_origin_statement: bool = False
    is_authorized_exporter: bool = False
    origin_statements: Optional[List] = None
    warnings: List[str] = field(default_factory=list)
    exporter: Optional[Party] = None
    importer: Optional[Party] = None
    consumed_paths: List[str] = field(default_factory=list)
    incoterm_code: str = ""

    def __post_init__(self):
        if not self.is_authorized_exporter and self.origin_statements:
            self.is_authorized_exporter = any(
                getattr(s, "tip_izjave", "") == "ovlaseni_izvoznik"
                for s in self.origin_statements
            )

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index: int | slice) -> InvoiceLine | List[InvoiceLine]:
        return self.items[index]

    def validate(self, allow_empty: bool = False) -> tuple[bool, list[str], list[str]]:
        """Parser-level validacija — provjera da su podaci fizički ispravni."""
        errors: list[str] = []
        warnings: list[str] = []

        _KNOWN_CURRENCIES = {
            "EUR", "USD", "BAM", "CHF", "GBP", "SEK", "NOK", "DKK", "HRK", "RSD",
        }

        if not self.items and not allow_empty:
            errors.append("Parser nije pronašao nijednu stavku (0 stavki)")

        if self.currency and self.currency.upper() not in _KNOWN_CURRENCIES:
            warnings.append(f"Nepoznata valuta: '{self.currency}'")

        if self.bruto_kg < 0:
            errors.append(f"Negativna bruto težina: {self.bruto_kg} kg")

        if self.neto_kg < 0:
            errors.append(f"Negativna neto težina: {self.neto_kg} kg")

        if self.bruto_kg > 0 and self.neto_kg > 0 and self.neto_kg > self.bruto_kg:
            errors.append(
                f"Neto ({self.neto_kg} kg) > Bruto ({self.bruto_kg} kg) — fizički nemoguće"
            )

        if self.items and self.bruto_kg > 0 and self.neto_kg <= 0:
            warnings.append(
                f"Bruto težina pronađena ({self.bruto_kg} kg), ali Neto nije — provjerite fakturu"
            )
        elif self.items and self.neto_kg > 0 and self.bruto_kg <= 0:
            warnings.append(
                f"Neto težina pronađena ({self.neto_kg} kg), ali Bruto nije — provjerite fakturu"
            )

        for i, item in enumerate(self.items, 1):
            naziv = (item.naziv_robe or "").strip()
            if not naziv:
                warnings.append(f"Stavka {i}: prazan naziv robe")

            if item.kolicina <= 0:
                warnings.append(f"Stavka {i} ({naziv[:30] or '?'}): količina = {item.kolicina}")

            if item.cijena_jed < 0:
                errors.append(
                    f"Stavka {i} ({naziv[:30] or '?'}): negativna cijena {item.cijena_jed}"
                )

            if item.iznos < 0:
                errors.append(f"Stavka {i} ({naziv[:30] or '?'}): negativan iznos {item.iznos}")

            if item.bruto_kg > 0 and item.neto_kg > 0 and item.neto_kg > item.bruto_kg:
                warnings.append(
                    f"Stavka {i} ({naziv[:30] or '?'}): neto > bruto "
                    f"({item.neto_kg} > {item.bruto_kg})"
                )

        existing = set(self.warnings)
        for w in warnings:
            if w not in existing:
                self.warnings.append(w)
                existing.add(w)

        ok = len(errors) == 0
        return ok, errors, warnings

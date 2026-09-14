# Domain: invoice/canonical_invoice.
# Posjeduje: CanonicalInvoice, InvoiceLine, InvoiceField, InvoiceStatus.
# Ne zna za: SQLite, PySide6, Docling, openpyxl/xlrd, contract, adapters, presentation.
"""CanonicalInvoice — vendor-agnostic invoice domain model.

Sadrzi svih 20 ciljnih poslovnih polja iz V3 sekcija 4.1 i 4.2,
plus status (FOUND/NOT_PRESENT/AMBIGUOUS/FAILED) i provenance (Evidence).

Klase:

- `InvoiceStatus` — status vrijednosti (V3 sekcija 5).
- `InvoiceField` — value + status + provenance omotac za jedno polje.
- `InvoiceLine` — jedan red iz tablice stavki (10 InvoiceField-ova + line_no).
- `CanonicalInvoice` — kompletna faktura (9 invoice-level polja + items).

Napomena o vendor agnosticizmu:

CanonicalInvoice NE sadrzi vendor-specific imena polja (nema
"Faktura1Invoice", "MedicopharmLine", ...). Nazivi polja su canonical:
invoice_number, invoice_date, currency, exporter, importer, incoterm_code,
total_bruto_kg, total_neto_kg, origin_statement (invoice-level) i
product_code, naziv_robe, tarifni_broj, jm, kolicina, cijena_jed, iznos,
zemlja_porijekla, neto_kg, bruto_kg (item-level).

Isti CanonicalInvoice moze predstavljati Faktura-1, Faktura-2, Medicopharm,
Sumaprom — razlika je SAMO u sadrzaju polja i provenance.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any

from parser_studio.domain.evidence import Evidence

# Poznate valute prema contract/import_result.py.
# Ovo je read-only konstanta; NE importuje contract modul.
_KNOWN_CURRENCIES: frozenset[str] = frozenset({
    "EUR", "USD", "BAM", "CHF", "GBP", "SEK", "NOK", "DKK", "HRK", "RSD",
})


class InvoiceStatus(str, Enum):
    """Status jednog canonical polja (V3 sekcija 5).

    FOUND:           vrijednost postoji i ima dokaz/provenance.
    NOT_PRESENT:     provjeren je scope i podatak stvarno ne postoji.
    AMBIGUOUS:       dva ili vise kandidata bez dovoljno dokaza.
    FAILED:          podatak vjerovatno postoji, ali extraction/reading nije uspio.
    """

    FOUND = "FOUND"
    NOT_PRESENT = "NOT_PRESENT"
    AMBIGUOUS = "AMBIGUOUS"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class InvoiceField:
    """Omotac: value + status + provenance za jedno canonical polje.

    Vendor-agnostic. value moze biti bilo koji od dozvoljenih tipova
    (str | None, date | None, Decimal | None) ovisno o polju.

    Status je obavezan; provenance (Evidence) je opcionalan.
    """

    value: Any  # str | None | date | None | Decimal | None — zavisno od polja
    status: InvoiceStatus
    provenance: Evidence | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, InvoiceStatus):
            raise TypeError(
                f"status mora biti InvoiceStatus instanca, "
                f"dobijeno {type(self.status).__name__}"
            )
        if self.provenance is not None and not isinstance(self.provenance, Evidence):
            raise TypeError(
                f"provenance mora biti Evidence instanca ili None, "
                f"dobijeno {type(self.provenance).__name__}"
            )


@dataclass(frozen=True, slots=True)
class InvoiceLine:
    """Jedan red tablice stavki fakture.

    11 item-level polja iz V3 sekcija 4.2:
    - line_no (int, pozicija, nije InvoiceField — ordinal)
    - product_code, naziv_robe, tarifni_broj, jm (str)
    - kolicina, cijena_jed, iznos, neto_kg, bruto_kg (Decimal)
    """

    line_no: int
    product_code: InvoiceField
    naziv_robe: InvoiceField
    tarifni_broj: InvoiceField
    jm: InvoiceField
    kolicina: InvoiceField
    cijena_jed: InvoiceField
    iznos: InvoiceField
    zemlja_porijekla: InvoiceField
    neto_kg: InvoiceField
    bruto_kg: InvoiceField

    def __post_init__(self) -> None:
        if not isinstance(self.line_no, int):
            raise TypeError(
                f"line_no mora biti int, dobijeno {type(self.line_no).__name__}"
            )
        if self.line_no < 0:
            raise ValueError(f"line_no ne može biti negativan, dobijeno {self.line_no}")
        # Sva polja moraju biti InvoiceField instance
        field_names = (
            "product_code", "naziv_robe", "tarifni_broj", "jm", "kolicina",
            "cijena_jed", "iznos", "zemlja_porijekla", "neto_kg", "bruto_kg",
        )
        for fname in field_names:
            fval = getattr(self, fname)
            if not isinstance(fval, InvoiceField):
                raise TypeError(
                    f"{fname} mora biti InvoiceField instanca, "
                    f"dobijeno {type(fval).__name__}"
                )


@dataclass(frozen=True, slots=True)
class CanonicalInvoice:
    """Kompletna faktura — vendor-agnostic.

    9 invoice-level polja iz V3 sekcija 4.1 + items (tuple InvoiceLine-ova).

    Polja:
    - invoice_number (str), invoice_date (date), currency (str)
    - exporter (str), importer (str), incoterm_code (str)
    - total_bruto_kg (Decimal), total_neto_kg (Decimal)
    - origin_statement (str)

    `source_path` i `document_id` su opcioni metapodaci za traceability.
    """

    invoice_number: InvoiceField
    invoice_date: InvoiceField
    currency: InvoiceField
    exporter: InvoiceField
    importer: InvoiceField
    incoterm_code: InvoiceField
    total_bruto_kg: InvoiceField
    total_neto_kg: InvoiceField
    origin_statement: InvoiceField

    items: tuple[InvoiceLine, ...] = field(default_factory=tuple)

    source_path: str | None = None
    document_id: str | None = None

    def __post_init__(self) -> None:
        field_names = (
            "invoice_number", "invoice_date", "currency", "exporter", "importer",
            "incoterm_code", "total_bruto_kg", "total_neto_kg", "origin_statement",
        )
        for fname in field_names:
            fval = getattr(self, fname)
            if not isinstance(fval, InvoiceField):
                raise TypeError(
                    f"{fname} mora biti InvoiceField instanca, "
                    f"dobijeno {type(fval).__name__}"
                )
        # items mora biti tuple InvoiceLine-ova
        if not isinstance(self.items, tuple):
            raise TypeError(
                f"items mora biti tuple, dobijeno {type(self.items).__name__}"
            )
        for i, item in enumerate(self.items):
            if not isinstance(item, InvoiceLine):
                raise TypeError(
                    f"items[{i}] mora biti InvoiceLine instanca, "
                    f"dobijeno {type(item).__name__}"
                )


def _str_field(value: str | None, status: InvoiceStatus) -> InvoiceField:
    """Helper: InvoiceField za string vrijednost (invoice_number, currency, ...)."""
    if value is not None and not isinstance(value, str):
        raise TypeError(f"ocekivano str | None, dobijeno {type(value).__name__}")
    return InvoiceField(value=value, status=status)


def _decimal_field(value: Decimal | None, status: InvoiceStatus) -> InvoiceField:
    """Helper: InvoiceField za Decimal vrijednost (monetarni iznosi, mase)."""
    if value is not None and not isinstance(value, Decimal):
        raise TypeError(f"ocekivano Decimal | None, dobijeno {type(value).__name__}")
    if value is not None and value < 0:
        raise ValueError(f"negativna vrijednost nije dozvoljena, dobijeno {value}")
    return InvoiceField(value=value, status=status)


def _date_field(value: date | None, status: InvoiceStatus) -> InvoiceField:
    """Helper: InvoiceField za date vrijednost (invoice_date)."""
    if value is not None and not isinstance(value, date):
        raise TypeError(f"ocekivano date | None, dobijeno {type(value).__name__}")
    return InvoiceField(value=value, status=status)


def canonical_field_count() -> int:
    """Vrati broj canonical poslovnih polja (9 invoice + 11 item = 20)."""
    return 20


def canonical_invoice_field_names() -> tuple[str, ...]:
    """Vrati imena 9 invoice-level canonical polja."""
    return (
        "invoice_number",
        "invoice_date",
        "currency",
        "exporter",
        "importer",
        "incoterm_code",
        "total_bruto_kg",
        "total_neto_kg",
        "origin_statement",
    )


def canonical_item_field_names() -> tuple[str, ...]:
    """Vrati imena 11 item-level canonical polja (ukljucujuci line_no)."""
    return (
        "line_no",
        "product_code",
        "naziv_robe",
        "tarifni_broj",
        "jm",
        "kolicina",
        "cijena_jed",
        "iznos",
        "zemlja_porijekla",
        "neto_kg",
        "bruto_kg",
    )


def known_currencies() -> frozenset[str]:
    """Vrati set poznatih valuta (read-only konstanta)."""
    return _KNOWN_CURRENCIES
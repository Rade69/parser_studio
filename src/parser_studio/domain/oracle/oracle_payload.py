# Domain: OraclePayload.
# Posjeduje: vendor-agnostička reprezentacija oracle import rezultata.
# Ne zna za: contract (ImportResult), adaptere, prezentaciju, SQLite.
"""OraclePayload — vendor-agnostički payload od oracle import-a.

Adapteri (npr. DeclarantProOracle) prevode vendor ImportResult
(contract/) u OraclePayload. Application sloj (OracleCandidateProducer)
radi iskljucivo sa OraclePayload, NE sa vendor tipovima.

Ova granica postuje V3 DEP pravilo: application NE importuje contract.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class OracleItem:
    """Jedan item iz oracle outputa (vendor-agnostički).

    Polja odgovaraju CanonicalInvoice.lines[i] ali u vendor-neutralnom
    formatu (engleski nazivi, standardni tipovi).
    """

    line_no: int
    description: str = ""
    quantity: float = 0.0
    unit_price: float = 0.0
    line_amount: float = 0.0
    hs_code: str = ""
    origin_country: str = ""
    uom: str = ""
    gross_weight_kg: float = 0.0
    net_weight_kg: float = 0.0
    product_code: str = ""

    def __post_init__(self) -> None:
        if self.line_no < 0:
            raise ValueError(f"line_no ne može biti negativan: {self.line_no}")


@dataclass(frozen=True, slots=True)
class OraclePayload:
    """Vendor-agnostički oracle import payload.

    Polja odgovaraju Deklarant Pro ImportResult ali prevedena na engleski
    (CanonicalInvoice terminologija). Default vrijednosti za prazne
    ImportResult slučajeve.
    """

    # Invoice-level (9 polja, V3_2)
    invoice_number: str = ""
    supplier_name: str = ""
    supplier_address: str = ""
    supplier_country: str = ""
    supplier_vat: str = ""
    invoice_date: str = ""
    due_date: str = ""
    invoice_total: float = 0.0
    currency: str = ""

    # Meta
    bruto_kg: float = 0.0
    neto_kg: float = 0.0
    incoterm: str = ""
    is_combined: bool = False
    has_origin_statement: bool = False

    # Items
    items: tuple[OracleItem, ...] = ()

    # Oracle metadata
    source_strategy: str = ""
    source_priority: int = 0

    def __post_init__(self) -> None:
        if self.invoice_total < 0:
            raise ValueError(
                f"invoice_total ne može biti negativan: {self.invoice_total}"
            )

    def is_empty(self) -> bool:
        """True ako payload nema nikakvih podataka."""
        return (
            not self.invoice_number
            and not self.items
            and self.invoice_total == 0.0
        )

    def get_field(self, field_name: str) -> Any:
        """Dohvati vrijednost za ime polja (canonical field name).

        Koristi se od strane OracleCandidateProducer za mapiranje
        oracle vrijednosti na traženi target field.

        Returns:
            Vrijednost polja ili None ako polje ne postoji.
        """
        if not hasattr(self, field_name):
            return None
        return getattr(self, field_name)

    def get_item_field(self, line_no: int, field_name: str) -> Any:
        """Dohvati vrijednost item polja za dati line_no.

        Returns:
            Vrijednost polja ili None ako item/field ne postoji.
        """
        for item in self.items:
            if item.line_no == line_no:
                if not hasattr(item, field_name):
                    return None
                return getattr(item, field_name)
        return None
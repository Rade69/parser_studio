# Domain: oracle_mapping.
# Posjeduje: statička mapa oracle payload polja na canonical field imena.
# Ne zna za: contract (ImportResult), adaptere, prezentaciju, SQLite.
"""Oracle field mapping.

Statička mapa koja povezuje OraclePayload polja sa CanonicalInvoice
poljima (20 vendor-agnostičkih polja).

Koristi se u:
- OracleCandidateProducer (D2) — mapiranje oracle vrijednosti na Candidate
- ConfirmOracle (D3) — confirm/reject oracle vrijednosti

Konvencija:
- Ključevi: canonical field names (kao u CanonicalInvoice / InvoiceField)
- Vrijednosti: OraclePayload field names (sa prefiksom 'item_' za stavke)

Item polja koriste format 'item.<line_no>.<field>' za specifičnu stavki,
ili 'item.<field>' za mapiranje na sve stavke (producer prim od).
"""
from __future__ import annotations

# Invoice-level mapping: OraclePayload polje → canonical polje
# (canonical polje = key, OraclePayload polje = value)
INVOICE_LEVEL_MAP: dict[str, str] = {
    # canonical field name : oracle_payload attribute
    "invoice_number": "invoice_number",
    "supplier_name": "supplier_name",
    "supplier_address": "supplier_address",
    "supplier_country": "supplier_country",
    "supplier_vat": "supplier_vat",
    "invoice_date": "invoice_date",
    "due_date": "due_date",
    "invoice_total": "invoice_total",
    "currency": "currency",
    "gross_weight_kg": "bruto_kg",  # bruto_kg je deklarant_pro naziv
    "net_weight_kg": "neto_kg",
    "incoterm": "incoterm",
}


# Item-level mapping (11 polja po stavki)
ITEM_LEVEL_MAP: dict[str, str] = {
    # canonical field name : OracleItem attribute
    "description": "description",
    "quantity": "quantity",
    "unit_price": "unit_price",
    "line_amount": "line_amount",
    "hs_code": "hs_code",
    "origin_country": "origin_country",
    "uom": "uom",
    "item_gross_weight_kg": "gross_weight_kg",
    "item_net_weight_kg": "net_weight_kg",
    "product_code": "product_code",
}


def is_item_field(field_name: str) -> bool:
    """Da li je dati field item-level (za stavku) ili invoice-level."""
    return field_name in ITEM_LEVEL_MAP


def is_invoice_field(field_name: str) -> bool:
    """Da li je dati field invoice-level (header) polje."""
    return field_name in INVOICE_LEVEL_MAP


def get_oracle_attr_for(field_name: str) -> str | None:
    """Vraća OraclePayload/OracleItem attribute name za dati canonical field.

    Returns:
        Attribute name na OraclePayload/OracleItem, ili None ako field
        nije podržan.
    """
    if field_name in INVOICE_LEVEL_MAP:
        return INVOICE_LEVEL_MAP[field_name]
    if field_name in ITEM_LEVEL_MAP:
        return ITEM_LEVEL_MAP[field_name]
    return None


def all_supported_fields() -> tuple[str, ...]:
    """Lista svih podržanih canonical field imena."""
    return tuple(INVOICE_LEVEL_MAP.keys()) + tuple(ITEM_LEVEL_MAP.keys())


def is_known_field(field_name: str) -> bool:
    """Da li je field_name podržan u oracle mapi (invoice ili item)."""
    return is_invoice_field(field_name) or is_item_field(field_name)
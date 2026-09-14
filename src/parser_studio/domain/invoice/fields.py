# Domain: invoice/fields.
# Posjeduje: COLUMN_ALIASES konstanta (canonical -> [aliases]).
# Ne zna za: SQLite, PySide6, Docling, openpyxl/xlrd, contract.
"""COLUMN_ALIASES — mapiranje canonical polja na listu aliasa zaglavlja.

Struktura: dict[canonical_name, list[alias_string]] (canonical -> [aliases]).
Sadrzi 30+ aliasa preuzetih iz legacy core/engines/excel_headers.py.

Koristi se u identify_columns() za mapiranje Excel headera na Invoice polja.
"""
from __future__ import annotations

from typing import Final

COLUMN_ALIASES: Final[dict[str, list[str]]] = {
    "naziv_robe": [
        "naziv", "naziv robe", "opis", "opis robe", "description", "item",
        "item description", "artikal", "roba", "proizvod", "naziv dobra",
        "naziv dobra / usluge",
    ],
    "product_code": [
        "sifra", "sifra artikla", "kod", "code", "item code", "product code",
        "art. br", "artikl br", "kataloski broj",
    ],
    "tarifni_broj": [
        "tarifni broj", "tarifni br", "tarifni", "tariff", "tariff code",
        "hs", "hs code", "tarifa", "tarifna oznaka", "cn", "cn code",
        "commodity code", "gtip",
    ],
    "kolicina": [
        "kolicina", "kol", "kol.", "qty", "quantity", "kom", "miktar",
    ],
    "jm": [
        "jm", "j.m.", "jed. mjere", "jedinica mjere", "u.m.", "um", "unit",
        "unit of measure", "mjera", "measure",
    ],
    "cijena_jed": [
        "cijena", "cena", "cijena jed", "jedinicna cijena", "price",
        "unit price", "cij", "cjena", "neto cena",
    ],
    "iznos": [
        "iznos", "amount", "total", "total amount", "vrijednost", "vrednost",
        "value", "ukupno",
    ],
    "bruto_kg": [
        "bruto", "brutto", "bruto kg", "bruto masa", "bruto tezina",
        "gross", "gross weight", "gross kg", "bruto (kg)",
    ],
    "neto_kg": [
        "neto", "neto kg", "neto masa", "neto tezina", "net", "net weight",
        "neto (kg)", "neto (kgr)",
    ],
    "zemlja_porijekla": [
        "zemlja", "zemlja porijekla", "zemlja porekla", "porijeklo", "poreklo",
        "country", "origin", "country of origin", "orig",
    ],
    "povlastica": [
        "povlastica", "preferencijal", "preference", "preferential", "pref",
    ],
    "valuta": [
        "valuta", "currency", "curr", "val", "doviz",
    ],
    "invoice_number": [
        "faktura", "broj fakture", "invoice", "invoice no", "invoice number",
        "racun",
    ],
}


# Kolone koje su same po sebi dovoljne da se red smatra "stavkom".
_ESSENTIAL_FIELDS: Final[tuple[str, ...]] = ("naziv_robe", "product_code")


# Redovi zbira/footera koji IMAJU tekst u koloni naziva, ali NISU stavke.
_FOOTER_PREFIXES: Final[tuple[str, ...]] = (
    "ukupno", "total", "sum", "suma", "svega", "pdv", "vat", "rabat", "popust",
    "osnovica", "za uplatu", "iznos bez", "iznos sa", "grand total", "subtotal",
    "napomena", "note", "carry over", "prenos",
)

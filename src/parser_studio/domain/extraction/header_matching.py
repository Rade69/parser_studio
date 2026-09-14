# Domain: extraction/header_matching.
# Posjeduje: normalize_header, match_score, identify_columns.
# Ne zna za: SQLite, PySide6, Docling, openpyxl/xlrd, contract.
"""Header matching — mapiranje Excel headera na canonical Invoice polja.

Tri funkcije:
- normalize_header: NFKC + strip dijakritika + lowercase + collapse whitespace
- match_score: binaran score (exact match ili kao zasebna rijec)
- identify_columns: greedy mapiranje header -> canonical polje
"""
from __future__ import annotations

import re
import unicodedata
from typing import Iterable

from parser_studio.domain.invoice.fields import COLUMN_ALIASES


# Kratki aliasi (≤3 znaka) smiju pogoditi samo exact ili kao zasebna rijec.
_SHORT_ALIAS_LEN = 3


def normalize_header(name: object) -> str:
    """NFKC + strip dijakritika + lowercase + collapsed whitespace.

    "Kolicina" → "kolicina"
    "Kolicina robe" → "kolicina robe"
    "U.M." → "um"  (tacke se uklanjaju)

    Algoritam:
    1. NFKC normalizacija (kompatibilnost unicode formi)
    2. đ/Đ -> d (rucno; nema NFD dekompoziciju)
    3. NFD dekompozicija + strip kategorije Mn (kombinirani dijakritici)
    4. lowercase
    5. collapse whitespace (vise razmaka u jedan, trim)

    Primjenjuje se SAMO na header imena, nikad na podatke
    (gdje bi '1.5' postalo '15' — problem za numericke vrijednosti).
    """
    text = "" if name is None else str(name).strip()
    if not text:
        return ""
    nfkc = unicodedata.normalize("NFKC", text)
    text_d = nfkc.replace("đ", "d").replace("Đ", "d")
    text_clean = text_d.replace(".", "")
    decomposed = unicodedata.normalize("NFD", text_clean)
    stripped = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    return " ".join(stripped.lower().split())


def match_score(header: str, alias: str) -> float:
    """Binarni score: 1.0 za match, 0.0 za ne-match.

    Pravila (BEZ FUZZY po V3 zabrani):
    - exact match (cijeli header == cijeli alias) -> 1.0
    - kratki alias (≤3 znaka: "kol", "jm", "um", "val", "hs", "cn") smije
      pogoditi samo kao zasebna rijec ("neto kol robe") -> 1.0
    - inace (dovoljno dug alias) substring ili word match -> 1.0
    - u suprotnom -> 0.0

    Za razliku od legacy (koji ima vise nivoa: 100/95/90/80/fuzzy),
    V3 zahtijeva binarni score zbog AI grounding pravila.
    """
    if not header or not alias:
        return 0.0

    h = normalize_header(header)
    a = normalize_header(alias)

    if not h or not a:
        return 0.0

    if h == a:
        return 1.0

    if len(a) <= _SHORT_ALIAS_LEN:
        # Kratak alias: samo kao zasebna rijec
        return 1.0 if f" {a} " in f" {h} " else 0.0

    # Duzak alias: pocetak rijeci ili substring
    if h.startswith(a):
        return 1.0
    if f" {a} " in f" {h} ":
        return 1.0
    if a in h:
        return 1.0

    return 0.0


def identify_columns(
    header_cells: Iterable[str],
    aliases: dict[str, list[str]] | None = None,
) -> dict[str, int]:
    """Mapiraj {ime_polja: indeks_kolone} iz reda zaglavlja.

    Algoritam (greedy):
    1. Za svaki par (field, alias) i svaki header, izracunaj match_score
    2. Sortiraj kandidate po score-u (silazno)
    3. Prolazi kroz sortirane kandidate i dodijeli prvi free match
       (svaki field dobija najvise jednu kolonu; svaka kolona
       najvise jedan field)

    Vraca dict: canonical_name -> column_index (0-based).
    """
    table = aliases if aliases is not None else COLUMN_ALIASES
    normalized_headers = [normalize_header(h) for h in header_cells]

    # Svi kandidati (score, polje, indeks_kolone)
    candidates: list[tuple[float, str, int]] = []
    for field_name, field_aliases in table.items():
        for col_idx, header in enumerate(normalized_headers):
            if not header:
                continue
            best = max(
                (match_score(header, alias) for alias in field_aliases),
                default=0.0,
            )
            if best > 0.0:
                candidates.append((best, field_name, col_idx))

    candidates.sort(key=lambda c: (-c[0], -len(c[1])))

    mapping: dict[str, int] = {}
    used_cols: set[int] = set()
    for _score, field_name, col_idx in candidates:
        if field_name in mapping or col_idx in used_cols:
            continue
        mapping[field_name] = col_idx
        used_cols.add(col_idx)
    return mapping


def is_footer_text(text: str) -> bool:
    """Da li tekst pocinje nekim od poznatih footer pojmova.

    Poredi se po GRANICI RIJECI (\\b), ne golim startswith — bez toga bi
    "TOTALIZATOR ZA KOSILICU" (stvarna roba) bio odbacen jer pocinje sa "total".
    """
    norm = normalize_header(text)
    if not norm:
        return False
    return any(re.match(rf"^{re.escape(p)}\b", norm) for p in __import__(
        "parser_studio.domain.invoice.fields",
        fromlist=["_FOOTER_PREFIXES"],
    )._FOOTER_PREFIXES)

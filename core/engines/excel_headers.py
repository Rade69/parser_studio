"""
excel_headers engine — mapiranje kolona po nazivu zaglavlja.

Port `ExcelImporter.COLUMN_MAP` logike iz deklarant_pro
(importers/excel_importer.py:55-85, 303-407), sa tri popravke u odnosu na original:

1. **Normalizacija dijakritika** — original poredi sirove nazive, pa "količina" i
   "kolicina" nisu isto. Uzeto iz `master_frigo_importer._normalize_header_name`.
2. **Rangirano poklapanje umjesto golog substringa** — original radi
   `if any(alias in cell_value)`, gdje alias "kol" pogađa i "kolona" i "kolicina".
   Ovdje: tačno poklapanje > početak riječi > substring > fuzzy (rapidfuzz),
   i svaka kolona se dodjeljuje samo JEDNOM (najbolji kandidat pobjeđuje).
3. **Provenanca** — svaka ćelija zna svoj red/kolonu/sheet.

Pravilo: NULA PySide6 importa.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

from core.documents.base import Cell, ExtractionTable
from core.engines.base import ProbeResult

# Ciljna polja InvoiceLine → aliasi zaglavlja (bs/hr/sr + en).
# Prošireno u odnosu na original: dodati aliasi viđeni u postojećim vendor parserima
# (Šumaprom "Item Code"/"U.M.", Master Frigo "Šifra"/"Tarifni br", Leburic "Neto (kgr)").
COLUMN_ALIASES: dict[str, list[str]] = {
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

# Aliasi ≤3 znaka ("kol", "jm", "um", "hs", "cn") smiju pogoditi samo tačno
# ili kao zasebna riječ — inače "kol" pogađa "kolona".
_SHORT_ALIAS_LEN = 3

# Fuzzy je opasan na kratkim nazivima: "nesto" vs "neto" daje ratio 89.
_FUZZY_MIN_LEN = 6
_FUZZY_THRESHOLD = 90.0

# Kolone koje su same po sebi dovoljne da se red smatra "stavkom".
_ESSENTIAL = ("naziv_robe", "product_code")

# Redovi zbira/footera koji IMAJU tekst u koloni naziva, ali NISU stavke.
# Isti obrazac kao `_SKIP_ROW_PREFIXES` u deklarant_pro/importers/generic_pdf_importer.py.
_FOOTER_PREFIXES = (
    "ukupno", "total", "sum", "suma", "svega", "pdv", "vat", "rabat", "popust",
    "osnovica", "za uplatu", "iznos bez", "iznos sa", "grand total", "subtotal",
    "napomena", "note", "carry over", "prenos",
)


def normalize_header(name: Any) -> str:
    """Skini dijakritike i tačke, mala slova, kolapsiraj razmake.

    'Količina' → 'kolicina', 'Kol.' → 'kol', 'U.M.' → 'um', 'ŠIFRA' → 'sifra'

    Tačke se uklanjaju da bi 'Kol.' i 'Kol' bili isto — inače bi svaki alias
    morao imati obje varijante. Primjenjuje se SAMO na zaglavlja, nikad na
    podatke (gdje bi '1.5' postalo '15').
    """
    text = "" if name is None else str(name).strip().lower()
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    # đ/Đ nema dekompoziciju u NFD — mora ručno
    stripped = stripped.replace("đ", "d").replace("Đ", "d").replace(".", "")
    return " ".join(stripped.split())


def _match_score(header: str, alias: str) -> float:
    """Koliko dobro naziv zaglavlja odgovara aliasu. 0.0 = nikako.

    Kratki aliasi (≤3 znaka: "kol", "jm", "um", "val", "hs", "cn") smiju pogađati
    SAMO tačno ili kao zasebna riječ. Bez toga bi "kol" kroz startswith pogodio
    "kolona", a "val" pogodio "vrijednost".

    Ulaz mora već biti prošao kroz normalize_header (bez tačaka, bez dijakritika).
    """
    if not header or not alias:
        return 0.0

    if header == alias:
        return 100.0

    if len(alias) <= _SHORT_ALIAS_LEN:
        # Kratak alias smije pogoditi samo kao zasebna riječ ("neto kol robe").
        return 90.0 if f" {alias} " in f" {header} " else 0.0

    if header.startswith(alias):
        return 95.0
    if f" {alias} " in f" {header} ":
        return 90.0
    if alias in header:
        return 80.0

    # Fuzzy samo za dovoljno duge nazive — na kratkim je opasan
    # ("nesto" vs "neto" daje ratio 89, što bi bio lažan pogodak).
    if len(header) < _FUZZY_MIN_LEN or len(alias) < _FUZZY_MIN_LEN:
        return 0.0
    try:
        from rapidfuzz import fuzz

        score = fuzz.ratio(header, alias)
        return float(score) if score >= _FUZZY_THRESHOLD else 0.0
    except ImportError:
        return 0.0


def identify_columns(
    header_cells: list[str], aliases: dict[str, list[str]] | None = None
) -> dict[str, int]:
    """Mapiraj {ime_polja: indeks_kolone} iz reda zaglavlja.

    Svaka kolona se dodjeljuje najviše jednom polju, i svako polje najviše jednoj
    koloni — bira se globalno najbolji par (greedy po score-u). Time se izbjegava
    da "cijena" i "unit price" oba pokupe istu kolonu.
    """
    table = aliases or COLUMN_ALIASES
    normalized = [normalize_header(h) for h in header_cells]

    # Svi kandidati (score, polje, indeks_kolone)
    candidates: list[tuple[float, str, int]] = []
    for field_name, field_aliases in table.items():
        for col_idx, header in enumerate(normalized):
            if not header:
                continue
            best = max((_match_score(header, normalize_header(a)) for a in field_aliases),
                       default=0.0)
            if best > 0:
                candidates.append((best, field_name, col_idx))

    candidates.sort(key=lambda c: -c[0])

    mapping: dict[str, int] = {}
    used_cols: set[int] = set()
    for score, field_name, col_idx in candidates:
        if field_name in mapping or col_idx in used_cols:
            continue
        mapping[field_name] = col_idx
        used_cols.add(col_idx)
    return mapping


def find_header_row(sheet, max_rows: int = 30, min_matches: int = 3) -> tuple[int, dict[str, int]]:
    """Red sa najviše prepoznatih zaglavlja. Vraća (red, mapiranje) ili (-1, {})."""
    best_row, best_map, best_count = -1, {}, 0
    for row in range(min(max_rows, sheet.nrows)):
        cells = [sheet.value(row, c) for c in range(sheet.ncols)]
        if not any(str(c).strip() for c in cells):
            continue
        mapping = identify_columns(cells)
        if len(mapping) > best_count:
            best_row, best_map, best_count = row, mapping, len(mapping)
    if best_count < min_matches:
        return -1, {}
    return best_row, best_map


class ExcelHeadersEngine:
    """Engine koji čita Excel tabelu mapirajući kolone po nazivu zaglavlja."""

    name = "excel_headers"

    def probe(self, document) -> ProbeResult:
        """Procijeni da li dokument ima prepoznatljiv red zaglavlja."""
        try:
            sheets = document.sheets
        except Exception as exc:
            return ProbeResult(0.0, f"Nije moguće otvoriti Excel: {exc}")

        best: tuple[float, dict[str, Any], int, str] | None = None

        for sheet_idx, sheet in enumerate(sheets):
            header_row, mapping = find_header_row(sheet)
            if header_row < 0:
                continue

            data_rows = self._count_data_rows(sheet, header_row, mapping)
            if data_rows == 0:
                continue

            # Score: koliko polja prepoznato (max ~8 je odlično) + ima li ključnih
            field_score = min(len(mapping) / 8.0, 1.0)
            has_essential = any(f in mapping for f in _ESSENTIAL)
            score = field_score * (1.0 if has_essential else 0.4)

            if best is None or score > best[0]:
                config = {
                    "sheet": sheet_idx,
                    "header_row": header_row,
                    "columns": dict(mapping),
                }
                reason = (
                    f"List '{sheet.name}': zaglavlje na redu {header_row + 1}, "
                    f"prepoznato {len(mapping)} kolona ({', '.join(sorted(mapping))}), "
                    f"{data_rows} redova sa podacima"
                )
                best = (score, config, data_rows, reason)

        if best is None:
            return ProbeResult(0.0, "Nije pronađen prepoznatljiv red zaglavlja")

        score, config, rows, reason = best
        return ProbeResult(
            score=score, reason=reason, suggested_config=config, estimated_rows=rows
        )

    @staticmethod
    def _count_data_rows(sheet, header_row: int, mapping: dict[str, int]) -> int:
        """Koliko redova ispod zaglavlja liči na stavku."""
        if not mapping:
            return 0
        count = 0
        for row in range(header_row + 1, sheet.nrows):
            if ExcelHeadersEngine._is_data_row(sheet, row, mapping):
                count += 1
        return count

    @staticmethod
    def _is_data_row(sheet, row: int, mapping: dict[str, int]) -> bool:
        """Red je stavka ako ima sadržaj u bar jednoj ključnoj koloni I nije footer.

        Footer provjera je nužna: red "UKUPNO: 126,50" ima tekst u koloni naziva
        pa bi bez nje bio tiho uvučen kao stavka — greška koja se u carinskoj
        deklaraciji vidi tek kao pogrešan zbir.
        """
        has_content = False
        for field_name in _ESSENTIAL:
            col = mapping.get(field_name)
            if col is not None and str(sheet.value(row, col)).strip():
                has_content = True
                break
        if not has_content:
            return False

        return not ExcelHeadersEngine._is_footer_row(sheet, row, mapping)

    @staticmethod
    def _is_footer_row(sheet, row: int, mapping: dict[str, int]) -> bool:
        """Da li red počinje nekim od poznatih footer pojmova (UKUPNO/TOTAL/PDV...).

        Poredi se po GRANICI RIJEČI (\\b), ne golim `str.startswith` — bez toga bi
        "TOTALIZATOR ZA KOSILICU" (stvarna roba) bio odbačen jer doslovno počinje
        karakterima "total".
        """
        for field_name in _ESSENTIAL:
            col = mapping.get(field_name)
            if col is None:
                continue
            text = normalize_header(sheet.value(row, col))
            if text and any(
                re.match(rf"^{re.escape(p)}\b", text) for p in _FOOTER_PREFIXES
            ):
                return True
        return False

    def extract(self, document, config: dict[str, Any]) -> ExtractionTable:
        """Izvuci tabelu prema konfiguraciji iz profila."""
        sheet = document.sheet(config.get("sheet", 0))
        header_row = int(config.get("header_row", 0))
        mapping: dict[str, int] = dict(config.get("columns", {}))
        stop_on_empty = int(config.get("stop_after_empty_rows", 0))

        table = ExtractionTable(columns=sorted(mapping))
        table.diagnostics = {
            "engine": self.name,
            "sheet": sheet.name,
            "header_row": header_row,
            "columns": mapping,
        }

        consecutive_empty = 0
        for row in range(header_row + 1, sheet.nrows):
            if not self._is_data_row(sheet, row, mapping):
                raw = sheet.row_text(row)
                if not raw:
                    consecutive_empty += 1
                    if stop_on_empty and consecutive_empty >= stop_on_empty:
                        table.rejected.append((row, "kraj tabele (prazni redovi)"))
                        break
                    table.rejected.append((row, "prazan red"))
                else:
                    consecutive_empty = 0
                    if self._is_footer_row(sheet, row, mapping):
                        table.rejected.append((row, f"red zbira/footera: {raw[:60]}"))
                    else:
                        table.rejected.append((row, f"nema naziv/šifru: {raw[:60]}"))
                continue

            consecutive_empty = 0
            cells: dict[str, Cell] = {
                field_name: sheet.cell(row, col) for field_name, col in mapping.items()
            }
            table.rows.append(cells)

        return table

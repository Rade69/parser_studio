"""Normalization layer (TEST 5).

EKSPERIMENTALAN. NE u production core/.

Podržava:
- BROJEVI: 1.234,56 / 1,234.56 / 1234,56 / 1234.56 / 1 234,56 / 1 234.56
- PROCENTI: 10% / 10 % / 10,5 %
- JEDINICE: kg, g, pcs, pc, kom, kom., piece / pieces, stvarne
- VALUTE: EUR, USD, BAM/KM
- TARIFA: 8 cifara, tačke, razmaci, 6/8/10 cifara
- OCR korekcije: O→0, I/l→1 SAMO kad kontekst dokazuje numerički i rezultat
  zadovoljava format očekivanog polja.
"""
from __future__ import annotations
import re
from typing import Optional


# ─────────────────────────────────────────────────────────
# BROJEVI
# ─────────────────────────────────────────────────────────
def parse_number(s: str) -> Optional[float]:
    """Parsira evropske i US brojeve u float.

    Pravila:
    - '1.234,56' / '1,234.56' / '1234,56' / '1234.56' / '1 234,56' / '1 234.56'
    - Razmak se tretira kao hiljadarski separator
    - Ako ima i . i , — zadnji separator odlučuje decimalni format
      (tipično evropski: . hiljadski, , decimalni)
    - Ako ima samo , — gleda se broj cifara iza , da odluči decimalni ili hiljadski
    """
    if s is None:
        return None
    s = str(s).strip()
    if not s:
        return None
    # Ukloni razmake (obično hiljadski separator)
    s_no_space = s.replace(" ", "").replace("\u00a0", "")  # uključujući NBSP
    has_dot = "." in s_no_space
    has_comma = "," in s_no_space
    if has_dot and has_comma:
        # Zadnji separator odlučuje
        last_dot = s_no_space.rfind(".")
        last_comma = s_no_space.rfind(",")
        if last_comma > last_dot:
            # Evropski: , decimalni, . hiljadski
            s_clean = s_no_space.replace(".", "").replace(",", ".")
        else:
            # US: . decimalni, , hiljadski
            s_clean = s_no_space.replace(",", "")
    elif has_comma:
        # Samo , — ako ima tačno 1 zarez sa 1-3 cifre iza, decimalni; inače hiljadski
        parts = s_no_space.split(",")
        if len(parts) == 2 and 1 <= len(parts[1]) <= 3:
            s_clean = s_no_space.replace(",", ".")
        else:
            s_clean = s_no_space.replace(",", "")
    elif has_dot:
        s_clean = s_no_space
    else:
        s_clean = s_no_space
    try:
        return float(s_clean)
    except ValueError:
        return None


# ─────────────────────────────────────────────────────────
# PROCENTI
# ─────────────────────────────────────────────────────────
PERCENT_RE = re.compile(r"^\s*(-?\d+(?:[.,]\d+)?)\s*%?\s*$")


def parse_percent(s: str) -> Optional[float]:
    """'10%' / '10 %' / '10,5 %' → 10.0 / 10.0 / 10.5."""
    if s is None:
        return None
    s = str(s).strip()
    m = PERCENT_RE.match(s)
    if not m:
        return None
    return parse_number(m.group(1))


# ─────────────────────────────────────────────────────────
# JEDINICE
# ─────────────────────────────────────────────────────────
UNIT_ALIASES = {
    "kg": "kg",
    "g": "g",
    "gr": "g",
    "pcs": "pcs",
    "pc": "pcs",
    "piece": "pcs",
    "pieces": "pcs",
    "kom": "pcs",
    "kom.": "pcs",
    "komad": "pcs",
    "komada": "pcs",
    "stk": "pcs",
    "stk.": "pcs",
    "stuck": "pcs",
    "stueck": "pcs",
    "st": "pcs",
    "st.": "pcs",
    "l": "l",
    "ltr": "l",
    "liter": "l",
    "m": "m",
    "m2": "m2",
    "m3": "m3",
    "m\u00b2": "m2",
    "m\u00b3": "m3",
    "mt": "m",
    "m2": "m2",
    "m3": "m3",
}


def normalize_unit(s: str) -> Optional[str]:
    if not s:
        return None
    s_norm = s.strip().lower().rstrip(".").rstrip(",")
    return UNIT_ALIASES.get(s_norm, s_norm)  # vrati poznatu ili original


# ─────────────────────────────────────────────────────────
# VALUTE
# ─────────────────────────────────────────────────────────
CURRENCY_ALIASES = {
    "EUR": "EUR",
    "€": "EUR",
    "euro": "EUR",
    "USD": "USD",
    "$": "USD",
    "US$": "USD",
    "BAM": "BAM",
    "KM": "BAM",
    "BAM/KM": "BAM",
    "KM": "BAM",
    "HRK": "HRK",
    "kn": "HRK",
    "RSD": "RSD",
    "din": "RSD",
    "дин": "RSD",
    "MKD": "MKD",
    "den": "MKD",
}


def normalize_currency(s: str) -> Optional[str]:
    if not s:
        return None
    s_norm = s.strip().upper()
    return CURRENCY_ALIASES.get(s_norm, s_norm)


# ─────────────────────────────────────────────────────────
# TARIFA
# ─────────────────────────────────────────────────────────
def parse_tariff(s: str) -> Optional[str]:
    """Tarifa: 6-10 cifara, opcionalno tačke/razmaci.

    NE izmišlja nedostajuće cifre.
    Vraca None ako format nije prepoznatljiv.
    """
    if not s:
        return None
    s_clean = re.sub(r"[.\s/-]", "", str(s).strip())
    if not s_clean.isdigit():
        return None
    n = len(s_clean)
    if 6 <= n <= 10:
        return s_clean  # canon: samo cifre
    return None


# ─────────────────────────────────────────────────────────
# OCR KOREKCIJE — samo kad kontekst dokazuje numerički
# ─────────────────────────────────────────────────────────
def _looks_like_numeric_with_ocr_errors(s: str) -> bool:
    """Heuristika: da li bi O→0 / I/l→1 korekcija mogla pomoći."""
    return bool(re.search(r"[OIl]", s))


def ocr_correct_numeric(s: str, field: str = "auto") -> Optional[str]:
    """Primijeni O→0 i I/l→1 SAMO kad kontekst dokazuje numerički.

    field='numeric' ili 'tariff' zahtijeva da rezultat izgleda kao broj.
    field='auto' pokušava oba.
    """
    if not s:
        return None
    corrected = s.replace("O", "0").replace("o", "0").replace("I", "1").replace("l", "1")
    # Ako je već numerički
    if parse_number(corrected) is not None:
        return corrected
    # Provjeri tariff format
    if field in ("tariff", "auto"):
        t = parse_tariff(corrected)
        if t is not None:
            return t
    return None


def safe_ocr_correct(s: str, expected_format: str = "numeric") -> Optional[str]:
    """Wrapper: vrati None ako korekcija ne daje validan format.

    expected_format: 'numeric' | 'tariff' | 'auto'
    """
    if not s or not _looks_like_numeric_with_ocr_errors(s):
        return None
    return ocr_correct_numeric(s, field=expected_format)


# ─────────────────────────────────────────────────────────
# Aggregate: extract numeric candidates from cell
# ─────────────────────────────────────────────────────────
def extract_numeric_candidates(s: str) -> list[float]:
    """Ekstrahira sve numeričke vrijednosti iz ćelije (različiti formati).

    Koristi regex match za svaki broj (uključujući razmake i tačke/zareze).
    """
    if not s:
        return []
    # Regex: cifre sa opcionalnim separatorima (. , razmak NBSP / -)
    # Pokušaj match za svaki "kandidat token"
    candidates = []
    # Traži sve sekvence: digits (opcionalno separator) digits (opcionalno decimal)
    pattern = re.compile(r"-?\d+(?:[.,\s\u00a0/-]\d+)*(?:[.,]\d+)?")
    for match in pattern.finditer(s):
        token = match.group(0)
        n = parse_number(token)
        if n is not None:
            candidates.append(n)
    return candidates

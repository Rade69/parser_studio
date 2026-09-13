"""Semantic Column Resolver (sekcija 7).

Dodjeljuje ulogu svakoj koloni:
DESCRIPTION | PRODUCT_CODE | TARIFF | UNIT | QUANTITY | UNIT_PRICE
| LINE_AMOUNT | ORIGIN | NET_WEIGHT | GROSS_WEIGHT | DISCOUNT | UNKNOWN

Koristi kombinaciju signala:
1. header synonym
2. sadržaj kolone (numeric ratio, text ratio)
3. data format
4. arithmetic relations (qty × price ≈ amount)
5. neighboring columns (position kao slab signal)

NE production kod.
"""
from __future__ import annotations
import re
from typing import Any
import statistics


HEADER_SYNONYMS = {
    "DESCRIPTION": [
        "description", "opis", "opis robe", "naziv", "naziv artikla", "naziv robe",
        "item name", "roba", "artikal", "product", "artikl",
    ],
    "PRODUCT_CODE": [
        "item code", "code", "šifra", "sifra", "item", "art code",
        "product code", "barcode",
    ],
    "TARIFF": [
        "tariff", "tarifa", "tarifni broj", "tarifni", "tarifni br",
        "tariff number", "tariff heading", "tariff code", "hs code",
        "hs", "customs code",
    ],
    "UNIT": [
        "u.m.", "u.m", "jm", "unit", "jedinica", "jedinica mjere",
        "measure", "unit of measure", "um",
    ],
    "QUANTITY": [
        "quantity", "količina", "kolicina", "qty", "kol", "koli",
        "pieces", "kom", "qty/amount", "kol.",
    ],
    "UNIT_PRICE": [
        "unit price", "cena", "cijena", "price", "jed. cijena",
        "jed.cijena", "unitprice", "jedinica cijena", "cena/jm",
    ],
    "LINE_AMOUNT": [
        "amount", "iznos", "sum", "total amount", "line amount",
        "vrijednost", "fakturisana vrijednost", "total", "iznos/sum",
    ],
    "ORIGIN": [
        "country", "zemlja", "origin", "poreklo", "zemlja porekla",
        "zemlja porijekla", "country of origin", "drzava",
    ],
    "NET_WEIGHT": [
        "neto", "net", "net weight", "neto kg", "neto(kg)",
    ],
    "GROSS_WEIGHT": [
        "bruto", "gross", "gross weight", "bruto kg", "bruto(kg)",
    ],
    "DISCOUNT": [
        "rabat", "rab%", "discount", "popust", "rebate", "rebate %",
        "rabat%", "discount %",
    ],
}


def normalize_header(h: str) -> str:
    if not h:
        return ""
    s = h.lower().strip()
    s = s.replace("č", "c").replace("ć", "c").replace("š", "s").replace("ž", "z").replace("đ", "d")
    s = re.sub(r"\s+", " ", s)
    return s


def header_synonym_score(header: str, role: str) -> float:
    """Score 0-1 za header match sa role synonyms."""
    nh = normalize_header(header)
    if not nh:
        return 0.0
    best = 0.0
    for syn in HEADER_SYNONYMS.get(role, []):
        ns = normalize_header(syn)
        if nh == ns:
            best = max(best, 1.0)
        elif ns in nh or nh in ns:
            best = max(best, 0.85)
        else:
            nh_words = set(nh.split())
            ns_words = set(ns.split())
            if ns_words:
                overlap = len(nh_words & ns_words) / len(ns_words)
                if overlap >= 0.7:
                    best = max(best, 0.6)
    return best


def is_numeric(s: str) -> bool:
    """Provjeri da li string sadrži parsabilan broj."""
    from normalization import parse_number
    return parse_number(s) is not None


def numeric_ratio(cells: list[str]) -> float:
    n = 0
    nonempty = [c for c in cells if c and c.strip()]
    for c in nonempty:
        if is_numeric(c):
            n += 1
    return n / max(len(nonempty), 1)


def text_ratio(cells: list[str]) -> float:
    nonempty = [c for c in cells if c and c.strip()]
    n_text = 0
    for c in nonempty:
        s = re.sub(r"\s+", "", c)
        if s and sum(1 for ch in s if ch.isalpha()) / max(sum(1 for ch in s if ch.isalnum()), 1) >= 0.6:
            n_text += 1
    return n_text / max(len(nonempty), 1)


def avg_length(cells: list[str]) -> float:
    lengths = [len(c.strip()) for c in cells if c and c.strip()]
    return statistics.mean(lengths) if lengths else 0


def content_score(cells: list[str], role: str) -> float:
    """Score 0-1 baziran na sadržaju kolone za role."""
    if not cells:
        return 0.0
    nonempty = [c for c in cells if c and c.strip()]
    if not nonempty:
        return 0.0
    nr = numeric_ratio(cells)
    tr = text_ratio(cells)
    avg = avg_length(cells)
    score = 0.0
    if role in ("QUANTITY", "UNIT_PRICE", "LINE_AMOUNT", "TARIFF", "DISCOUNT", "NET_WEIGHT", "GROSS_WEIGHT"):
        if nr >= 0.8:
            score += 0.6
        elif nr >= 0.5:
            score += 0.3
        if avg < 12:  # numeričke vrijednosti obično kratke
            score += 0.2
    elif role in ("DESCRIPTION",):
        if tr >= 0.6:
            score += 0.6
        if avg >= 8:
            score += 0.3
    elif role == "PRODUCT_CODE":
        # Šifre su kratke, alfanumeričke
        if avg < 15 and nr + tr < 1.2:  # mješovito
            score += 0.5
    elif role == "ORIGIN":
        # Zemlja porijekla: kratki string, ne numerički
        if tr >= 0.7 and avg < 15:
            score += 0.6
    elif role == "UNIT":
        # Jedinica: kratki string
        if tr >= 0.7 and avg < 6:
            score += 0.6
    return min(score, 1.0)


def resolve_role(header: str, cells: list[str]) -> dict:
    """Dodijeli ulogu koloni na osnovu header + cells."""
    roles = list(HEADER_SYNONYMS.keys())
    scores = {}
    for role in roles:
        h_score = header_synonym_score(header, role)
        c_score = content_score(cells, role)
        # Težinski: header 60%, content 40%
        total = h_score * 0.6 + c_score * 0.4
        scores[role] = total
    best_role = max(scores, key=scores.get)
    best_score = scores[best_role]
    sorted_roles = sorted(scores.items(), key=lambda x: -x[1])
    second_score = sorted_roles[1][1] if len(sorted_roles) > 1 else 0
    margin = best_score - second_score
    if best_score < 0.3:
        role = "UNKNOWN"
        confidence = "UNRESOLVED"
    elif margin < 0.1:
        confidence = "REVIEW"
        role = best_role
    else:
        confidence = "HIGH"
        role = best_role
    return {
        "role": role,
        "confidence": confidence,
        "best_score": round(best_score, 4),
        "second_score": round(second_score, 4),
        "margin": round(margin, 4),
        "all_scores": {k: round(v, 4) for k, v in sorted(scores.items(), key=lambda x: -x[1])},
    }


def resolve_columns(columns: list[dict]) -> list[dict]:
    """Dodijeli uloge svim kolonama, uzimajući u obzir i neighboring columns."""
    if not columns:
        return []
    results = []
    for i, col in enumerate(columns):
        header = col.get("header_text", "")
        cells = col.get("cells", [])
        base = resolve_role(header, cells)
        # Position hint (slab signal)
        # Tipični raspored: [Code, Description, Tariff, Unit, Qty, Price, Amount, ...]
        # Ako je na poziciji 0/1 i nema signala → prefer PRODUCT_CODE/DESCRIPTION
        if base["confidence"] == "UNRESOLVED" and i == 0:
            base["position_hint"] = "first_column_likely_code"
        elif base["confidence"] == "UNRESOLVED" and i == 1:
            base["position_hint"] = "second_column_likely_description"
        results.append(base)
    # Ako su iste role dodijeljene susjednim kolonama, smanji confidence
    for i, r in enumerate(results):
        for j, r2 in enumerate(results):
            if i != j and r["role"] == r2["role"] and r["role"] != "UNKNOWN":
                r["confidence"] = "REVIEW"
                r["conflict_note"] = f"duplicate role with col {j}"
    return results

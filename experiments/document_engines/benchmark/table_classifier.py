"""Table Classifier (sekcija 3) — klasifikuje fizički Docling table segment.

Output:
- predicted_class: ITEM_TABLE | TARIFF_ORIGIN_SUMMARY | TOTALS_TABLE | OTHER | UNRESOLVED
- evidence: lista signala koji su triggerovali klasifikaciju
- confidence: HIGH | REVIEW | UNRESOLVED

NE production kod — eksperimentalan.
"""
from __future__ import annotations
import re
from typing import Any


# Header signals
ITEM_SIGNALS = [
    "description", "opis robe", "opis", "naziv artikla", "naziv",
    "item name", "roba", "artikal", "product",
    "quantity", "količina", "kolicina", "qty", "amount",
    "unit price", "cena", "cijena", "price",
    "iznos", "line amount", "total amount", "sum",
    "item code", "šifra", "sifra", "code", "item",
    "tariff", "tarifa", "tarifni", "tarif",
    "tariff number", "tarifni broj", "tarifni br",
    "u.m.", "jm", "unit", "jedinica",
    "country", "zemlja", "origin", "poreklo",
]

TARIFF_ORIGIN_SIGNALS = [
    "tariff heading", "tarifna oznaka", "tarifni broj", "tariff",
    "country", "zemlja", "zemlja porijekla", "zemlja porekla", "origin",
    "količina", "quantity", "qty",
    "iznos", "amount", "sum",
    "weight", "težina", "tezina",
    "bruto", "neto", "gross", "net",
]

TOTALS_SIGNALS = [
    "total", "ukupno", "vkupno", "sum total", "grand total",
    "bruto", "neto", "gross", "net",
    "payment", "plaćanje", "placanje",
    "for payment", "za plaćanje", "za placanje",
    "balance", "saldo",
]


def normalize_header(h: str) -> str:
    """Lowercase, strip dijakritike."""
    if not h:
        return ""
    s = h.lower().strip()
    s = s.replace("č", "c").replace("ć", "c").replace("š", "s").replace("ž", "z").replace("đ", "d")
    s = re.sub(r"\s+", " ", s)
    return s


def header_signal_score(header: str, signals: list[str]) -> tuple[float, list[str]]:
    """Vraća (score, list_matched_signals) za header."""
    nh = normalize_header(header)
    if not nh:
        return 0.0, []
    matched = []
    score = 0.0
    # Exact match
    for sig in signals:
        nsig = normalize_header(sig)
        if nh == nsig:
            score += 1.0
            matched.append(sig)
        # Substring
        elif nsig in nh or nh in nsig:
            score += 0.7
            matched.append(sig)
        # Word overlap
        else:
            nh_words = set(nh.split())
            nsig_words = set(nsig.split())
            if nsig_words:
                overlap = len(nh_words & nsig_words) / len(nsig_words)
                if overlap >= 0.7:
                    score += 0.5
                    matched.append(sig)
    return min(score, 5.0), matched  # cap


def classify_physical_segment(headers: list[str], n_rows: int, n_cols: int, page: int | None = None) -> dict:
    """Klasifikuj jedan fizički Docling table segment."""
    item_score = 0.0
    item_evidence = []
    tariff_score = 0.0
    tariff_evidence = []
    totals_score = 0.0
    totals_evidence = []
    for h in headers:
        s, m = header_signal_score(h, ITEM_SIGNALS)
        if s > 0:
            item_score += s
            item_evidence.extend(m)
        s, m = header_signal_score(h, TARIFF_ORIGIN_SIGNALS)
        if s > 0:
            tariff_score += s
            tariff_evidence.extend(m)
        s, m = header_signal_score(h, TOTALS_SIGNALS)
        if s > 0:
            totals_score += s
            totals_evidence.extend(m)
    # Strukturni signali
    structure = {
        "n_rows": n_rows,
        "n_cols": n_cols,
        "page": page,
    }
    # ITEM_TABLE structural: rows > 3, cols >= 5 (multi-column data)
    if n_rows >= 5 and n_cols >= 5:
        item_score += 0.5
        item_evidence.append("structure: many_rows_many_cols")
    # TOTALS structural: rows <= 5 (kratki summary), cols >= 3
    if 1 <= n_rows <= 5:
        totals_score += 0.3
        totals_evidence.append("structure: short_table")
    # TARIFF_ORIGIN structural: rows srednje, cols 4-6
    if 3 <= n_rows <= 30 and 3 <= n_cols <= 8:
        tariff_score += 0.2
        tariff_evidence.append("structure: medium_table")
    # Decision
    scores = {
        "ITEM_TABLE": item_score,
        "TARIFF_ORIGIN_SUMMARY": tariff_score,
        "TOTALS_TABLE": totals_score,
    }
    best_class = max(scores, key=scores.get)
    best_score = scores[best_class]
    total_signal = sum(scores.values())
    # Confidence
    if total_signal == 0:
        predicted = "OTHER"
        confidence = "UNRESOLVED"
        reason = "no_signals"
    elif best_score < 1.0:
        predicted = "OTHER"
        confidence = "UNRESOLVED"
        reason = "weak_signals"
    else:
        margin = best_score - max(s for k, s in scores.items() if k != best_class)
        if margin < 0.5:
            confidence = "REVIEW"
        else:
            confidence = "HIGH"
        predicted = best_class
        reason = f"best={best_class} score={best_score:.2f}"
    return {
        "predicted_class": predicted,
        "evidence": list(set({
            "ITEM_TABLE": item_evidence,
            "TARIFF_ORIGIN_SUMMARY": tariff_evidence,
            "TOTALS_TABLE": totals_evidence,
        }.get(predicted, []))),
        "confidence": confidence,
        "scores": {k: round(v, 2) for k, v in scores.items()},
        "structure": structure,
        "reason": reason,
    }


def classify_all_segments(doc) -> list[dict]:
    """Klasifikuj sve fizičke Docling table segmente u dokumentu."""
    results = []
    tables = list(doc.tables)
    for seg_idx, table in enumerate(tables):
        data = table.data
        # Headeri iz grid-a (row 0)
        cells = list(data.table_cells or [])
        max_col = 0
        for c in cells:
            ec = getattr(c, "end_col_offset_idx", None) or 0
            if ec > max_col:
                max_col = ec
        n_rows = max((getattr(c, "end_row_offset_idx", 0) or 0) for c in cells) if cells else 0
        n_cols = max_col
        # Izvuci header tekst
        headers = []
        for c in cells:
            if getattr(c, "column_header", False):
                headers.append(getattr(c, "text", "") or "")
        # Pronađi page iz provenance
        page = None
        for c in cells:
            bbox = getattr(c, "bbox", None)
            if bbox is not None:
                # Docling PageNumber
                pn = getattr(c, "page_no", None) or getattr(c, "page", None)
                if pn is not None:
                    page = pn
                    break
        classification = classify_physical_segment(headers, n_rows, n_cols, page)
        classification["segment_index"] = seg_idx
        classification["headers_raw"] = headers
        results.append(classification)
    return results

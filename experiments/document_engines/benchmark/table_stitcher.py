"""Table Stitcher (sekcija 4) — spaja fizičke Docling segmente u logičke tabele.

NE production kod.

Kriteriji za stitch:
- Ista semantic column signature (isti set headera)
- Ista ili veoma slična zaglavlja
- Nastavak rednih brojeva (column 0 nastavlja 1, 2, 3, ...)
- Ista klasifikacija tabele
- Susjedne stranice
- Kompatibilan broj/uloga kolona
"""
from __future__ import annotations
from typing import Any


def headers_match_strict(h1: list[str], h2: list[str]) -> bool:
    """Strogi match: isti set i isti redoslijed."""
    if len(h1) != len(h2):
        return False
    return all(a.strip().lower() == b.strip().lower() for a, b in zip(h1, h2))


def headers_match_fuzzy(h1: list[str], h2: list[str], threshold: float = 0.8) -> float:
    """Fuzzy match score (0-1)."""
    if not h1 or not h2:
        return 0.0
    s1 = [h.strip().lower() for h in h1]
    s2 = [h.strip().lower() for h in h2]
    if len(s1) != len(s2):
        # Različit broj kolona — manji match
        return 0.0
    matches = sum(1 for a, b in zip(s1, s2) if a == b or a in b or b in a)
    return matches / max(len(s1), 1)


def row_numbers_continue(seg1_first_row: list[str], seg2_first_row: list[str]) -> bool:
    """Heuristika: prvi numerički element seg2 nastavlja seg1."""
    if not seg1_first_row or not seg2_first_row:
        return False
    try:
        last_n1 = int(seg1_first_row[0])
        first_n2 = int(seg2_first_row[0])
        return first_n2 == last_n1 + 1
    except (ValueError, TypeError, IndexError):
        return False


def can_stitch(seg1: dict, seg2: dict) -> tuple[bool, str]:
    """Odluči da li se dva segmenta mogu spojiti."""
    reasons = []
    score = 0.0
    # 1. Ista klasifikacija
    if seg1.get("predicted_class") == seg2.get("predicted_class"):
        score += 0.3
        reasons.append("same_class")
    else:
        return False, "different_class"
    # 2. Ista/slična zaglavlja
    h_match = headers_match_fuzzy(
        seg1.get("headers_raw", []),
        seg2.get("headers_raw", []),
        threshold=0.6,
    )
    if h_match >= 0.6:
        score += 0.4
        reasons.append(f"headers_match={h_match:.2f}")
    else:
        return False, f"headers_mismatch={h_match:.2f}"
    # 3. Susjedne stranice: page2 mora biti > page1 (bez istog page-a, bez regresije)
    page1 = seg1.get("structure", {}).get("page")
    page2 = seg2.get("structure", {}).get("page")
    if page1 is not None and page2 is not None:
        if page2 > page1:
            score += 0.2
            reasons.append(f"page_progression={page1}->{page2}")
        elif page2 == page1:
            return False, "same_page_no_progression"
        else:
            return False, "page_regression"
    # 4. Kompatibilan broj kolona
    cols1 = seg1.get("structure", {}).get("n_cols", 0)
    cols2 = seg2.get("structure", {}).get("n_cols", 0)
    if cols1 > 0 and cols2 > 0:
        if cols1 == cols2:
            score += 0.1
            reasons.append("same_n_cols")
        elif abs(cols1 - cols2) <= 1:
            score += 0.05
            reasons.append(f"similar_n_cols={cols1},{cols2}")
        else:
            return False, f"n_cols_mismatch={cols1},{cols2}"
    # Score threshold
    can = score >= 0.5
    return can, ", ".join(reasons) + f" score={score:.2f}"


def stitch_physical_segments(classifications: list[dict]) -> list[dict]:
    """Stitch listu klasifikovanih fizičkih segmenata u logičke tabele."""
    if not classifications:
        return []
    logical_tables = []
    current_logical = {
        "logical_id": 0,
        "predicted_class": classifications[0]["predicted_class"],
        "segments": [classifications[0]["segment_index"]],
        "evidence": [classifications[0].get("reason", "")],
    }
    for i in range(1, len(classifications)):
        prev = classifications[i - 1]
        curr = classifications[i]
        can, reason = can_stitch(prev, curr)
        if can:
            current_logical["segments"].append(curr["segment_index"])
            current_logical["evidence"].append(reason)
        else:
            logical_tables.append(current_logical)
            current_logical = {
                "logical_id": len(logical_tables),
                "predicted_class": curr["predicted_class"],
                "segments": [curr["segment_index"]],
                "evidence": [curr.get("reason", "")],
            }
    logical_tables.append(current_logical)
    return logical_tables

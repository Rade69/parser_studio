"""Price vs Amount Resolver (sekcija 8).

Za svaku kombinaciju Q, P, A:
- arithmetic_match_rate = matching_rows / eligible_rows
- Preferira mapiranje sa:
  - header evidence
  - najveći arithmetic_match_rate
  - konzistentno na većini redova
"""
from __future__ import annotations
from typing import Any


def arithmetic_match(rows: list[dict], q_header: str, p_header: str, a_header: str, discount_header: str | None = None) -> float:
    """Izračunaj qty × price ≈ amount match rate."""
    if not rows:
        return 0.0
    matching = 0
    eligible = 0
    for r in rows:
        try:
            q = float(r.get(q_header))
            p = float(r.get(p_header))
            a = float(r.get(a_header))
        except (ValueError, TypeError, KeyError):
            continue
        eligible += 1
        discount = r.get(discount_header) if discount_header else None
        if discount is not None:
            try:
                d = float(discount)
            except (ValueError, TypeError):
                d = None
            if d is not None:
                e = q * p * (1 - d / 100)
            else:
                e = q * p
        else:
            e = q * p
        if abs(e - a) < 0.05:  # Tolerancija za rounding
            matching += 1
    return matching / max(eligible, 1)


def resolve_price_amount(rows: list[dict], numeric_columns: list[str], header_evidence: dict | None = None) -> dict:
    """Odredi koja kolona je UNIT_PRICE, a koja LINE_AMOUNT.

    Za svaku kombinaciju (q_col, p_col, a_col) računamo arithmetic_match_rate.
    Q mora imati integer-like karakter (integer_ratio >= 0.7) — Quantity je obično cijeli broj.
    Ako Q nema integer_like karakter, penaliziraj.

    Biramo onu sa najboljim score, poštujući:
    - HIGH: eligible >= 5 AND match_rate >= 0.80 AND best - second >= 0.20
    - UNRESOLVED: inače

    header_evidence (opciono): {header_name: 'PRICE' | 'AMOUNT'} za preferenciju.
    """
    if not rows or len(numeric_columns) < 3:
        return {
            "resolved": False,
            "best_assignment": None,
            "all_assignments": [],
            "confidence": "UNRESOLVED",
            "reason": "insufficient_data_or_columns",
        }
    # Heuristika: za svaku kolonu izračunaj integer_ratio
    def integer_ratio(col):
        cnt_int = 0
        cnt_total = 0
        for r in rows:
            v = r.get(col)
            if v is None:
                continue
            try:
                f = float(v)
                if abs(f - round(f)) < 0.01:
                    cnt_int += 1
            except (ValueError, TypeError):
                pass
            cnt_total += 1
        return cnt_int / max(cnt_total, 1)

    int_ratios = {c: integer_ratio(c) for c in numeric_columns}
    # Generiraj sve moguće kombinacije
    assignments = []
    cols = numeric_columns
    for i, q in enumerate(cols):
        for j, p in enumerate(cols):
            if j == i:
                continue
            for k, a in enumerate(cols):
                if k == i or k == j:
                    continue
                rate = arithmetic_match(rows, q, p, a)
                # Penaliziraj ako Q nije integer-like
                int_penalty = 0.0
                if int_ratios[q] < 0.7:
                    int_penalty = 0.3  # 30% penalty
                # Bonus za header evidence
                bonus = 0.0
                if header_evidence:
                    if header_evidence.get(p, "").upper() == "PRICE":
                        bonus += 0.1
                    if header_evidence.get(a, "").upper() == "AMOUNT":
                        bonus += 0.1
                adjusted_rate = max(0.0, min(rate + bonus - int_penalty, 1.0))
                assignments.append({
                    "q": q,
                    "p": p,
                    "a": a,
                    "match_rate": round(rate, 4),
                    "integer_ratio_q": round(int_ratios[q], 4),
                    "adjusted_rate": round(adjusted_rate, 4),
                })
    if not assignments:
        return {
            "resolved": False,
            "best_assignment": None,
            "all_assignments": [],
            "confidence": "UNRESOLVED",
            "reason": "no_assignments",
        }
    assignments.sort(key=lambda x: -x["adjusted_rate"])
    best = assignments[0]
    second = assignments[1] if len(assignments) > 1 else None
    eligible = len(rows)
    if eligible < 5:
        confidence = "UNRESOLVED"
        reason = "few_rows"
    elif best["adjusted_rate"] < 0.80:
        confidence = "UNRESOLVED"
        reason = "low_match_rate"
    elif second is None or (best["adjusted_rate"] - second["adjusted_rate"]) < 0.20:
        confidence = "UNRESOLVED"
        reason = "ambiguous_best_second_too_close"
    else:
        confidence = "HIGH"
        reason = "ok"
    return {
        "resolved": confidence == "HIGH",
        "best_assignment": best,
        "second_best": second,
        "all_assignments": assignments[:5],
        "confidence": confidence,
        "eligible_rows": eligible,
        "reason": reason,
    }

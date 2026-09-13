"""Quality Gate F6–F10 evaluacija nad Docling strukturama.

Pravila (iz specifikacije):
- F6: Tabela NIJE pronađena ali postoji item-like struktura u markdownu/Docling body
- F7: Description kolona nije pouzdano identifikovana (score < 0.65 ili margin < 0.10)
- F8: Numeric roles (Quantity/Unit Price/Line Amount) nisu pouzdano identifikovani
- F9: Strukturno slomljeni item redovi (>20% broken u analyzable)
- F10: Matematička konzistentnost (qty × price ≈ amount)

NE ovise o markdown tekstu. Koriste TableData strukturu.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import re

NUMBER_RE = re.compile(r"-?\d+(?:[.,]\d+)?")


def parse_number(s: str) -> float | None:
    """Parsira '1.234,56' / '1234.56' / '1234' u float."""
    if s is None:
        return None
    s = str(s).strip()
    if not s:
        return None
    # Ako ima i . i , — pretpostavi evropski format (1.234,56)
    if "." in s and "," in s:
        s_clean = s.replace(".", "").replace(",", ".")
    elif "," in s:
        # Ako zarez ima 2 cifre iza, tretiraj kao decimalni zarez
        parts = s.split(",")
        if len(parts[-1]) <= 2:
            s_clean = s.replace(",", ".")
        else:
            s_clean = s.replace(",", "")
    else:
        s_clean = s
    try:
        return float(s_clean)
    except ValueError:
        return None


def normalize_text(s: str) -> str:
    """Lowercase, strip dijakritike za header match."""
    if not s:
        return ""
    s = s.lower().strip()
    s = s.replace("č", "c").replace("ć", "c").replace("š", "s").replace("ž", "z").replace("đ", "d")
    s = re.sub(r"\s+", " ", s)
    return s


# ─────────────────────────────────────────────────────────
# F6 — Tabela NIJE pronađena, ali postoji item-like struktura
# ─────────────────────────────────────────────────────────
def _candidate_item_lines_from_text(doc_text: str) -> list[dict]:
    """Heuristika: nađi redove u Docling text body koji izgledaju kao item stavke."""
    if not doc_text:
        return []
    candidates = []
    for line in doc_text.splitlines():
        line = line.strip()
        if not line:
            continue
        nums = [m.group() for m in NUMBER_RE.finditer(line)]
        # Mora imati >= 1 tekstualni segment >= 3 slova
        text_parts = re.split(r"\s{2,}|\t", line)
        has_long_text = any(len(re.sub(r"[^a-zA-ZčćšžđČĆŠŽĐ]", "", t)) >= 3 for t in text_parts)
        if has_long_text and len(nums) >= 2:
            candidates.append({"text": line, "n_numbers": len(nums), "numbers": nums})
    return candidates


def _numeric_alignment(candidates: list[dict]) -> float:
    """Koliko kandidat-redova ima numeričke vrijednosti na sličnim X pozicijama.
    Budući da nemamo X pozicije iz plain texta, koristimo proxy:
    - jednak broj numeričkih vrijednosti
    """
    if not candidates:
        return 0.0
    counts = [c["n_numbers"] for c in candidates]
    if not counts:
        return 0.0
    modal = max(set(counts), key=counts.count)
    same_count = sum(1 for c in counts if c == modal)
    return same_count / len(counts)


def _row_repetition(candidates: list[dict]) -> float:
    """Koliko redova ima sličnu strukturu (isti broj numerika i tekstualnih blokova)."""
    if len(candidates) < 2:
        return 0.0
    keys = [(c["n_numbers"], len(c["text"])) for c in candidates]
    from collections import Counter

    cnt = Counter(keys)
    most_common_count = cnt.most_common(1)[0][1]
    return most_common_count / len(candidates)


def _description_presence(candidates: list[dict]) -> float:
    """Koliko redova ima >= 1 tekstualni segment >= 5 slova (description-like)."""
    if not candidates:
        return 0.0
    n = 0
    for c in candidates:
        text_parts = re.split(r"\s{2,}|\t", c["text"])
        if any(len(re.sub(r"[^a-zA-ZčćšžđČĆŠŽĐ]", "", t)) >= 5 for t in text_parts):
            n += 1
    return n / len(candidates)


def _amount_pattern(candidates: list[dict]) -> float:
    """Koliko redova ima numeriku >= 2 decimale (amount-like)."""
    if not candidates:
        return 0.0
    n = 0
    for c in candidates:
        for num in c["numbers"]:
            if "." in num or "," in num:
                decimal_part = num.split(".")[-1] if "." in num else num.split(",")[-1]
                if len(decimal_part) >= 2:
                    n += 1
                    break
    return n / len(candidates)


def _header_evidence(doc_text: str) -> float:
    """Da li postoji header riječ koja ukazuje na tabelu stavki?"""
    if not doc_text:
        return 0.0
    headers = ["red. br", "r.br", "naziv", "kolicina", "količina", "cijena", "iznos", "vrijednost", "tarifni", "tarifa"]
    found = sum(1 for h in headers if h in doc_text.lower())
    return min(found / 4, 1.0)


def evaluate_f6(docling_tables_count: int, docling_text: str) -> dict:
    """F6 trigger ako: nema tabela ALI ima item-like strukturu."""
    candidates = _candidate_item_lines_from_text(docling_text)
    n = len(candidates)
    if docling_tables_count == 0 and n >= 4:
        numeric_alignment = _numeric_alignment(candidates)
        row_repetition = _row_repetition(candidates)
        desc_presence = _description_presence(candidates)
        amount_pat = _amount_pattern(candidates)
        header_ev = _header_evidence(docling_text)
        item_score = (
            0.30 * numeric_alignment
            + 0.25 * row_repetition
            + 0.20 * desc_presence
            + 0.15 * amount_pat
            + 0.10 * header_ev
        )
        hard_trigger = n >= 6 and numeric_alignment >= 0.70
        f6_true = item_score >= 0.65 or hard_trigger
        return {
            "triggered": f6_true,
            "candidate_lines": n,
            "numeric_alignment": round(numeric_alignment, 4),
            "row_repetition": round(row_repetition, 4),
            "description_presence": round(desc_presence, 4),
            "amount_pattern": round(amount_pat, 4),
            "header_evidence": round(header_ev, 4),
            "item_structure_score": round(item_score, 4),
            "hard_trigger": hard_trigger,
            "verdict": "TRUE" if f6_true else "FALSE",
            "reason": "no_tables_with_item_structure" if f6_true else "tables_present_or_no_structure",
        }
    return {
        "triggered": False,
        "candidate_lines": n,
        "docling_tables_count": docling_tables_count,
        "verdict": "FALSE",
        "reason": "tables_present" if docling_tables_count > 0 else "insufficient_candidates",
    }


# ─────────────────────────────────────────────────────────
# F7 — Description kolona nije pouzdano identifikovana
# ─────────────────────────────────────────────────────────
# Početni rječnik labela za description (iz stvarnih dokumenata + projektnih sinonima).
# OGRANIČENO na ono što STVARNO postoji u testnim fakturama ili u PLAN.md.
DESCRIPTION_HEADER_LABELS = [
    # Iz testnih faktura (Faktura-1/2, Medicopharm, Sumaprom)
    "naziv robe",
    "naziv",
    "description",
    "opis",
    "roba",
    "artikal",
    "product",
    # Iz PLAN.md (sekcija 5 — generički prepoznavač)
    "opis robe",
]


def header_score(header_text: str) -> float:
    """0.00 / 0.60 / 0.80 / 1.00 prema specifikaciji."""
    nh = normalize_text(header_text)
    if not nh:
        return 0.0
    for label in DESCRIPTION_HEADER_LABELS:
        if nh == label:
            return 1.00
    for label in DESCRIPTION_HEADER_LABELS:
        # Jaka fuzzy: substring match kao proxy
        if label in nh or nh in label:
            return 0.80
    # Fuzzy preko dijeljenja riječi
    nh_words = set(nh.split())
    for label in DESCRIPTION_HEADER_LABELS:
        label_words = set(label.split())
        if not label_words:
            continue
        overlap = len(nh_words & label_words)
        ratio = overlap / len(label_words)
        if ratio >= 0.90:
            return 0.80
        if ratio >= 0.80:
            return 0.60
    return 0.0


def textual_content_score(cells: list[str]) -> float:
    """neprazne ćelije dominantno tekstualne / ukupno neprazne."""
    if not cells:
        return 0.0
    nonempty = [c for c in cells if c and c.strip()]
    if not nonempty:
        return 0.0
    dominant_textual = 0
    for c in nonempty:
        s = re.sub(r"\s+", "", c)
        alnum = sum(1 for ch in s if ch.isalnum())
        letters = sum(1 for ch in s if ch.isalpha())
        if alnum == 0:
            continue
        if letters / alnum >= 0.60:
            dominant_textual += 1
    return dominant_textual / len(nonempty)


def text_length_score(cells: list[str]) -> float:
    """Median-length score."""
    lengths = [len(c.strip()) for c in cells if c and c.strip()]
    if not lengths:
        return 0.0
    lengths.sort()
    n = len(lengths)
    median = lengths[n // 2] if n % 2 == 1 else (lengths[n // 2 - 1] + lengths[n // 2]) / 2
    if median >= 12:
        return 1.00
    if median >= 8:
        return 0.75
    if median >= 4:
        return 0.40
    return 0.10


def uniqueness_score(cells: list[str]) -> float:
    """distinct / non-empty."""
    nonempty = [c.strip() for c in cells if c and c.strip()]
    if not nonempty:
        return 0.0
    return len(set(nonempty)) / len(nonempty)


def evaluate_f7(columns: list[dict]) -> dict:
    """F7 evaluacija nad listom kolona. Svaka kolona mora imati:
    - header_text
    - cells (list[str])
    """
    if not columns:
        return {
            "triggered": True,
            "verdict": "TRUE",
            "reason": "no_columns",
            "per_column": [],
            "best_score": 0.0,
            "margin": 0.0,
        }
    per_column = []
    for col in columns:
        header = col.get("header_text", "")
        cells = col.get("cells", [])
        h = header_score(header)
        tc = textual_content_score(cells)
        tl = text_length_score(cells)
        un = uniqueness_score(cells)
        score = 0.45 * h + 0.25 * tc + 0.15 * tl + 0.15 * un
        per_column.append({
            "header": header,
            "header_score": round(h, 4),
            "textual_content_score": round(tc, 4),
            "text_length_score": round(tl, 4),
            "uniqueness_score": round(un, 4),
            "total_score": round(score, 4),
        })
    sorted_scores = sorted(per_column, key=lambda c: c["total_score"], reverse=True)
    best = sorted_scores[0]["total_score"] if sorted_scores else 0.0
    second = sorted_scores[1]["total_score"] if len(sorted_scores) > 1 else 0.0
    margin = best - second
    f7_true = best < 0.65 or margin < 0.10
    return {
        "triggered": f7_true,
        "verdict": "TRUE" if f7_true else "FALSE",
        "best_score": round(best, 4),
        "second_best_score": round(second, 4),
        "margin": round(margin, 4),
        "per_column": per_column,
        "best_column": sorted_scores[0]["header"] if sorted_scores else None,
        "reason": "low_confidence" if f7_true else "high_confidence",
    }


# ─────────────────────────────────────────────────────────
# F8 — Numeričke uloge (Quantity / Unit Price / Line Amount) nisu pouzdane
# ─────────────────────────────────────────────────────────
def _is_numeric(s: str) -> bool:
    return parse_number(s) is not None


def _is_positive(s: str) -> bool:
    n = parse_number(s)
    return n is not None and n > 0


def _looks_integer_or_reasonable_decimal(s: str) -> bool:
    n = parse_number(s)
    if n is None:
        return False
    # Ako je cijeli broj ili ima <= 3 decimale
    return abs(n - round(n, 3)) < 0.001


def evaluate_f8(columns: list[dict]) -> dict:
    """Vraća role assignments i F8 trigger."""
    per_column = []
    for col in columns:
        cells = [c for c in col.get("cells", []) if c and c.strip()]
        if not cells:
            per_column.append({
                "header": col.get("header_text", ""),
                "numeric_ratio": 0.0,
                "positive_ratio": 0.0,
                "integer_or_reasonable_decimal_ratio": 0.0,
                "is_numeric": False,
            })
            continue
        numeric = [c for c in cells if _is_numeric(c)]
        positive = [c for c in cells if _is_positive(c)]
        int_dec = [c for c in cells if _looks_integer_or_reasonable_decimal(c)]
        n = len(cells)
        per_column.append({
            "header": col.get("header_text", ""),
            "n_cells": n,
            "numeric_ratio": round(len(numeric) / n, 4),
            "positive_ratio": round(len(positive) / n, 4),
            "integer_or_reasonable_decimal_ratio": round(len(int_dec) / n, 4),
            "is_numeric": len(numeric) / n >= 0.80 if n > 0 else False,
        })
    # Filtriraj numeričke kolone
    numeric_cols = [c for c in per_column if c.get("is_numeric", False)]
    n_numeric = len(numeric_cols)

    # Role kandidati — koristimo HEADER ime za poređenje (per_column pravi nove dict-ove)
    def find_best(predicate, exclude_headers=None):
        if exclude_headers is None:
            exclude_headers = set()
        candidates = [
            c for c in per_column
            if c["header"] not in exclude_headers and predicate(c)
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda c: c["numeric_ratio"])

    quantity_col = find_best(
        lambda c: c.get("numeric_ratio", 0) >= 0.80
        and c.get("positive_ratio", 0) >= 0.90
        and c.get("integer_or_reasonable_decimal_ratio", 0) >= 0.80
    )
    qty_header = quantity_col["header"] if quantity_col else None
    price_col = find_best(
        lambda c: c.get("numeric_ratio", 0) >= 0.80
        and c.get("positive_ratio", 0) >= 0.90,
        exclude_headers={qty_header} if qty_header else set(),
    )
    price_header = price_col["header"] if price_col else None
    amount_col = find_best(
        lambda c: c.get("numeric_ratio", 0) >= 0.80
        and c.get("positive_ratio", 0) >= 0.90,
        exclude_headers={h for h in (qty_header, price_header) if h},
    )

    # Pouzdanost = da li imamo sva 3 RAZLIČITA role-a (po headeru)
    identified_headers = [h for h in (qty_header, price_header, amount_col["header"] if amount_col else None) if h]
    n_identified = len(set(identified_headers))
    reliable = n_identified >= 3

    # Conflict trigger za razlikovanje Price vs Amount NIJE IMPLEMENTIRAN.
    # Razlog: price i amount tipično imaju isti numeric_ratio + positive_ratio + int_dec_ratio
    # (oboje su decimalni pozitivni brojevi). Za stvarnu razliku trebao bih ground-truth
    # baziranu formulu (npr. omjer amount/price vs quantity), što zahtijeva evaluaciju
    # ground-truth-a prije kalibracije.
    # Po specifikaciji: "Ne izmišljaj role score bez dokumentovane formule."
    conflict = False  # placehodler — vidi NOTE

    f8_true = not reliable or conflict
    return {
        "triggered": f8_true,
        "verdict": "TRUE" if f8_true else "FALSE",
        "n_numeric_columns": n_numeric,
        "quantity": quantity_col["header"] if quantity_col else None,
        "unit_price": price_col["header"] if price_col else None,
        "line_amount": amount_col["header"] if amount_col else None,
        "conflict_role_ambiguous": conflict,
        "reliable": reliable,
        "per_column": per_column,
        "reason": "roles_unidentified" if f8_true else "roles_identified",
        "note": "Price/Amount role conflict NIJE IMPLEMENTIRAN (zahtijeva ground-truth kalibraciju)",
    }


# ─────────────────────────────────────────────────────────
# F9 — Strukturno slomljeni item redovi
# ─────────────────────────────────────────────────────────
def evaluate_f9(table_data: dict) -> dict:
    """F9 trigger ako > 20% redova ima B1-B4 broken uslove.

    table_data očekuje:
    - rows: list[list[dict]] — svaka ćelija ima 'text' i opciono 'x0','x1','col_index'
    - expected_columns: kolone koje očekujemo (npr. quantity/price/amount)
    - column_x_centers: dict[col_name -> float]
    """
    rows = table_data.get("rows", [])
    expected_columns = table_data.get("expected_columns", [])
    column_x_centers = table_data.get("column_x_centers", {})
    if not rows or not expected_columns:
        return {
            "triggered": False,
            "verdict": "FALSE",
            "analyzable_rows": 0,
            "broken_rows": 0,
            "broken_rate": 0.0,
            "broken_details": [],
            "reason": "no_data_or_no_expected_columns",
        }
    modal_n_cells = max((len(r) for r in rows), default=0)
    analyzable = []
    broken_details = []
    for i, row in enumerate(rows):
        # Normalizuj multiline description — za sada, tretiraj svaki red kao zaseban
        cell_nums = []
        cell_x_centers = []
        cell_texts = []
        for c in row:
            t = c.get("text", "").strip() if isinstance(c, dict) else str(c).strip()
            nums = [m.group() for m in NUMBER_RE.finditer(t)]
            cell_nums.append((t, nums))
            x0 = c.get("x0", None) if isinstance(c, dict) else None
            x1 = c.get("x1", None) if isinstance(c, dict) else None
            if x0 is not None and x1 is not None:
                cell_x_centers.append((x0 + x1) / 2)
            else:
                cell_x_centers.append(None)
            cell_texts.append(t)
        # B1: nedostaju >= 2 numerička polja
        n_with_numbers = sum(1 for t, nums in cell_nums if nums)
        missing_numeric = expected_columns_count = len(expected_columns) - n_with_numbers
        # B2: jedna ćelija ima >= 2 numeričke vrijednosti koje pripadaju različitim kolonama
        b2 = any(len(nums) >= 2 for t, nums in cell_nums)
        # B4: broj ćelija odstupa >= 2 od moda
        b4 = abs(len(row) - modal_n_cells) >= 2
        # B3: overlap sa susjednom kolonom >= 25% — zahtijeva X centre; samo info
        reasons = []
        if missing_numeric >= 2:
            reasons.append("B1")
        if b2:
            reasons.append("B2")
        if b4:
            reasons.append("B4")
        if reasons:
            broken_details.append({
                "row_index": i,
                "reasons": reasons,
                "n_cells": len(row),
                "cell_texts": cell_texts[:8],
                "missing_numeric_fields": max(0, missing_numeric),
            })
            analyzable.append(i)
    broken_count = len(broken_details)
    rate = broken_count / max(len(rows), 1)
    f9_true = len(rows) >= 5 and broken_count >= 2 and rate > 0.20
    return {
        "triggered": f9_true,
        "verdict": "TRUE" if f9_true else "FALSE",
        "analyzable_rows": len(rows),
        "broken_rows": broken_count,
        "broken_rate": round(rate, 4),
        "broken_details": broken_details,
        "modal_n_cells": modal_n_cells,
        "reason": "broken_rows_above_20pct" if f9_true else "stable",
    }


# ─────────────────────────────────────────────────────────
# F10 — Matematička konzistentnost
# ─────────────────────────────────────────────────────────
def _decimals_in_number(n: float) -> int:
    s = f"{n:.10f}".rstrip("0").rstrip(".")
    if "." in s:
        return len(s.split(".")[1])
    return 0


def evaluate_f10_row(q: float, p: float, a: float, discount: float | None = None) -> dict:
    """Jedan red F10 evaluacije."""
    # MODEL 1: A = Q * P
    # MODEL 2: A = Q * P * (1 - discount/100) ako discount je eksplicitno prisutan
    if discount is not None:
        e = q * p * (1 - discount / 100)
        model = "MODEL_2_DISCOUNT"
    else:
        e = q * p
        model = "MODEL_1_SIMPLE"

    abs_err = abs(e - a)
    rel_err = abs_err / max(abs(e), abs(a), 1e-9)
    price_dec = min(_decimals_in_number(p), 6)
    amount_dec = min(_decimals_in_number(a), 6)
    price_round_bound = abs(q) * 0.5 * (10 ** -price_dec) if q != 0 else 0
    amount_round_bound = 0.5 * (10 ** -amount_dec)
    rounding_bound = price_round_bound + amount_round_bound
    rounding_tol = min(rounding_bound, 0.005 * max(abs(e), abs(a)))
    final_tol = max(0.02, 0.001 * max(abs(e), abs(a)), rounding_tol)
    passed = abs_err <= final_tol
    severe = rel_err >= 0.10 and abs_err >= 1.00
    return {
        "q": q, "p": p, "a": a, "discount": discount,
        "expected": round(e, 4),
        "absolute_error": round(abs_err, 4),
        "relative_error": round(rel_err, 6),
        "tolerance": round(final_tol, 6),
        "pass": bool(passed),
        "severe_mismatch": bool(severe),
        "model": model,
    }


def _normalize_row(r: dict) -> dict | None:
    """Normalizuj ključeve: q/p/a ili quantity/unit_price/line_amount."""
    q = r.get("q") or r.get("quantity")
    p = r.get("p") or r.get("unit_price")
    a = r.get("a") or r.get("line_amount")
    if q is None or p is None or a is None:
        return None
    return {"q": q, "p": p, "a": a, "discount": r.get("discount")}


def evaluate_f10(item_rows: list[dict]) -> dict:
    """F10 evaluacija.

    item_rows očekuje listu dict-ova sa: q/p/a ili quantity/unit_price/line_amount.
    """
    if not item_rows:
        return {
            "triggered": False,
            "verdict": "FALSE",
            "eligible_rows": 0,
            "failed_rows": 0,
            "failed_rate": 0.0,
            "severe_mismatches": 0,
            "per_row": [],
            "reason": "no_data",
        }
    per_row = []
    failed = 0
    severe = 0
    for raw in item_rows:
        norm = _normalize_row(raw)
        if norm is None:
            per_row.append({"pass": False, "reason": "invalid_input", "input": raw})
            failed += 1
            continue
        try:
            q = float(norm["q"])
            p = float(norm["p"])
            a = float(norm["a"])
        except (ValueError, TypeError):
            per_row.append({"pass": False, "reason": "invalid_input", "input": raw})
            failed += 1
            continue
        discount = norm.get("discount")
        if discount is not None:
            try:
                discount = float(discount)
            except (ValueError, TypeError):
                discount = None
        result = evaluate_f10_row(q, p, a, discount)
        per_row.append(result)
        if not result["pass"]:
            failed += 1
        if result["severe_mismatch"]:
            severe += 1
    eligible = len(item_rows)
    rate = failed / max(eligible, 1)
    f10_true = eligible >= 5 and failed >= 2 and rate > 0.20
    f10_true = f10_true or severe >= 2
    return {
        "triggered": f10_true,
        "verdict": "TRUE" if f10_true else "FALSE",
        "eligible_rows": eligible,
        "failed_rows": failed,
        "failed_rate": round(rate, 4),
        "severe_mismatches": severe,
        "per_row": per_row,
        "reason": "math_inconsistency" if f10_true else "math_consistent",
    }

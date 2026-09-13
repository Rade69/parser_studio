"""Character accuracy test (TEST 2) — koristi Docling markdown output (bez ponovnog učitavanja modela).

Ground-truth koristi vrijednosti iz GROUND_TRUTH_CANDIDATE JSON-ova.
"""
import sys
import os
import json
import re
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

GT_DIR = Path("H:/parser_studio/tests/fakture_ground_truth")
MD_DIR = Path("H:/parser_studio/experiments/document_engines/outputs")
OUT = Path("H:/parser_studio/experiments/document_engines/quality_v3/character_tests")
OUT.mkdir(parents=True, exist_ok=True)


def gt_to_expected(gt_row):
    fields = {
        "description": gt_row.get("description", ""),
        "quantity": str(gt_row.get("quantity", "")),
        "unit_price": str(gt_row.get("unit_price", "")),
        "line_amount": str(gt_row.get("line_amount", "")),
        "unit": gt_row.get("unit_of_measure_normalized", gt_row.get("unit_of_measure_raw", "")),
        "country": gt_row.get("country_raw", ""),
        "tariff": gt_row.get("tariff", ""),
    }
    return fields


def find_in_text(md_text, gt_fields):
    text_norm = re.sub(r"\s+", " ", md_text.lower())
    found = {}
    for field_name, value in gt_fields.items():
        if not value:
            found[field_name] = {"found": False, "value": ""}
            continue
        value_norm = re.sub(r"\s+", " ", str(value).lower())
        if value_norm in text_norm:
            found[field_name] = {"found": True, "value": str(value)}
        else:
            value_alt = value_norm.replace(",", ".").replace(".", ",")
            if value_alt in text_norm:
                found[field_name] = {"found": True, "value": str(value) + " (alt format)"}
            else:
                num_match = re.search(r"\d+[.,]?\d*", value_norm)
                if num_match and num_match.group() in text_norm:
                    found[field_name] = {"found": True, "value": str(value) + " (partial)"}
                else:
                    found[field_name] = {"found": False, "value": str(value)}
    return found


def critical_chars_check(gt_value, found_value):
    issues = []
    if "0" in str(gt_value) and "O" in str(found_value):
        issues.append("0→O")
    if "O" in str(gt_value) and "0" in str(found_value):
        issues.append("O→0")
    if "1" in str(gt_value) and re.search(r"[Il]", str(found_value)):
        issues.append("1→I/l")
    if re.search(r"[Il]", str(gt_value)) and "1" in str(found_value):
        issues.append("I/l→1")
    if "," in str(gt_value) and "." in str(found_value):
        issues.append(",→.")
    if "." in str(gt_value) and "," in str(found_value):
        issues.append(".→,")
    return issues


def main():
    pdf_name = sys.argv[1] if len(sys.argv) > 1 else "Sumaprom.pdf"
    gt_path = GT_DIR / f"{pdf_name.replace('.pdf', '')}_ground_truth.json"
    md_path = MD_DIR / f"{pdf_name.replace('.pdf', '')}.docling.md"
    if not gt_path.exists():
        print(f"NO GT for {pdf_name}", flush=True)
        return
    if not md_path.exists():
        print(f"NO MD for {pdf_name}", flush=True)
        return
    with open(gt_path, "r", encoding="utf-8") as f:
        gt = json.load(f)
    md_text = md_path.read_text(encoding="utf-8")
    rows = gt.get("rows", [])
    if not rows:
        print(f"{pdf_name}: no rows in GT", flush=True)
        return
    print(f"=== {pdf_name}: {len(rows)} GT rows ===", flush=True)
    per_row = []
    for r in rows:
        expected = gt_to_expected(r)
        found = find_in_text(md_text, expected)
        critical_issues = {}
        for fname, info in found.items():
            if fname in ("description", "country", "unit"):
                # Check critical chars in found value
                fv = info.get("value", "")
                if info.get("found"):
                    ci = critical_chars_check(expected[fname], fv)
                    if ci:
                        critical_issues[fname] = ci
        per_row.append({
            "row": r.get("row"),
            "expected": expected,
            "found": found,
            "critical_issues": critical_issues,
        })
        found_count = sum(1 for f in found.values() if f.get("found"))
        total_count = len(found)
        print(f"  row {r.get('row')}: {found_count}/{total_count} fields found", flush=True)
    summary = {
        "pdf": pdf_name,
        "n_rows": len(rows),
        "per_row": per_row,
    }
    total_fields = 0
    found_fields = 0
    for pr in per_row:
        for fname, info in pr["found"].items():
            total_fields += 1
            if info.get("found"):
                found_fields += 1
    summary["aggregate"] = {
        "total_fields": total_fields,
        "found_fields": found_fields,
        "field_match_rate": round(found_fields / max(total_fields, 1), 4),
        "by_field": {},
    }
    for fname in ["description", "quantity", "unit_price", "line_amount", "unit", "country"]:
        f_total = sum(1 for pr in per_row if fname in pr["found"])
        f_found = sum(1 for pr in per_row if pr["found"].get(fname, {}).get("found"))
        summary["aggregate"]["by_field"][fname] = {
            "found": f_found,
            "total": f_total,
            "rate": round(f_found / max(f_total, 1), 4),
        }
    out_path = OUT / f"character_test_{pdf_name.replace('.pdf', '')}.json"
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved: {out_path}", flush=True)
    print(f"AGGREGATE: {found_fields}/{total_fields} = {summary['aggregate']['field_match_rate']}", flush=True)


if __name__ == "__main__":
    main()

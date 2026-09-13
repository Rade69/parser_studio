"""Character accuracy test (TEST 2) — OCR kritičnih karaktera.

Ground-truth koristi vrijednosti iz GROUND_TRUTH_CANDIDATE JSON-ova.
POTVRĐENO TESTOM samo za one redove gdje je GT ručno potvrđen.
Za ostale je PROCJENA.
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

from docling.document_converter import DocumentConverter

GT_DIR = Path("H:/parser_studio/tests/fakture_ground_truth")
OUT = Path("H:/parser_studio/experiments/document_engines/quality_v3/character_tests")
OUT.mkdir(parents=True, exist_ok=True)


# Mapiranje GT -> očekivani karakteri
def gt_to_expected(gt_row):
    """Iz GT reda izvuci očekivane znakove (description, quantity, unit_price, line_amount, unit)."""
    fields = {
        "description": gt_row.get("description", ""),
        "quantity": str(gt_row.get("quantity", "")),
        "unit_price": str(gt_row.get("unit_price", "")),
        "line_amount": str(gt_row.get("line_amount", "")),
        "unit": gt_row.get("unit_of_measure_normalized", gt_row.get("unit_of_measure_raw", "")),
        "country": gt_row.get("country_raw", ""),
    }
    return fields


def find_in_docling_text(doc, gt_fields):
    """Traži GT vrijednost u Docling output teksta (case-insensitive, normalize spaces)."""
    try:
        text = doc.export_to_text()
    except Exception:
        text = ""
    text_norm = re.sub(r"\s+", " ", text.lower())
    found = {}
    for field_name, value in gt_fields.items():
        if not value:
            found[field_name] = {"found": False, "value": ""}
            continue
        # Normalizuj GT vrijednost
        value_norm = re.sub(r"\s+", " ", str(value).lower())
        # Traži substring
        if value_norm in text_norm:
            found[field_name] = {"found": True, "value": str(value)}
        else:
            # Probaj sa zarezom umjesto tačke i obrnuto
            value_alt = value_norm.replace(",", ".").replace(".", ",")
            if value_alt in text_norm:
                found[field_name] = {"found": True, "value": str(value) + " (alt format)"}
            else:
                # Probaj samo numerički dio
                num_match = re.search(r"\d+[.,]?\d*", value_norm)
                if num_match and num_match.group() in text_norm:
                    found[field_name] = {"found": True, "value": str(value) + " (partial)"}
                else:
                    found[field_name] = {"found": False, "value": str(value)}
    return found


def critical_chars_check(gt_value, docling_value):
    """Provjerava da li kritični karakteri preživljavaju OCR."""
    issues = []
    # 0 vs O
    if "0" in str(gt_value) and "O" in str(docling_value):
        issues.append("0→O")
    # O vs 0
    if "O" in str(gt_value) and "0" in str(docling_value):
        issues.append("O→0")
    # 1 vs I/l
    if "1" in str(gt_value) and re.search(r"[Il]", str(docling_value)):
        issues.append("1→I/l")
    # I/l vs 1
    if re.search(r"[Il]", str(gt_value)) and "1" in str(docling_value):
        issues.append("I/l→1")
    # decimalni zarez vs tačka
    if "," in str(gt_value) and "." in str(docling_value):
        issues.append(",→.")
    # tačka vs zarez
    if "." in str(gt_value) and "," in str(docling_value):
        issues.append(".→,")
    return issues


def main():
    pdf_name = sys.argv[1] if len(sys.argv) > 1 else "Sumaprom.pdf"
    gt_path = GT_DIR / f"{pdf_name.replace('.pdf', '')}_ground_truth.json"
    if not gt_path.exists():
        print(f"NO GT for {pdf_name}", flush=True)
        return
    with open(gt_path, "r", encoding="utf-8") as f:
        gt = json.load(f)
    rows = gt.get("rows", [])
    if not rows:
        print(f"{pdf_name}: no rows in GT", flush=True)
        return
    pdf_path = Path(f"H:/parser_studio/tests/fakture/{pdf_name}")
    print(f"=== {pdf_name}: {len(rows)} GT rows ===", flush=True)
    converter = DocumentConverter()
    result = converter.convert(str(pdf_path))
    doc = result.document
    per_row = []
    for r in rows:
        expected = gt_to_expected(r)
        found = find_in_docling_text(doc, expected)
        # Critical char issues
        critical_issues = {}
        for f, info in found.items():
            docling_text = doc.export_to_text() if hasattr(doc, "export_to_text") else ""
            # Heuristika: extrahiraj dio dokumenta koji matchuje description
            if f == "description":
                issues = critical_chars_check(expected[f], info.get("value", ""))
                if issues:
                    critical_issues[f] = issues
        per_row.append({
            "row": r.get("row"),
            "expected": expected,
            "found": found,
            "critical_issues": critical_issues,
        })
        # Print summary
        found_count = sum(1 for f in found.values() if f.get("found"))
        total_count = len(found)
        print(f"  row {r.get('row')}: {found_count}/{total_count} fields found", flush=True)
    summary = {
        "pdf": pdf_name,
        "n_rows": len(rows),
        "per_row": per_row,
    }
    # Aggregate
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

"""F6-F10 quality gate evaluacija.

F6 = tekst kompletan (broj prepoznatih riječi naspram heuristike)
F7 = reading order logičan (Docling ima strukturu, PaddleOCR ima Y-rastući redoslijed)
F8 = tabele strukturirane (broj detektovanih tabela i ćelija)
F9 = bounding boxes / poligoni prisutni
F10 = numerička konzistentnost (qty × price ≈ amount)
"""
import json
import re
from pathlib import Path

OUT = Path("H:/parser_studio/experiments/document_engines/outputs")
PDFS = ["Faktura-1.pdf", "Faktura-2.pdf", "Medicopharm.pdf", "Sumaprom.pdf"]


def load_docling_md(name):
    md_path = OUT / f"{name.replace('.pdf', '')}.docling.md"
    return md_path.read_text(encoding="utf-8") if md_path.exists() else None


def load_paddle_text(name):
    pages = []
    for page_path in sorted(OUT.glob(f"{name.replace('.pdf', '')}.paddle.page*.txt")):
        pages.append(page_path.read_text(encoding="utf-8"))
    return pages


def eval_f6(name, docling_md, paddle_pages):
    """F6: da li je tekst kompletan? Heuristika: broj riječi."""
    d_words = len(re.findall(r"\S+", docling_md)) if docling_md else 0
    p_words = sum(len(re.findall(r"\S+", p)) for p in paddle_pages)
    return {
        "docling_words": d_words,
        "paddle_words": p_words,
        "ratio": round(p_words / max(d_words, 1), 2),
        "verdict": "PASS" if d_words > 50 and p_words > 50 else "FAIL",
    }


def eval_f7(name, docling_md, paddle_pages):
    """F7: reading order. Docling eksportuje strukturiran markdown; PaddleOCR nema layout order."""
    has_struct = docling_md and ("# " in docling_md or "| " in docling_md)
    has_order = len(paddle_pages) > 0
    return {
        "docling_structured": has_struct,
        "paddle_ordered": has_order,
        "verdict": "PASS" if has_struct else "PARTIAL",
    }


def eval_f8(name, docling_md):
    """F8: tabele strukturirane."""
    n_md_tables = docling_md.count("|") if docling_md else 0
    return {
        "docling_table_lines": n_md_tables,
        "verdict": "PASS" if n_md_tables > 5 else "FAIL",
    }


def eval_f9(name):
    """F9: poligoni. PaddleOCR ih ima; Docling nema eksportovane u MD."""
    poly_count = 0
    for json_path in OUT.glob("*.paddle.json"):
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            poly_count += len(data.get("res", {}).get("rec_polys", []))
        except Exception:
            pass
    return {
        "paddle_polygons": poly_count,
        "verdict": "PASS" if poly_count > 0 else "FAIL",
    }


# F10 — pokušaj računske provjere
NUMBER_RE = re.compile(r"\d+[.,]?\d*")


def try_extract_lines(md_text):
    """Heuristika: nađi redove u markdown-u koji sadrže 3+ broja (količina, cijena, iznos)."""
    if not md_text:
        return []
    rows = []
    for line in md_text.splitlines():
        nums = NUMBER_RE.findall(line.replace(".", "").replace(",", "."))
        if len(nums) >= 3:
            try:
                vals = [float(n) for n in nums[-4:]]
                rows.append(vals)
            except ValueError:
                pass
    return rows


def eval_f10(name, docling_md):
    """F10: qty × price ≈ amount."""
    rows = try_extract_lines(docling_md)
    matches = 0
    mismatches = 0
    examples = []
    for r in rows:
        if len(r) < 3:
            continue
        # Pretpostavka: qty, unit_price, amount (zadnja 3)
        for triple in (r[-3:], r):
            if len(triple) >= 3:
                qty, price, amount = triple[0], triple[1], triple[2]
                if qty > 0 and price > 0:
                    expected = round(qty * price, 2)
                    if abs(expected - amount) < 0.5:
                        matches += 1
                        if len(examples) < 3:
                            examples.append({"qty": qty, "price": price, "amount": amount, "ok": True})
                        break
                    else:
                        mismatches += 1
                        if len(examples) < 3:
                            examples.append({"qty": qty, "price": price, "amount": amount, "expected": expected, "ok": False})
                        break
    return {
        "rows_with_3_numbers": len(rows),
        "matches": matches,
        "mismatches": mismatches,
        "examples": examples,
        "verdict": "PASS" if matches > 0 and mismatches == 0 else ("PARTIAL" if matches > 0 else "FAIL"),
    }


def main():
    summary = {"system": "F6-F10 evaluacija nad benchmark outputima"}
    per_pdf = {}
    for pdf in PDFS:
        docling_md = load_docling_md(pdf)
        paddle_pages = load_paddle_text(pdf)
        per_pdf[pdf] = {
            "F6_text_complete": eval_f6(pdf, docling_md, paddle_pages),
            "F7_reading_order": eval_f7(pdf, docling_md, paddle_pages),
            "F8_tables_structured": eval_f8(pdf, docling_md),
            "F9_bboxes_polygons": eval_f9(pdf),
            "F10_numeric_consistency": eval_f10(pdf, docling_md),
        }
    summary["per_pdf"] = per_pdf
    out_path = OUT / "f6_f10_evaluation.json"
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved: {out_path}")


if __name__ == "__main__":
    main()

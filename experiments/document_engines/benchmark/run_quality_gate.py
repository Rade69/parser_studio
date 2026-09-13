"""Quality Gate runner — pokreće F6-F10 evaluaciju nad stvarnim Docling strukturama.

NE koristi markdown tekst. Radi sa TableCell objektima.
"""
import json
import sys
import os
from pathlib import Path
from typing import Any

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from docling.document_converter import DocumentConverter

from quality_gate import (
    evaluate_f6,
    evaluate_f7,
    evaluate_f8,
    evaluate_f9,
    evaluate_f10,
    parse_number,
    normalize_text,
)


INVOICES = Path("H:/parser_studio/tests/fakture")
OUT = Path("H:/parser_studio/experiments/document_engines/outputs")
GT_DIR = Path("H:/parser_studio/tests/fakture_ground_truth")


def cells_to_grid(table_data) -> tuple[list[list[dict]], list[dict]]:
    """Pretvori TableData.table_cells u grid (rows x cols) + header_cells."""
    cells = list(table_data.table_cells or [])
    if not cells:
        return [], []
    header_cells = [c for c in cells if getattr(c, "column_header", False)]
    # Izračunaj max col_idx i row_idx
    max_col = 0
    max_row = 0
    for c in cells:
        ec = getattr(c, "end_col_offset_idx", None) or 0
        er = getattr(c, "end_row_offset_idx", None) or 0
        if ec > max_col:
            max_col = ec
        if er > max_row:
            max_row = er
    grid: list[list[dict]] = [[{"text": "", "col": c, "row": r, "is_header": False}
                                for c in range(max_col)] for r in range(max_row)]
    for c in cells:
        sc = getattr(c, "start_col_offset_idx", 0) or 0
        sr = getattr(c, "start_row_offset_idx", 0) or 0
        ec = getattr(c, "end_col_offset_idx", sc) or sc
        er = getattr(c, "end_row_offset_idx", sr) or sr
        bbox = getattr(c, "bbox", None)
        bbox_dict = None
        if bbox is not None:
            try:
                # BoundingBox objekat ima .l, .t, .r, .b (ili x0, y0, x1, y1)
                bbox_dict = {
                    "x0": getattr(bbox, "l", None) if hasattr(bbox, "l") else getattr(bbox, "x0", None),
                    "y0": getattr(bbox, "t", None) if hasattr(bbox, "t") else getattr(bbox, "y0", None),
                    "x1": getattr(bbox, "r", None) if hasattr(bbox, "r") else getattr(bbox, "x1", None),
                    "y1": getattr(bbox, "b", None) if hasattr(bbox, "b") else getattr(bbox, "y1", None),
                }
            except Exception:
                bbox_dict = None
        for r in range(sr, er):
            for col in range(sc, ec):
                if r < max_row and col < max_col:
                    grid[r][col] = {
                        "text": getattr(c, "text", "") or "",
                        "col": col,
                        "row": r,
                        "is_header": getattr(c, "column_header", False),
                        "bbox": bbox_dict,
                    }
    return grid, header_cells


def grid_to_columns(grid: list[list[dict]]) -> list[dict]:
    """Pretvori grid u listu kolona (preslikavanje po col indexu).
    Preskoči header red (row 0) za cells.
    """
    if not grid:
        return []
    n_cols = len(grid[0])
    columns = [{"header_text": "", "cells": []} for _ in range(n_cols)]
    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            text = cell.get("text", "") or ""
            if r == 0:
                # Header
                columns[c]["header_text"] = (columns[c]["header_text"] + " " + text).strip()
            else:
                columns[c]["cells"].append(text)
    return columns


def grid_to_rows(grid: list[list[dict]]) -> list[list[dict]]:
    """Vrati retke BEZ headera, sa ćelijama koje imaju bbox."""
    if not grid:
        return []
    return [row for row in grid[1:] if any((c.get("text", "") or "").strip() for c in row)]


def get_table_text_body(doc) -> str:
    """Puni Docling body tekst za F6 heuristiku."""
    try:
        return doc.export_to_text()
    except Exception:
        return ""


def load_ground_truth(name: str) -> list[dict] | None:
    """Učitaj ground-truth za PDF (ako postoji)."""
    base = name.replace(".pdf", "")
    path = GT_DIR / f"{base}_ground_truth.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("rows", [])
    except Exception as e:
        print(f"GT load failed for {name}: {e}", flush=True)
        return None


def main():
    converter = DocumentConverter()
    pdfs = sorted(INVOICES.glob("*.pdf"))
    print(f"found {len(pdfs)} PDFs", flush=True)
    results = {}
    for pdf in pdfs:
        print(f"--- {pdf.name} ---", flush=True)
        r = converter.convert(str(pdf))
        doc = r.document
        n_tables = len(list(doc.tables))
        body_text = get_table_text_body(doc)
        # F6
        f6 = evaluate_f6(n_tables, body_text)
        print(f"  F6: {f6['verdict']} (tables={n_tables}, candidates={f6.get('candidate_lines', 0)})", flush=True)
        # Koristimo prvu tablu
        if n_tables == 0:
            results[pdf.name] = {
                "n_tables": 0,
                "F6": f6,
                "F7": {"triggered": True, "verdict": "TRUE", "reason": "no_tables"},
                "F8": {"triggered": True, "verdict": "TRUE", "reason": "no_tables"},
                "F9": {"triggered": False, "verdict": "FALSE", "reason": "no_tables"},
                "F10": {"triggered": False, "verdict": "FALSE", "reason": "no_tables"},
            }
            continue
        first_table = list(doc.tables)[0]
        grid, headers = cells_to_grid(first_table.data)
        columns = grid_to_columns(grid)
        rows = grid_to_rows(grid)
        # F7
        f7 = evaluate_f7(columns)
        print(f"  F7: {f7['verdict']} (best={f7['best_score']}, margin={f7['margin']})", flush=True)
        # F8
        f8 = evaluate_f8(columns)
        print(f"  F8: {f8['verdict']} qty={f8['quantity']} price={f8['unit_price']} amount={f8['line_amount']} (n_numeric_cols={f8['n_numeric_columns']})", flush=True)
        # F9
        # Ako nemamo ground-truth, koristimo column_x_centers iz bbox-ova
        col_x_centers = {}
        for col_idx, col in enumerate(columns):
            xs = []
            for r in rows:
                if col_idx < len(r) and r[col_idx].get("bbox"):
                    bb = r[col_idx]["bbox"]
                    if bb.get("x0") is not None and bb.get("x1") is not None:
                        xs.append((bb["x0"] + bb["x1"]) / 2)
            if xs:
                col_x_centers[f"col_{col_idx}"] = sum(xs) / len(xs)
        f9_input = {
            "rows": rows,
            "expected_columns": ["quantity", "unit_price", "line_amount"],
            "column_x_centers": col_x_centers,
        }
        f9 = evaluate_f9(f9_input)
        print(f"  F9: {f9['verdict']} broken={f9['broken_rows']}/{f9['analyzable_rows']} rate={f9['broken_rate']}", flush=True)
        # F10
        gt_rows = load_ground_truth(pdf.name)
        if gt_rows:
            f10 = evaluate_f10(gt_rows)
            print(f"  F10 (GT): {f10['verdict']} failed={f10['failed_rows']}/{f10['eligible_rows']}", flush=True)
        else:
            # Fallback: pokušaj izvući iz reda grid (heuristika)
            f10 = {"triggered": False, "verdict": "FALSE", "reason": "no_ground_truth", "eligible_rows": 0}
            print(f"  F10: FALSE (no ground-truth)", flush=True)
        results[pdf.name] = {
            "n_tables": n_tables,
            "n_rows": len(rows),
            "n_cols": len(columns),
            "F6": f6,
            "F7": f7,
            "F8": f8,
            "F9": f9,
            "F10": f10,
        }
    out_path = OUT / "quality_gate_v2.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved: {out_path}", flush=True)


if __name__ == "__main__":
    main()

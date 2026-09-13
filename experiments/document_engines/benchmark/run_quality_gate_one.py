"""Quality Gate runner — samo za jedan PDF (za retry bez Medicopharm OOM-a)."""
import sys
import os
import json
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from docling.document_converter import DocumentConverter
import sys as _sys
_sys.path.insert(0, str(Path(__file__).parent))
from quality_gate import (
    evaluate_f6, evaluate_f7, evaluate_f8, evaluate_f9, evaluate_f10,
    parse_number,
)


def cells_to_grid(table_data):
    cells = list(table_data.table_cells or [])
    if not cells:
        return [], []
    max_col = 0
    max_row = 0
    for c in cells:
        ec = getattr(c, "end_col_offset_idx", None) or 0
        er = getattr(c, "end_row_offset_idx", None) or 0
        if ec > max_col:
            max_col = ec
        if er > max_row:
            max_row = er
    grid = [[{"text": "", "col": c, "row": r, "is_header": False}
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
                        "col": col, "row": r,
                        "is_header": getattr(c, "column_header", False),
                        "bbox": bbox_dict,
                    }
    return grid, []


def grid_to_columns(grid):
    if not grid:
        return []
    n_cols = len(grid[0])
    cols = [{"header_text": "", "cells": []} for _ in range(n_cols)]
    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            text = cell.get("text", "") or ""
            if r == 0:
                cols[c]["header_text"] = (cols[c]["header_text"] + " " + text).strip()
            else:
                cols[c]["cells"].append(text)
    return cols


def grid_to_rows(grid):
    if not grid:
        return []
    return [row for row in grid[1:] if any((c.get("text", "") or "").strip() for c in row)]


def load_gt(name):
    base = name.replace(".pdf", "")
    path = Path(f"H:/parser_studio/tests/fakture_ground_truth/{base}_ground_truth.json")
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("rows", [])
    except Exception:
        return None


def run(pdf_name):
    OUT = Path("H:/parser_studio/experiments/document_engines/outputs")
    converter = DocumentConverter()
    pdf_path = Path(f"H:/parser_studio/tests/fakture/{pdf_name}")
    print(f"--- {pdf_name} ---", flush=True)
    r = converter.convert(str(pdf_path))
    doc = r.document
    n_tables = len(list(doc.tables))
    body_text = doc.export_to_text() if hasattr(doc, "export_to_text") else ""
    f6 = evaluate_f6(n_tables, body_text)
    print(f"  F6: {f6['verdict']}", flush=True)
    if n_tables == 0:
        return {"F6": f6, "F7": {"triggered": True, "verdict": "TRUE"}, "F8": {"triggered": True, "verdict": "TRUE"}}
    first_table = list(doc.tables)[0]
    grid, _ = cells_to_grid(first_table.data)
    columns = grid_to_columns(grid)
    rows = grid_to_rows(grid)
    f7 = evaluate_f7(columns)
    print(f"  F7: {f7['verdict']} best={f7['best_score']}", flush=True)
    f8 = evaluate_f8(columns)
    print(f"  F8: {f8['verdict']} qty={f8['quantity']}", flush=True)
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
    f9 = evaluate_f9({
        "rows": rows,
        "expected_columns": ["quantity", "unit_price", "line_amount"],
        "column_x_centers": col_x_centers,
    })
    print(f"  F9: {f9['verdict']} broken={f9['broken_rows']}/{f9['analyzable_rows']}", flush=True)
    gt_rows = load_gt(pdf_name)
    if gt_rows:
        f10 = evaluate_f10(gt_rows)
        print(f"  F10: {f10['verdict']} failed={f10['failed_rows']}/{f10['eligible_rows']} severe={f10['severe_mismatches']}", flush=True)
    else:
        f10 = {"triggered": False, "verdict": "FALSE", "reason": "no_ground_truth"}
        print(f"  F10: FALSE (no GT)", flush=True)
    return {"F6": f6, "F7": f7, "F8": f8, "F9": f9, "F10": f10, "n_tables": n_tables, "n_rows": len(rows), "n_cols": len(columns)}


if __name__ == "__main__":
    pdf_name = sys.argv[1] if len(sys.argv) > 1 else "Sumaprom.pdf"
    result = run(pdf_name)
    OUT = Path("H:/parser_studio/experiments/document_engines/outputs")
    safe_name = pdf_name.replace(".pdf", "")
    out_path = OUT / f"quality_gate_{safe_name}.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved: {out_path}", flush=True)

"""Benchmark runner — Docling vs PaddleOCR (flat).

PP-StructureV3 je blocked na Windows CPU (predict deadlock nakon model load).
Koristimo PaddleOCR flat kao baseline — vraća OCR sa rec_polys, rec_texts, rec_scores.
Nema layout detekciju ni table recognition.
"""
import sys
import time
import json
import gc
import os
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

INVOICES = Path("H:/parser_studio/tests/fakture")
OUT = Path("H:/parser_studio/experiments/document_engines/outputs")
OUT.mkdir(parents=True, exist_ok=True)

PDFS = sorted(INVOICES.glob("*.pdf"))
print(f"found {len(PDFS)} PDFs", flush=True)


def measure(fn):
    gc.collect()
    t0 = time.perf_counter()
    err = None
    result = None
    try:
        result = fn()
    except Exception as e:
        import traceback
        err = f"{type(e).__name__}: {e}"
        traceback.print_exc()
    elapsed = time.perf_counter() - t0
    return elapsed, err, result


# ─── Docling ─────────────────────────────────────────────
print("=== Docling ===", flush=True)
def run_docling_all():
    from docling.document_converter import DocumentConverter
    converter = DocumentConverter()
    out = {}
    for pdf in PDFS:
        t0 = time.perf_counter()
        result = converter.convert(str(pdf))
        elapsed = time.perf_counter() - t0
        doc = result.document
        md = doc.export_to_markdown()
        n_tables = len(list(doc.tables))
        n_pages = len(list(doc.pages))
        out[pdf.name] = {
            "elapsed_s": round(elapsed, 2),
            "markdown_chars": len(md),
            "tables": n_tables,
            "pages": n_pages,
        }
        (OUT / f"{pdf.stem}.docling.md").write_text(md, encoding="utf-8")
        print(f"  {pdf.name}: {elapsed:.1f}s, {len(md)} chars, {n_tables} tables, {n_pages} pages", flush=True)
    return out


docling_elapsed, docling_err, docling_result = measure(run_docling_all)
print(f"Docling total: {docling_elapsed:.1f}s, error={docling_err}", flush=True)


# ─── PaddleOCR (flat baseline) ──────────────────────────
print("=== PaddleOCR flat ===", flush=True)
def run_paddle_all():
    import pypdfium2 as pdfium
    from paddleocr import PaddleOCR
    t = time.perf_counter()
    ocr = PaddleOCR(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        lang="en",
    )
    print(f"  PaddleOCR init: {time.perf_counter()-t:.2f}s", flush=True)
    out = {}
    for pdf in PDFS:
        pages_data = []
        for page_idx, page in enumerate(pdfium.PdfDocument(str(pdf))):
            img_path = OUT / f"{pdf.stem}.paddle.page{page_idx+1}.png"
            page.render(scale=2.0).to_pil().save(img_path)
            t0 = time.perf_counter()
            results = ocr.predict(str(img_path))
            elapsed = time.perf_counter() - t0
            r = results[0]
            data = r.json if hasattr(r, "json") else {}
            res = data.get("res", data) if isinstance(data, dict) else {}
            texts = res.get("rec_texts", []) or []
            scores = res.get("rec_scores", []) or []
            polys = res.get("rec_polys", []) or []
            pages_data.append({
                "page": page_idx + 1,
                "elapsed_s": round(elapsed, 2),
                "n_text_lines": len(texts),
                "n_polygons": len(polys),
                "mean_confidence": round(sum(scores) / max(len(scores), 1), 4) if scores else 0,
                "first_5_lines": [t for t in texts[:5]],
            })
            # sacuvaj flat tekst
            flat_txt = "\n".join(texts)
            (OUT / f"{pdf.stem}.paddle.page{page_idx+1}.txt").write_text(flat_txt, encoding="utf-8")
        out[pdf.name] = {"pages": pages_data, "n_text_lines_total": sum(p["n_text_lines"] for p in pages_data)}
        total_lines = out[pdf.name]["n_text_lines_total"]
        print(f"  {pdf.name}: {sum(p['elapsed_s'] for p in pages_data):.1f}s, {total_lines} lines, {len(pages_data)} pages", flush=True)
    return out


paddle_elapsed, paddle_err, paddle_result = measure(run_paddle_all)
print(f"PaddleOCR total: {paddle_elapsed:.1f}s, error={paddle_err}", flush=True)


# ─── Sažetak ─────────────────────────────────────────────
report = {
    "system": {
        "python": sys.version.split()[0],
        "n_pdfs": len(PDFS),
        "pdfs": [p.name for p in PDFS],
        "ppstructure_status": "BLOCKED — Windows CPU deadlock nakon model init",
    },
    "docling": {
        "total_elapsed_s": round(docling_elapsed, 2),
        "error": docling_err,
        "per_pdf": docling_result,
    },
    "paddle_ocr_flat": {
        "total_elapsed_s": round(paddle_elapsed, 2),
        "error": paddle_err,
        "per_pdf": paddle_result,
    },
}

(OUT / "benchmark_summary.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print("=== benchmark_summary.json saved ===", flush=True)

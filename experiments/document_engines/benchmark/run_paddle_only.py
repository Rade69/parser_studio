"""PaddleOCR flat benchmark (paddle_env)."""
import sys
import time
import json
import gc
import os
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

INVOICES = Path("H:/parser_studio/tests/fakture")
OUT = Path("H:/parser_studio/experiments/document_engines/outputs")
PDFS = sorted(INVOICES.glob("*.pdf"))
print(f"found {len(PDFS)} PDFs", flush=True)

from paddleocr import PaddleOCR
import pypdfium2 as pdfium

t = time.perf_counter()
ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    lang="en",
)
print(f"init: {time.perf_counter()-t:.2f}s", flush=True)

results = {}
for pdf in PDFS:
    pages = []
    for page_idx, page in enumerate(pdfium.PdfDocument(str(pdf))):
        img = OUT / f"{pdf.stem}.paddle.page{page_idx + 1}.png"
        page.render(scale=2.0).to_pil().save(img)
        t0 = time.perf_counter()
        r = ocr.predict(str(img))
        el = time.perf_counter() - t0
        data = r[0].json if hasattr(r[0], "json") else {}
        res = data.get("res", data) if isinstance(data, dict) else {}
        texts = res.get("rec_texts", []) or []
        scores = res.get("rec_scores", []) or []
        polys = res.get("rec_polys", []) or []
        pages.append({
            "page": page_idx + 1,
            "elapsed_s": round(el, 2),
            "n_text_lines": len(texts),
            "n_polygons": len(polys),
            "mean_conf": round(sum(scores) / max(len(scores), 1), 4) if scores else 0,
        })
        (OUT / f"{pdf.stem}.paddle.page{page_idx + 1}.txt").write_text("\n".join(texts), encoding="utf-8")
    total_lines = sum(p["n_text_lines"] for p in pages)
    total_seconds = sum(p["elapsed_s"] for p in pages)
    results[pdf.name] = {"pages": pages, "total_lines": total_lines}
    print(f"{pdf.name}: {total_seconds:.1f}s, {total_lines} lines, {len(pages)} pages", flush=True)

(OUT / "paddle_benchmark_summary.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
print("paddle_benchmark_summary.json saved", flush=True)

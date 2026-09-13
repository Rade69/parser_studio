"""Inventory jednog PDF-a u zasebnom procesu — za ograničeni RAM."""
import sys
import os
import json
import time
import gc
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import psutil

OUT = Path("H:/parser_studio/experiments/document_engines/quality_v3/raw_extraction")
OUT.mkdir(parents=True, exist_ok=True)


def proc_metrics():
    p = psutil.Process(os.getpid())
    return p.memory_info().rss


def detect_lang(text):
    text_l = text.lower()
    score = {"bs/sr/hr": 0, "en": 0, "de": 0, "mk": 0}
    for w in ["količina", "kolicina", "izvoznik", "uvoznik", "roba", "cijena", "faktura", "ukupno", "bruto", "neto"]:
        if w in text_l:
            score["bs/sr/hr"] += 1
    for w in ["invoice", "exporter", "importer", "total", "amount", "quantity", "weight"]:
        if w in text_l:
            score["en"] += 1
    for w in ["rechnung", "menge", "einzelpreis", "gesamt", "gewicht", "ursprung"]:
        if w in text_l:
            score["de"] += 1
    return max(score, key=score.get) if max(score.values()) > 0 else "unknown"


def has_text_layer(pdf_path):
    try:
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(str(pdf_path))
        textpage = pdf[0].get_textpage()
        n = len(textpage.get_text_range() or "")
        textpage.close()
        return n > 20
    except Exception:
        return False


def page_count(pdf_path):
    try:
        import pypdfium2 as pdfium
        return len(pdfium.PdfDocument(str(pdf_path)))
    except Exception:
        return 0


def convert(pdf_path):
    gc.collect()
    rss_pre = proc_metrics()
    t0 = time.perf_counter()
    from docling.document_converter import DocumentConverter
    converter_t = time.perf_counter() - t0
    t1 = time.perf_counter()
    converter = DocumentConverter()
    converter_init = time.perf_counter() - t1
    rss_after_init = proc_metrics()
    t2 = time.perf_counter()
    try:
        result = converter.convert(str(pdf_path))
        elapsed = time.perf_counter() - t2
        rss_end = proc_metrics()
        doc = result.document
        n_tables = len(list(doc.tables))
        n_pages_doc = len(list(doc.pages))
        n_cells = sum(len(list(t.data.table_cells or [])) for t in doc.tables)
        n_text = 0
        max_t = 0
        all_text = []
        # doc.pages je list page objekata; iterirati sa indeksom
        n_pages_list = list(doc.pages)
        for page_idx in range(len(n_pages_list)):
            page = n_pages_list[page_idx]
            # page objekt ima .iter_items() u novijim verzijama
            iter_method = getattr(page, "iter_items", None) or getattr(page, "iterate_items", None)
            if iter_method is None:
                continue
            try:
                for item, _ in iter_method():
                    if hasattr(item, "text") and item.text:
                        n_text += 1
                        all_text.append(item.text)
                        if len(item.text) > max_t:
                            max_t = len(item.text)
            except Exception:
                continue
        body = "\n".join(all_text[:200])
        return {
            "status": "ok",
            "file": pdf_path.name,
            "size_bytes": pdf_path.stat().st_size,
            "is_digital": has_text_layer(pdf_path),
            "n_pages_pdf": page_count(pdf_path),
            "n_pages_docling": n_pages_doc,
            "n_tables": n_tables,
            "n_cells": n_cells,
            "n_text_items": n_text,
            "max_text_item_len": max_t,
            "elapsed_total_s": round(time.perf_counter() - t0, 2),
            "docling_import_s": round(converter_t, 2),
            "converter_init_s": round(converter_init, 2),
            "convert_s": round(elapsed, 2),
            "rss_pre_mb": round(rss_pre / 1e6, 1),
            "rss_after_init_mb": round(rss_after_init / 1e6, 1),
            "rss_end_mb": round(rss_end / 1e6, 1),
            "language": detect_lang(body),
            "body_sample": body[:500],
        }
    except Exception as e:
        return {
            "status": "error",
            "file": pdf_path.name,
            "error": f"{type(e).__name__}: {e}",
            "elapsed_total_s": round(time.perf_counter() - t0, 2),
            "rss_pre_mb": round(rss_pre / 1e6, 1),
        }


if __name__ == "__main__":
    pdf_name = sys.argv[1]
    pdf = Path(f"H:/parser_studio/tests/fakture/{pdf_name}")
    result = convert(pdf)
    out_path = OUT / f"inventory_{pdf_name.replace('.pdf', '')}.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"saved: {out_path}", flush=True)

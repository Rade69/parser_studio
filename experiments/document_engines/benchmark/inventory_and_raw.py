"""Inventory + Raw Docling Extraction (TEST 1).

Za svaku fakturu:
- konverzija sa Docling
- mjerenje: vrijeme (cold + warm), RAM (RSS), broj stranica, tabela, ćelija
- strukturirani output (DoclingDocument JSON)
"""
import sys
import os
import json
import time
import gc
from pathlib import Path
from datetime import datetime

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import psutil

INVOICES = Path("H:/parser_studio/tests/fakture")
OUT = Path("H:/parser_studio/experiments/document_engines/quality_v3/raw_extraction")
OUT.mkdir(parents=True, exist_ok=True)


def proc_metrics():
    """Trenutni RSS za ovaj proces."""
    p = psutil.Process(os.getpid())
    return p.memory_info().rss


def detect_lang_from_text(text: str) -> str:
    """Vrlo gruba detekcija jezika."""
    text_l = text.lower()
    score = {"bs/sr/hr": 0, "en": 0, "de": 0, "mk": 0}
    diacritic_words = ["količina", "kolicina", "izvoznik", "uvoznik", "roba", "cijena",
                        "datum", "faktura", "ukupno", "bruto", "neto", "paritet",
                        "iznos", "poreklo", "jedinica"]
    for w in diacritic_words:
        if w in text_l:
            score["bs/sr/hr"] += 1
    en_words = ["invoice", "exporter", "importer", "total", "amount", "quantity",
                "unit price", "shipper", "consignee", "country", "weight"]
    for w in en_words:
        if w in text_l:
            score["en"] += 1
    de_words = ["rechnung", "menge", "einzelpreis", "gesamt", "gewicht", "ursprung"]
    for w in de_words:
        if w in text_l:
            score["de"] += 1
    mk_words = ["датум", "извозник", "вкупна", "количина"]
    for w in mk_words:
        if w in text_l:
            score["mk"] += 1
    best = max(score, key=score.get)
    return best if score[best] > 0 else "unknown"


def has_text_layer(pdf_path: Path) -> bool:
    """Provjeri da li PDF ima vidljiv text (ne scan)."""
    try:
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(str(pdf_path))
        page = pdf[0]
        textpage = page.get_textpage()
        n_chars = len(textpage.get_text_range() or "")
        textpage.close()
        return n_chars > 20
    except Exception:
        return False


def page_count(pdf_path: Path) -> int:
    try:
        import pypdfium2 as pdfium
        return len(pdfium.PdfDocument(str(pdf_path)))
    except Exception:
        return 0


def convert_and_measure(pdf_path: Path, converter):
    """Convert sa Docling i izmjeri metrike."""
    gc.collect()
    rss_start = proc_metrics()
    t0 = time.perf_counter()
    try:
        result = converter.convert(str(pdf_path))
        elapsed = time.perf_counter() - t0
        rss_end = proc_metrics()
        doc = result.document
        n_tables = len(list(doc.tables))
        n_pages = len(list(doc.pages))
        # Broji ćelije i text items
        n_cells = 0
        n_text_items = 0
        max_text_len = 0
        all_text_parts = []
        for t in doc.tables:
            if t.data.table_cells:
                n_cells += len(list(t.data.table_cells))
        for page in doc.pages:
            for item, _ in page.iterate_items():
                if hasattr(item, "text") and item.text:
                    n_text_items += 1
                    all_text_parts.append(item.text)
                    if len(item.text) > max_text_len:
                        max_text_len = len(item.text)
        body_text = "\n".join(all_text_parts[:200])
        return {
            "status": "ok",
            "elapsed_s": round(elapsed, 2),
            "rss_start_mb": round(rss_start / 1e6, 1),
            "rss_end_mb": round(rss_end / 1e6, 1),
            "rss_peak_mb": round(max(rss_start, rss_end) / 1e6, 1),
            "n_pages_docling": n_pages,
            "n_tables": n_tables,
            "n_cells": n_cells,
            "n_text_items": n_text_items,
            "max_text_item_len": max_text_len,
            "body_text_sample": body_text[:500],
        }
    except Exception as e:
        elapsed = time.perf_counter() - t0
        return {"status": "error", "error": f"{type(e).__name__}: {e}", "elapsed_s": round(elapsed, 2)}


def main():
    pdfs = sorted(INVOICES.glob("*.pdf"))
    print(f"=== Inventory + Raw Extraction ({len(pdfs)} PDFs) ===", flush=True)
    inventory = []
    # COLD start — novi proces, sve od nule
    print("COLD: importing Docling...", flush=True)
    cold_t0 = time.perf_counter()
    from docling.document_converter import DocumentConverter
    cold_import_s = time.perf_counter() - cold_t0
    rss_pre_converter = proc_metrics()
    cold_t0 = time.perf_counter()
    converter = DocumentConverter()
    cold_init_s = time.perf_counter() - cold_t0
    print(f"COLD: docling import={cold_import_s:.2f}s, converter init={cold_init_s:.2f}s, rss_pre={rss_pre_converter/1e6:.1f}MB", flush=True)
    for pdf in pdfs:
        # Has text layer
        is_digital = has_text_layer(pdf)
        pages = page_count(pdf)
        # Convert
        m = convert_and_measure(pdf, converter)
        m["file"] = pdf.name
        m["size_bytes"] = pdf.stat().st_size
        m["n_pages_pdf"] = pages
        m["is_digital"] = is_digital
        if m["status"] == "ok":
            lang = detect_lang_from_text(m.get("body_text_sample", ""))
            m["language"] = lang
        inventory.append(m)
        print(f"  {pdf.name}: {m['status']} {m.get('elapsed_s','?')}s, {pages}p, {m.get('n_tables','?')}t, {m.get('n_cells','?')}c, digital={is_digital}, lang={m.get('language','?')}", flush=True)
    # WARM: ponovi sve dokumente u istom procesu
    print("=== WARM re-runs ===", flush=True)
    warm_results = []
    for pdf in pdfs:
        m = convert_and_measure(pdf, converter)
        m["file"] = pdf.name
        warm_results.append(m)
        print(f"  {pdf.name}: warm={m.get('elapsed_s','?')}s, rss_end={m.get('rss_end_mb','?')}MB", flush=True)
    # Save
    summary = {
        "system": {
            "python": sys.version.split()[0],
            "psutil": psutil.__version__,
            "cpu_count_logical": psutil.cpu_count(logical=True),
            "cpu_count_physical": psutil.cpu_count(logical=False),
        },
        "cold_start": {
            "docling_import_s": round(cold_import_s, 2),
            "converter_init_s": round(cold_init_s, 2),
            "rss_pre_converter_mb": round(rss_pre_converter / 1e6, 1),
        },
        "cold_runs": inventory,
        "warm_runs": warm_results,
    }
    out = OUT / "inventory_and_raw.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved: {out}", flush=True)


if __name__ == "__main__":
    main()

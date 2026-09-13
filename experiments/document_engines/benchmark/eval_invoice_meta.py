"""Eval invoice_meta_extractor na 4 fakture."""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from invoice_meta_extractor import extract_invoice_meta

OUT = Path("H:/parser_studio/experiments/document_engines/outputs")
results = {}
for pdf in ["Faktura-1.pdf", "Faktura-2.pdf", "Medicopharm.pdf", "Sumaprom.pdf"]:
    base = pdf.replace(".pdf", "")
    md_path = OUT / f"{base}.docling.md"
    if md_path.exists():
        text = md_path.read_text(encoding="utf-8")
        meta = extract_invoice_meta(text)
        results[pdf] = meta
        print(f"{pdf}: exporter={meta['exporter'] is not None}, invoice_no={meta['invoice_number']}, currency={meta['currency']}, bruto={meta['total_bruto_kg']}, neto={meta['total_neto_kg']}, origin_stmt={meta['has_origin_statement']}", flush=True)

out = Path("H:/parser_studio/experiments/document_engines/quality_v3/raw_extraction/invoice_meta_results.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"saved: {out}", flush=True)

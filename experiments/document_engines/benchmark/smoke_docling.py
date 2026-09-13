"""Docling smoke test — Faktura-1.pdf → Markdown + diagnostics."""
import sys
import time
from pathlib import Path

from docling.document_converter import DocumentConverter

PDF = Path("H:/parser_studio/tests/fakture/Faktura-1.pdf").resolve()
OUT = Path("H:/parser_studio/experiments/document_engines/outputs").resolve()

print(f"python: {sys.version.split()[0]}")
print(f"pdf:    {PDF.name} ({PDF.stat().st_size} bytes)")

start = time.perf_counter()
converter = DocumentConverter()
init_seconds = time.perf_counter() - start
print(f"converter init: {init_seconds:.2f}s")

start = time.perf_counter()
result = converter.convert(str(PDF))
convert_seconds = time.perf_counter() - start
print(f"convert: {convert_seconds:.2f}s")

doc = result.document
print(f"doc type: {type(doc).__name__}")

md = doc.export_to_markdown()
md_path = OUT / "Faktura-1.docling.md"
md_path.write_text(md, encoding="utf-8")
print(f"markdown: {len(md)} chars → {md_path.name}")

pages = list(doc.pages)
print(f"pages: {len(pages)}")

if pages:
    p0 = pages[0]
    size = getattr(p0, "size", None)
    print(f"page 0 size: {size}")

print("DOCLING_SMOKE = PASS")

"""PP-StructureV3 smoke test sa CPU-only opcijama."""
import sys
import time
from pathlib import Path

PDF = Path("H:/parser_studio/tests/fakture/Faktura-1.pdf").resolve()
OUT = Path("H:/parser_studio/experiments/document_engines/outputs").resolve()

print(f"python: {sys.version.split()[0]}")

from paddleocr import PPStructureV3, PPStructureV3Options
import pypdfium2 as pdfium
import json

options = PPStructureV3Options(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    use_table_orientation_classify=False,
    use_seal_recognition=False,
    use_formula_recognition=False,
    use_chart_recognition=False,
    use_region_detection=True,
    use_table_recognition=True,
)

start = time.perf_counter()
# PPStructureV3 — minimalni set argumenata, ostavi default za ostalo
pipeline = PPStructureV3(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
)
init_seconds = time.perf_counter() - start
print(f"PP-StructureV3 init: {init_seconds:.2f}s")

pdf = pdfium.PdfDocument(str(PDF))
img_path = OUT / "Faktura-1.page1.png"
pdf[0].render(scale=2.0).to_pil().save(img_path)

start = time.perf_counter()
results = pipeline.predict(str(img_path))
predict_seconds = time.perf_counter() - start
print(f"predict: {predict_seconds:.2f}s")
print(f"results: {len(results)} page(s)")

r = results[0]
attrs = [a for a in dir(r) if not a.startswith("_")]
print(f"OCRResult attrs: {attrs}")

md = None
if hasattr(r, "markdown"):
    md_obj = r.markdown
    if hasattr(md_obj, "markdown"):
        md = md_obj.markdown
    elif isinstance(md_obj, str):
        md = md_obj
if md:
    (OUT / "Faktura-1.ppstructure.md").write_text(md, encoding="utf-8")
    print(f"markdown saved: {len(md)} chars")
else:
    if hasattr(r, "json"):
        data = r.json
        (OUT / "Faktura-1.ppstructure.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print("json saved")

for cand in ("layout_det_res", "table_res_list", "formula_res_list", "text_det_res", "text_rec_res", "seal_res_list", "chart_res_list", "region_det_res"):
    if hasattr(r, cand):
        v = getattr(r, cand)
        print(f"  {cand}: type={type(v).__name__} len={len(v) if hasattr(v, '__len__') else '?'}")

print("PADDLE_PPSTRUCTURE_SMOKE = PASS")

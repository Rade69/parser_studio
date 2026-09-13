"""Probe Docling TableData strukturu — za sve 4 fakture."""
import sys
import os

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from docling.document_converter import DocumentConverter

UNDERSCORE = "_"
conv = DocumentConverter()
for pdf in ["Faktura-1.pdf", "Faktura-2.pdf", "Medicopharm.pdf", "Sumaprom.pdf"]:
    r = conv.convert(f"H:/parser_studio/tests/fakture/{pdf}")
    doc = r.document
    print(f"=== {pdf} ===", flush=True)
    print(f"tables: {len(list(doc.tables))}", flush=True)
    for i, t in enumerate(doc.tables):
        d = t.data
        attrs = [a for a in dir(d) if not a.startswith(UNDERSCORE)]
        print(f"  table {i}: type={type(d).__name__}", flush=True)
        print(f"  TableData attrs: {attrs}", flush=True)
        # Cell structure
        cells = getattr(d, "table_cells", None)
        if cells is not None:
            print(f"  n_cells: {len(cells)}", flush=True)
            if cells:
                c0 = cells[0]
                print(f"  cell0 type: {type(c0).__name__}", flush=True)
                cell_attrs = [a for a in dir(c0) if not a.startswith(UNDERSCORE)]
                print(f"  cell attrs: {cell_attrs}", flush=True)
        # export_to_dataframe
        try:
            df = t.export_to_dataframe(doc=doc)
            print(f"  df shape: {df.shape}", flush=True)
            print(f"  df columns: {list(df.columns)}", flush=True)
            print(f"  first row: {df.iloc[0].tolist()}", flush=True)
        except Exception as e:
            print(f"  export_to_dataframe failed: {type(e).__name__}: {e}", flush=True)
        print("---", flush=True)

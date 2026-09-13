"""Error handling testovi (TEST 16) — generiše loš PDF i testira Docling.

NE commituj outpute u Git.
"""
import sys
import os
import json
import tempfile
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


OUT = Path("H:/parser_studio/experiments/document_engines/quality_v3/error_handling")
OUT.mkdir(parents=True, exist_ok=True)


def make_empty_pdf(path):
    """Prazan PDF (bez stranica)."""
    from reportlab.pdfgen import canvas
    c = canvas.Canvas(str(path))
    c.showPage()
    c.save()


def make_textless_pdf(path):
    """PDF sa samo slikom (bez text layer-a)."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    c = canvas.Canvas(str(path), pagesize=letter)
    # Crtaj pravougaonik umjesto slike (image drawing izbjegava potrebu za image fajlom)
    c.rect(50, 50, 500, 700, fill=1)
    c.showPage()
    c.save()


def make_single_image_pdf(path):
    """PDF sa jednom slikom (ne-faktura)."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    c = canvas.Canvas(str(path), pagesize=letter)
    c.setFillColorRGB(1, 0, 0)
    c.circle(300, 400, 100, fill=1)
    c.showPage()
    c.save()


def make_pdf_with_text(path, text):
    """Jednostavan PDF sa tekstom."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    c = canvas.Canvas(str(path), pagesize=letter)
    c.drawString(50, 700, text)
    c.showPage()
    c.save()


def make_password_protected_pdf(path, password="test"):
    """PDF zaštićen lozinkom (bez hasla za čitanje)."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    c = canvas.Canvas(str(path), pagesize=letter)
    c.drawString(50, 700, "secret content")
    c.save()
    # reportlab ne podržava encryption; koristimo PyPDF2 ako je dostupan
    try:
        from pypdf import PdfReader, PdfWriter
        reader = PdfReader(str(path))
        writer = PdfWriter()
        writer.append_pages(reader.pages)
        writer.encrypt(password)
        with open(path, "wb") as f:
            writer.write(f)
    except ImportError:
        # ako nema pypdf, ostavljamo nezaštićen
        pass


def make_corrupted_pdf(path):
    """Korumpiran PDF (header oštećen)."""
    # Generiramo validan PDF, pa oštetimo header
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    c = canvas.Canvas(str(path), pagesize=letter)
    c.drawString(50, 700, "Hello")
    c.showPage()
    c.save()
    # Ošteti prvih 8 bajtova
    with open(path, "rb") as f:
        data = f.read()
    corrupted = b"XXXXXXXX" + data[8:]
    with open(path, "wb") as f:
        f.write(corrupted)


def make_truncated_pdf(path):
    """Skraćeni PDF (nepotpuni)."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    c = canvas.Canvas(str(path), pagesize=letter)
    c.drawString(50, 700, "Truncated")
    c.showPage()
    c.save()
    # Skrati na pola
    with open(path, "rb") as f:
        data = f.read()
    with open(path, "wb") as f:
        f.write(data[:len(data) // 2])


def test_docling_on(pdf_path):
    """Testira Docling na PDF-u, hvata izuzetke."""
    import time
    try:
        from docling.document_converter import DocumentConverter
        t0 = time.perf_counter()
        converter = DocumentConverter()
        result = converter.convert(str(pdf_path))
        elapsed = time.perf_counter() - t0
        doc = result.document
        return {
            "file": pdf_path.name,
            "status": "ok",
            "elapsed_s": round(elapsed, 2),
            "n_pages": len(list(doc.pages)),
            "n_tables": len(list(doc.tables)),
        }
    except Exception as e:
        return {
            "file": pdf_path.name,
            "status": "error",
            "error_type": type(e).__name__,
            "error_msg": str(e)[:200],
        }


def main():
    test_cases = [
        ("empty.pdf", make_empty_pdf, "Prazan PDF"),
        ("textless.pdf", make_textless_pdf, "PDF sa samo slikom (bez teksta)"),
        ("single_image.pdf", make_single_image_pdf, "PDF sa jednom slikom"),
        ("simple_text.pdf", lambda p: make_pdf_with_text(p, "Just text"), "Jednostavan tekst"),
        ("password_protected.pdf", lambda p: make_password_protected_pdf(p), "Zaštićen lozinkom"),
        ("corrupted.pdf", make_corrupted_pdf, "Korumpiran header"),
        ("truncated.pdf", make_truncated_pdf, "Skraćen na pola"),
    ]
    results = []
    for fname, gen_func, desc in test_cases:
        path = OUT / fname
        try:
            gen_func(path)
            size = path.stat().st_size if path.exists() else 0
        except Exception as e:
            print(f"FAIL to generate {fname}: {e}", flush=True)
            results.append({"file": fname, "desc": desc, "status": "gen_error", "error": str(e)})
            continue
        if not path.exists() or size == 0:
            results.append({"file": fname, "desc": desc, "status": "gen_empty"})
            continue
        result = test_docling_on(path)
        result["desc"] = desc
        result["file_size"] = size
        results.append(result)
        print(f"{fname}: {result['status']}", flush=True)
    out = OUT / "error_handling_results.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved: {out}", flush=True)


if __name__ == "__main__":
    main()

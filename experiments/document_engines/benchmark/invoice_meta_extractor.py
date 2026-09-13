"""Invoice-level metadata extractor (sekcija 12).

Ekstrahira iz Docling markdown:
- exporter / importer (party)
- invoice number
- invoice date
- currency
- Incoterm
- bruto / neto kg ukupno
- origin statement

NE production kod.
"""
from __future__ import annotations
import re
from typing import Optional
from dataclasses import dataclass, asdict


@dataclass
class InvoiceMeta:
    exporter: Optional[str] = None
    importer: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    currency: Optional[str] = None
    incoterm: Optional[str] = None
    total_bruto_kg: Optional[float] = None
    total_neto_kg: Optional[float] = None
    origin_statement: Optional[str] = None
    has_origin_statement: bool = False
    status: dict = None


def _find_value_after_label(text: str, label_pattern: str) -> Optional[str]:
    """Nađi vrijednost nakon labele — dozvoljava prazne redove između."""
    m = re.search(label_pattern + r"\s*\n+\s*([^\n]+)", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return None


def extract_invoice_meta(md_text: str) -> dict:
    """Ekstrahira invoice-level metadata iz Docling markdown."""
    meta = {
        "exporter": None,
        "importer": None,
        "invoice_number": None,
        "invoice_date": None,
        "currency": None,
        "incoterm": None,
        "total_bruto_kg": None,
        "total_neto_kg": None,
        "origin_statement": None,
        "has_origin_statement": False,
        "status": {},
    }
    text = md_text
    # EXPORTER
    val = _find_value_after_label(text, r"(?:Izvoznik|Exporter|Shipper)[^\n]*")
    if val:
        meta["exporter"] = val
        meta["status"]["exporter"] = "FOUND"
    else:
        meta["status"]["exporter"] = "MISSING_IN_SOURCE"
    # IMPORTER
    val = _find_value_after_label(text, r"(?:Uvoznik|Importer|Consignee|Buyer|Kupac)[^\n]*")
    if val:
        meta["importer"] = val
        meta["status"]["importer"] = "FOUND"
    else:
        meta["status"]["importer"] = "MISSING_IN_SOURCE"
    # INVOICE NUMBER
    patterns = [
        r"(?:Broj fakture|Invoice (?:No|Number))[.:]?\s*([A-Za-z0-9\-/]+)",
        r"(?:FAKTURA\s+BR\.?|Invoice No\.?)[.:]?\s*([A-Za-z0-9\-/]+)",
        r"INV[-\s]?(\d{2,}[-/]?\w*)",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            meta["invoice_number"] = m.group(1).strip()
            meta["status"]["invoice_number"] = "FOUND"
            break
    if not meta["invoice_number"]:
        meta["status"]["invoice_number"] = "MISSING_IN_SOURCE"
    # INVOICE DATE
    patterns = [
        r"(?:Datum fakture|Invoice date)[.:]?\s*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})",
        r"(?:Datum|Date)[.:]?\s*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            meta["invoice_date"] = m.group(1).strip()
            meta["status"]["invoice_date"] = "FOUND"
            break
    if not meta["invoice_date"]:
        meta["status"]["invoice_date"] = "MISSING_IN_SOURCE"
    # CURRENCY
    m = re.search(r"\b(EUR|USD|BAM|KM|HRK|RSD|MKD|€|\$)\b", text)
    if m:
        meta["currency"] = m.group(1).strip()
        meta["status"]["currency"] = "FOUND"
    else:
        meta["status"]["currency"] = "MISSING_IN_SOURCE"
    # INCOTERM
    m = re.search(r"\b(EXW|FOB|CIF|CFR|CIP|CPT|DAP|DPU|DDP|FCA|FAS)\b", text)
    if m:
        meta["incoterm"] = m.group(1).strip()
        meta["status"]["incoterm"] = "FOUND"
    else:
        meta["status"]["incoterm"] = "MISSING_IN_SOURCE"
    # BRUTO/NETO KG (ukupno)
    # Heuristika: "Bruto" ili "Neto" sa brojem
    bruto_patterns = [
        r"(?:Ukupno\s+)?bruto[^\n]*?(\d{1,5}[.,]?\d*)\s*(?:kg|kgs)?",
        r"total\s+bruto[^\n]*?(\d{1,5}[.,]?\d*)\s*(?:kg|kgs)?",
    ]
    for pat in bruto_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                meta["total_bruto_kg"] = float(m.group(1).replace(",", "."))
                meta["status"]["total_bruto_kg"] = "FOUND"
                break
            except ValueError:
                pass
    if meta["total_bruto_kg"] is None:
        meta["status"]["total_bruto_kg"] = "MISSING_IN_SOURCE"
    neto_patterns = [
        r"(?:Ukupno\s+)?neto[^\n]*?(\d{1,5}[.,]?\d*)\s*(?:kg|kgs)?",
        r"total\s+neto[^\n]*?(\d{1,5}[.,]?\d*)\s*(?:kg|kgs)?",
    ]
    for pat in neto_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                meta["total_neto_kg"] = float(m.group(1).replace(",", "."))
                meta["status"]["total_neto_kg"] = "FOUND"
                break
            except ValueError:
                pass
    if meta["total_neto_kg"] is None:
        meta["status"]["total_neto_kg"] = "MISSING_IN_SOURCE"
    # ORIGIN STATEMENT
    origin_keywords = ["izjava o porijeklu", "origin statement", "country of origin", "zemlja porijekla", "poreklo"]
    for kw in origin_keywords:
        if kw.lower() in text.lower():
            meta["has_origin_statement"] = True
            # Izvuci kontekst
            idx = text.lower().find(kw.lower())
            context = text[max(0, idx - 50):idx + 200]
            meta["origin_statement"] = context.strip()[:200]
            meta["status"]["origin_statement"] = "FOUND"
            break
    if not meta["has_origin_statement"]:
        meta["status"]["origin_statement"] = "MISSING_IN_SOURCE"
    return meta

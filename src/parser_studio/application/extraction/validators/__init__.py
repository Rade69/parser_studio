# Application: extraction/validators.
# Sadrzi: Validator Protocol + Issue dataclass + 6 implementacija.
# Zna za: domain.evidence, domain.extraction.extraction_draft.
# Ne zna za: SQLite, PySide6, Docling, contract, adapters.
"""FAZA C / C4 — Validators za ExtractionDraft.

6 validatora (minimalni set prema V3_2 §43.4):
- syntax: format polja (datum ISO, kolicina > 0, iznos != null)
- structure: 9 invoice polja prisutna, items.count > 0
- arithmetic: subtotal + tax = total, item.sum(qty * price) ~ total
- domain: seller_tax_id validan format
- cross_field: invoice_number unique, due_date >= invoice_date
- cross_document: NO_MATCH provjera sa drugim dokumentima (placeholder za FAZA D)

V3 ARCH-009: arithmetic NE SMIJE izmisljati vrijednosti — samo flaggira.
"""
from .arithmetic import ArithmeticValidator
from .base import Issue, IssueSeverity, Validator
from .cross_document import CrossDocumentValidator
from .cross_field import CrossFieldValidator
from .domain import DomainValidator
from .structure import StructureValidator
from .syntax import SyntaxValidator

__all__ = [
    "ArithmeticValidator",
    "CrossDocumentValidator",
    "CrossFieldValidator",
    "DomainValidator",
    "Issue",
    "IssueSeverity",
    "StructureValidator",
    "SyntaxValidator",
    "Validator",
]

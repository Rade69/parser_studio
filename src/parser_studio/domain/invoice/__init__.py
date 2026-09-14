# Domain: invoice package.
# Eksportuje: COLUMN_ALIASES, CanonicalInvoice, InvoiceLine, InvoiceField,
#             InvoiceStatus, VendorParserModel (+ supporting rule types).
# Ne zna za: SQLite, PySide6, Docling, openpyxl/xlrd, contract, adapters,
#            presentation.
"""Invoice domain package.

Moduli:

- `fields` — COLUMN_ALIASES + footer/essential konstante za header matching.
- `canonical_invoice` — vendor-agnostic CanonicalInvoice (20 polja + statusi).
- `vendor_parser_model` — VendorParserModel + supporting rule dataclasses/enums.
"""
from .canonical_invoice import (
    CanonicalInvoice,
    InvoiceField,
    InvoiceLine,
    InvoiceStatus,
    canonical_field_count,
    canonical_invoice_field_names,
    canonical_item_field_names,
    known_currencies,
)
from .fields import COLUMN_ALIASES
from .vendor_parser_model import (
    ConsumedPathsBehavior,
    ExtractionStrategy,
    FallbackStrategy,
    FieldExtractionRule,
    LayoutRule,
    NormalizationRule,
    ValidationRule,
    VendorParserModel,
    rule_count_summary,
)

__all__ = [
    "COLUMN_ALIASES",
    "CanonicalInvoice",
    "ConsumedPathsBehavior",
    "ExtractionStrategy",
    "FallbackStrategy",
    "FieldExtractionRule",
    "InvoiceField",
    "InvoiceLine",
    "InvoiceStatus",
    "LayoutRule",
    "NormalizationRule",
    "ValidationRule",
    "VendorParserModel",
    "canonical_field_count",
    "canonical_invoice_field_names",
    "canonical_item_field_names",
    "known_currencies",
    "rule_count_summary",
]
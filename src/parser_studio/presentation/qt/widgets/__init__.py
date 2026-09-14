# Presentation: qt/widgets package.
# Eksportuje: InvoiceReviewView, CellTableView.
# Ne zna za: SQLite, Docling, contract.
"""Qt Widgets — view layer (V3 B4).

Sadrzi InvoiceReviewView (glavni review widget) i CellTableView (read-only
prikaz celija dokumenta).
"""
from .cell_table_view import CellTableView
from .invoice_review_view import InvoiceReviewView

__all__ = ["CellTableView", "InvoiceReviewView"]

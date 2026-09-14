"""Parser Studio composition root.

Wiring između use case-ova, portova i adaptera.

A5: build_default_application() kreira 3 use case-a (ImportDocument,
AnalyzeInvoice, ConfirmInvoice) sa svim raspoloživim reader-ima i producer-ima.
LearningRepository je None (A6 će dodati SQLite adapter).
"""
from __future__ import annotations

from parser_studio.adapters.documents.excel_reader import ExcelDocumentReader
from parser_studio.application.extraction.analyze_invoice import (
    AnalyzeInvoice,
)
from parser_studio.application.extraction.producers.excel_header import (
    ExcelHeaderProducer,
)
from parser_studio.application.ingest.import_document import (
    ImportDocument,
)
from parser_studio.application.review.confirm_invoice import (
    ConfirmInvoice,
)


def build_default_application() -> tuple[
    ImportDocument, AnalyzeInvoice, ConfirmInvoice
]:
    """Kreiraj default aplikaciju sa svim raspoloživim portovima/adapterima."""
    excel_reader = ExcelDocumentReader()
    import_doc = ImportDocument(readers=(excel_reader,))

    excel_header_producer = ExcelHeaderProducer()
    analyze = AnalyzeInvoice(producers=(excel_header_producer,))

    # ConfirmInvoice bez LearningRepository (A6 će dodati SQLite adapter)
    confirm = ConfirmInvoice(learning_repo=None)

    return import_doc, analyze, confirm


__all__ = ["build_default_application"]

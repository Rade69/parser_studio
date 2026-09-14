"""Parser Studio composition root.

Wiring između use case-ova, portova i adaptera.

A6: build_default_application() kreira 3 use case-a + SQLiteLearningRepository.
File-based SQLite repo po defaultu u ~/.parser_studio/learning.db.
Env var PARSER_STUDIO_DB za override.
"""
from __future__ import annotations

import os
from pathlib import Path

from parser_studio.adapters.documents.excel_reader import ExcelDocumentReader
from parser_studio.adapters.persistence import SQLiteLearningRepository
from parser_studio.application.extraction.analyze_invoice import AnalyzeInvoice
from parser_studio.application.extraction.producers.excel_header import (
    ExcelHeaderProducer,
)
from parser_studio.application.ingest.import_document import ImportDocument
from parser_studio.application.review.confirm_invoice import ConfirmInvoice


DEFAULT_DB_PATH = Path.home() / ".parser_studio" / "learning.db"


def build_default_application(
    db_path: str | Path | None = None,
) -> tuple[
    ImportDocument,
    AnalyzeInvoice,
    ConfirmInvoice,
    SQLiteLearningRepository,
]:
    """Kreiraj default aplikaciju sa SQLite LearningRepository."""
    if db_path is None:
        env_path = os.environ.get("PARSER_STUDIO_DB")
        db_path = Path(env_path) if env_path else DEFAULT_DB_PATH

    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    excel_reader = ExcelDocumentReader()
    import_doc = ImportDocument(readers=(excel_reader,))

    excel_header_producer = ExcelHeaderProducer()
    analyze = AnalyzeInvoice(producers=(excel_header_producer,))

    repo = SQLiteLearningRepository(db_path=db_path)
    confirm = ConfirmInvoice(learning_repo=repo)

    return import_doc, analyze, confirm, repo


__all__ = ["DEFAULT_DB_PATH", "build_default_application"]

# Application: ingest/import_document.
# Posjeduje: ImportDocument use case + ImportRequest + ImportResult.
# Zna za: ports.document_reader.
# Ne zna za: SQLite, PySide6, Docling, openpyxl/xlrd, contract.
"""ImportDocument use case — cita izvorni dokument preko DocumentReader porta.

Koordinira domain (DocumentEvidence) + ports (DocumentReader).
NE importuje openpyxl/xlrd direktno — sve ide kroz port.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from parser_studio.domain.evidence import DocumentEvidence
from parser_studio.ports.document_reader import DocumentReader


@dataclass(frozen=True, slots=True)
class ImportRequest:
    path: Path
    document_id: str | None = None


@dataclass(frozen=True, slots=True)
class ImportResult:
    document: DocumentEvidence
    reader_id: str


class ImportDocument:
    """Use case: cita izvorni dokument preko DocumentReader porta."""

    def __init__(self, readers: tuple[DocumentReader, ...]) -> None:
        if not readers:
            raise ValueError("ImportDocument zahtijeva bar jedan DocumentReader")
        self._readers = readers

    def execute(self, request: ImportRequest) -> ImportResult:
        """Pronadji prvi reader koji podržava path, vrati ImportResult."""
        for reader in self._readers:
            if reader.supports(request.path):
                document = reader.read(request.path)
                return ImportResult(
                    document=document,
                    reader_id=reader.reader_id,
                )
        supported = ", ".join(r.reader_id for r in self._readers)
        raise ValueError(
            f"Nijedan DocumentReader ne podržava fajl: {request.path}. "
            f"Dostupni readeri: {supported}"
        )

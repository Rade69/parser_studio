# Port: DocumentReader.
# Posjeduje: Protocol contract za citanje izvornih dokumenata.
# Implementacije: ExcelDocumentReader (adapters/documents/), DoclingDocumentReader (FAZA B).
# Ne zna za: SQLite, PySide6, openpyxl/xlrd, contract.
"""DocumentReader port.

Definise contract za citanje izvornih dokumenata u DocumentEvidence.

Implementacije:
- ExcelDocumentReader (adapters/documents/excel_reader.py) za .xlsx/.xls
- DoclingDocumentReader (FAZA B / M3) za PDF/Docling
"""
from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from parser_studio.domain.evidence import DocumentEvidence


@runtime_checkable
class DocumentReader(Protocol):
    """Cita izvorni dokument i proizvodi DocumentEvidence."""

    reader_id: str

    def supports(self, path: Path) -> bool:
        """Da li ovaj reader moze citati dati fajl?"""
        ...

    def read(self, path: Path) -> DocumentEvidence:
        """Procitaj fajl i vrati DocumentEvidence sa cell/text/page evidence."""
        ...

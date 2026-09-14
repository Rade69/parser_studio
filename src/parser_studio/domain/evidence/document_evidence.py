# Domain: DocumentEvidence.
# Posjeduje: document_id, source_path, pages, text_elements, tables, cells, page_dimensions, metadata.
# Ne zna za: SQLite, PySide6, Docling, openpyxl, contract.
"""DocumentEvidence — standardizovan document model nezavisan od Doclinga/Excela.

Immutable value object. Sadrzi minimalni V3 skup polja.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .evidence import Evidence


@dataclass(frozen=True, slots=True)
class DocumentEvidence:
    """Standardizovan document model nezavisan od Doclinga/Excela."""

    document_id: str
    source_path: str

    pages: list[Any] = field(default_factory=list)
    text_elements: list[Evidence] = field(default_factory=list)
    tables: list[Any] = field(default_factory=list)
    cells: list[Evidence] = field(default_factory=list)

    page_dimensions: dict[int, tuple[float, float]] | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.document_id:
            raise ValueError("document_id ne može biti prazan string")
        if not self.source_path:
            raise ValueError("source_path ne može biti prazan string")

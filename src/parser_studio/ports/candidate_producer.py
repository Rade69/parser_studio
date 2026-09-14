# Port: CandidateProducer.
# Posjeduje: Protocol contract + FieldContext dataclass.
# Implementacije: ExcelHeaderProducer (application/extraction/producers/).
# Ne zna za: SQLite, PySide6, Docling, openpyxl/xlrd, contract.
"""CandidateProducer port.

Definise contract za Producer-e koji predlazu Candidate vrijednosti
za trazeno Invoice polje iz DocumentEvidence.

Implementacije:
- ExcelHeaderProducer (application/extraction/producers/excel_header.py)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from parser_studio.domain.evidence import Candidate, DocumentEvidence


@dataclass(frozen=True, slots=True)
class FieldContext:
    """State za producer poziv."""

    document_id: str
    field: str
    language: str = "bs"
    profile_version: int | None = None

    def __post_init__(self) -> None:
        if not self.document_id:
            raise ValueError("document_id ne može biti prazan string")
        if not self.field:
            raise ValueError("field ne može biti prazan string")


@runtime_checkable
class CandidateProducer(Protocol):
    """Predlaze kandidate vrijednosti za trazeno polje."""

    producer_id: str

    def supports(self, context: FieldContext) -> bool:
        """Da li ovaj producer moze obraditi dati context?"""
        ...

    def propose(
        self, document: DocumentEvidence, context: FieldContext
    ) -> list[Candidate]:
        """Propose kandidate za trazeno polje."""
        ...

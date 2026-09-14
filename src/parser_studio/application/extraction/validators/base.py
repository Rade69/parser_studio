# Application: extraction/validators/base.
# Posjeduje: Validator Protocol + Issue dataclass + IssueSeverity enum.
# Ne zna za: SQLite, PySide6, Docling, contract, adapters.
"""Validator Protocol i Issue dataclass (FAZA C / C4)."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from parser_studio.domain.extraction.extraction_draft import ExtractionDraft


class IssueSeverity(str, Enum):
    """Severnost Issue-a."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class Issue:
    """Jedan nalaz validatora.

    Atributi:
        severity: INFO/WARNING/ERROR.
        field: Ime polja na koje se odnosi (npr. "invoice_number").
            Moze biti prazno za strukturne probleme.
        message: Opis problema.
        code: Kratki kod (npr. "E001") za programatski pristup.
    """

    severity: IssueSeverity
    field: str
    message: str
    code: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.severity, IssueSeverity):
            raise TypeError(
                f"severity mora biti IssueSeverity, dobijeno {type(self.severity).__name__}"
            )


@runtime_checkable
class Validator(Protocol):
    """Port: validator za ExtractionDraft.

    Implementacije:
    - SyntaxValidator (validacija formata)
    - StructureValidator (provjera prisutnosti invoice/item polja)
    - ArithmeticValidator (matematicka konzistentnost)
    - DomainValidator (validacija domain-specific pravila)
    - CrossFieldValidator (odnose izmedju invoice polja)
    - CrossDocumentValidator (FAZA D — placeholder)
    """

    name: str

    def validate(self, draft: ExtractionDraft) -> tuple[Issue, ...]:
        """Vrati listu Issue-ova za dati draft."""
        ...


__all__ = ["Issue", "IssueSeverity", "Validator"]

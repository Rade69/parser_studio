# Domain: learning/learning_event.
# Posjeduje: LearningEvent dataclass + EventType enum.
# Ne zna za: SQLite, PySide6, Docling, openpyxl/xlrd, contract.
"""LearningEvent — append-only zapis promjene na dokumentu.

V3 specifikacija: append-only learning history. Svaki event je jedna
'cinjenica' koju parser smije zapamtiti. SQLite adapter za pohranu
je u A6 (LearningRepository port).
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from parser_studio.domain.evidence.locator import Locator


class EventType(str, enum.Enum):
    """Tip learning event-a. Koristi str za JSON serijalizaciju."""

    OCR_EXTRACTED = "OCR_EXTRACTED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    USER_CORRECTED = "USER_CORRECTED"
    USER_VERIFIED = "USER_VERIFIED"
    USER_CONFIRMED = "USER_CONFIRMED"
    # Oracle (V3_2 §44 D3) — korisnik potvrdio/odbacio oracle vrijednost
    ORACLE_CONFIRMED = "ORACLE_CONFIRMED"
    ORACLE_REJECTED = "ORACLE_REJECTED"


@dataclass(frozen=True, slots=True)
class LearningEvent:
    """Append-only zapis promjene na dokumentu."""

    document_id: str
    field_name: str
    event_type: EventType
    new_value: Any
    locator: Locator | None
    source: str
    item_id: str | None = None
    old_value: Any = None
    note: str = ""
    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def __post_init__(self) -> None:
        if not self.document_id:
            raise ValueError("document_id ne može biti prazan string")
        if not self.field_name:
            raise ValueError("field_name ne može biti prazan string")
        if not self.source:
            raise ValueError("source ne može biti prazan string")

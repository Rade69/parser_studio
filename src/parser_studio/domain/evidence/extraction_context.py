# Domain: ExtractionContext.
# Posjeduje: document_id, language, target_fields, profile_version, producer_id.
# Ne zna za: SQLite, PySide6, Docling, openpyxl, contract.
"""ExtractionContext — state za resolver/producer tokom extraction.

Immutable value object. Drzi informacije o jeziku, target poljima,
profile verziji i producer-u.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ExtractionContext:
    """State za resolver/producer tokom extraction."""

    document_id: str
    language: str = "bs"
    target_fields: tuple[str, ...] = field(default_factory=tuple)
    profile_version: int | None = None
    producer_id: str | None = None

    def __post_init__(self) -> None:
        if not self.document_id:
            raise ValueError("document_id ne može biti prazan string")
        if not self.language:
            raise ValueError("language ne može biti prazan string")

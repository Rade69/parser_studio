# Application: review/confirm_invoice.
# Posjeduje: ConfirmInvoice use case + FieldConfirmation + ConfirmRequest.
# Zna za: domain.learning (LearningEvent, EventType), domain.evidence (Locator).
# Ne zna za: SQLite, PySide6, Docling, openpyxl/xlrd, contract.
"""ConfirmInvoice use case — korisnik potvrđuje vrijednosti, generiše LearningEvent-ove.

Za MVP (A5): NE pohranjuje u SQLite (LearningRepository je A6).
Samo generise list[LearningEvent] i vraca ih pozivaocu.

GUI (FAZA B / M4) bude pozivao ovaj use case sa korisnickim inputom.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from parser_studio.domain.evidence.locator import Locator
from parser_studio.domain.extraction.extraction_draft import ExtractionDraft
from parser_studio.domain.learning.learning_event import EventType, LearningEvent


@runtime_checkable
class LearningRepository(Protocol):
    """Port za pohranu learning events. A6 implementira SQLite adapter."""

    def append(self, event: LearningEvent) -> None:
        ...

    def events_for(
        self, document_id: str, field: str | None = None
    ) -> list[LearningEvent]:
        """Vrati sve evente za dati dokument (opcionalno po polju)."""
        ...

    def events_since(
        self, since: datetime, field: str | None = None
    ) -> list[LearningEvent]:
        """Vrati evente kreirane poslije 'since' (opcionalno po polju)."""
        ...


@dataclass(frozen=True, slots=True)
class FieldConfirmation:
    """Jedna korisnicka potvrda vrijednosti polja."""

    field: str
    raw_value: Any
    normalized_value: Any
    locator: Locator
    confirmed: bool
    note: str = ""


@dataclass(frozen=True, slots=True)
class ConfirmRequest:
    draft: ExtractionDraft
    confirmations: tuple[FieldConfirmation, ...]
    actor: str  # user id (za learning events source)


class ConfirmInvoice:
    """Use case: korisnik potvrđuje vrijednosti, generiše LearningEvent-ove."""

    def __init__(self, learning_repo: LearningRepository | None = None) -> None:
        self._learning_repo = learning_repo

    def execute(self, request: ConfirmRequest) -> list[LearningEvent]:
        """Generisi LearningEvent za svaku potvrdu; pohrani ako repo postoji."""
        events: list[LearningEvent] = []
        for conf in request.confirmations:
            event = LearningEvent(
                document_id=request.draft.document_id,
                field_name=conf.field,
                event_type=EventType.USER_CONFIRMED,
                new_value=conf.normalized_value,
                locator=conf.locator,
                source=request.actor,
                old_value=conf.raw_value,
                note=conf.note,
            )
            events.append(event)
            if self._learning_repo is not None:
                self._learning_repo.append(event)
        return events

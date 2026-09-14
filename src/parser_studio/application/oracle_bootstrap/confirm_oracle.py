# Application: oracle_bootstrap/confirm_oracle.
# Posjeduje: ConfirmOracle use case.
# Smije zavisiti samo od: domain, ports.
"""ConfirmOracle — korisnik potvrđuje/odbacuje Oracle vrijednosti.

V3_2 §44 D3 — Human verification.

Tok:
- accept: emituje ORACLE_CONFIRMED + USER_CONFIRMED event
  (Oracle vrijednost postaje Gold)
- reject: emituje ORACLE_REJECTED event (bez confirmed value,
  Oracle vrijednost ODBACENA)

Stari parser NIJE automatski istina (V3 §23). ConfirmOracle je TAJ
koji odlučuje.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from parser_studio.domain.evidence import Locator
from parser_studio.domain.learning import EventType, LearningEvent


@runtime_checkable
class LearningRepository(Protocol):
    """Minimal LearningRepository port (ConfirmOracle samo treba append).

    Definisan lokalno jer FAZA D3 ne zavisi od A6 adaptera. Ako se
    kasnije refaktoriše u ports/learning_repository.py, ConfirmOracle
    importuje odande.
    """

    def append(self, event: LearningEvent) -> None:
        ...


@dataclass(frozen=True, slots=True)
class ConfirmOracleRequest:
    """Input za ConfirmOracle."""

    document_id: str
    field_name: str
    oracle_value: Any
    locator: Locator | None
    decision: str  # "accept" | "reject"
    item_id: str | None = None
    actor: str = "user:test"
    note: str = ""

    def __post_init__(self) -> None:
        if not self.document_id:
            raise ValueError("document_id ne može biti prazan string")
        if not self.field_name:
            raise ValueError("field_name ne može biti prazan string")
        if self.decision not in ("accept", "reject"):
            raise ValueError(
                f"decision mora biti 'accept' ili 'reject', dobijeno {self.decision!r}"
            )


@dataclass(frozen=True, slots=True)
class ConfirmOracleResult:
    """Output iz ConfirmOracle."""

    accepted: bool
    events: tuple[LearningEvent, ...]
    gold_dataset_entry_id: str | None  # ako accept — entry_id u GoldDataset


class ConfirmOracle:
    """Use case: korisnik accept/reject Oracle vrijednost."""

    def __init__(self, learning_repo: LearningRepository | None = None) -> None:
        self._learning_repo = learning_repo

    def execute(self, request: ConfirmOracleRequest) -> ConfirmOracleResult:
        """Generiši LearningEvent za accept/reject odluku.

        Returns:
            ConfirmOracleResult sa:
            - accepted: True ako accept, False ako reject
            - events: tuple LearningEvent-ova (ORACLE_CONFIRMED + USER_CONFIRMED za accept;
              ORACLE_REJECTED za reject)
            - gold_dataset_entry_id: None (FAZA D3; FAZA I ce vratiti pravi entry_id)

        Raises:
            ValueError: ako decision nije 'accept' ili 'reject'
        """
        events: list[LearningEvent] = []

        # Uvijek emituj ORACLE_* event za audit
        oracle_event_type = (
            EventType.ORACLE_CONFIRMED
            if request.decision == "accept"
            else EventType.ORACLE_REJECTED
        )
        oracle_event = LearningEvent(
            document_id=request.document_id,
            field_name=request.field_name,
            event_type=oracle_event_type,
            new_value=request.oracle_value if request.decision == "accept" else None,
            locator=request.locator,
            source=f"oracle:{request.actor}",
            item_id=request.item_id,
            note=request.note or f"Oracle {request.decision}",
        )
        events.append(oracle_event)
        self._append_if_repo(oracle_event)

        # Ako accept, dodatno emituj USER_CONFIRMED (Oracle → Gold)
        if request.decision == "accept":
            user_event = LearningEvent(
                document_id=request.document_id,
                field_name=request.field_name,
                event_type=EventType.USER_CONFIRMED,
                new_value=request.oracle_value,
                locator=request.locator,
                source=request.actor,
                item_id=request.item_id,
                old_value=request.oracle_value,
                note=request.note or "Oracle accepted",
            )
            events.append(user_event)
            self._append_if_repo(user_event)

        # FAZA D3: gold_dataset_entry_id=None (FAZA I ce povezati)
        return ConfirmOracleResult(
            accepted=request.decision == "accept",
            events=tuple(events),
            gold_dataset_entry_id=None,
        )

    def _append_if_repo(self, event: LearningEvent) -> None:
        """Pohrani event u repo ako repo postoji (best-effort)."""
        if self._learning_repo is not None:
            self._learning_repo.append(event)
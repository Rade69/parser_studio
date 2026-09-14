# Application: extraction/resolve_candidates.
# Posjeduje: ResolveRequest + ResolveResult + ResolutionStrategy + ResolveCandidates.
# Zna za: domain.evidence, domain.extraction.extraction_draft.
# Ne zna za: SQLite, PySide6, Docling, contract, adapters.
"""ResolveCandidates use case — deterministic kombinovanje kandidata.

Uzima ExtractionDraft sa kandidatima od razlicitih Producer-a (ExcelHeader,
LabelRight, ValueShape, itd.) i bira jednog finalnog kandidata po polju.

Strategije:
- FIRST_MATCH: prvi kandidat (deterministicki redoslijed po producer_id)
- HIGHEST_CONFIDENCE: kandidat sa najvisim confidence (1/producer rank)
- CONSENSUS: ako 2+ producer-a setuju na istu vrijednost, ta vrijednost je final
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from parser_studio.domain.evidence import Candidate
from parser_studio.domain.extraction.extraction_draft import ExtractionDraft


class ResolutionStrategy(str, Enum):
    """Strategija biranja finalnog kandidata po polju."""

    FIRST_MATCH = "first_match"
    HIGHEST_CONFIDENCE = "highest_confidence"
    CONSENSUS = "consensus"


# Confidence score po producer_id (heuristika, moze se override-at)
_DEFAULT_CONFIDENCE: dict[str, float] = {
    "excel_header": 0.90,
    "label_right": 0.80,
    "label_below": 0.75,
    "table_header": 0.85,
    "column_content": 0.70,
    "value_shape": 0.60,
}


@dataclass(frozen=True, slots=True)
class ResolveRequest:
    """Request za ResolveCandidates use case."""

    draft: ExtractionDraft
    strategy: ResolutionStrategy = ResolutionStrategy.FIRST_MATCH

    def __post_init__(self) -> None:
        if not isinstance(self.draft, ExtractionDraft):
            raise TypeError(
                f"draft mora biti ExtractionDraft, dobijeno {type(self.draft).__name__}"
            )
        if not isinstance(self.strategy, ResolutionStrategy):
            raise TypeError(
                f"strategy mora biti ResolutionStrategy, dobijeno {type(self.strategy).__name__}"
            )


@dataclass(frozen=True, slots=True)
class ConflictInfo:
    """Informacija o konfliktu izmedju producer-a za isto polje."""

    field: str
    candidates: tuple[Candidate, ...]
    chosen: Candidate
    reason: str


@dataclass(frozen=True, slots=True)
class ResolveResult:
    """Rezultat ResolveCandidates use case-a."""

    resolved_by_field: dict[str, Candidate]
    conflicts: tuple[ConflictInfo, ...]
    unresolved: tuple[str, ...]


class ResolveCandidates:
    """Use case: biraj finalnog Candidate-a po polju koristeci strategy."""

    def execute(self, request: ResolveRequest) -> ResolveResult:
        """Resolve sve kandidate po polju koristeci strategy."""
        resolved: dict[str, Candidate] = {}
        conflicts: list[ConflictInfo] = []
        unresolved: list[str] = []

        for field, candidates in request.draft.candidates_by_field.items():
            if not candidates:
                unresolved.append(field)
                continue

            chosen, conflict = self._resolve_field(field, candidates, request.strategy)
            resolved[field] = chosen
            if conflict is not None:
                conflicts.append(conflict)

        return ResolveResult(
            resolved_by_field=resolved,
            conflicts=tuple(conflicts),
            unresolved=tuple(unresolved),
        )

    def _resolve_field(
        self,
        field: str,
        candidates: tuple[Candidate, ...],
        strategy: ResolutionStrategy,
    ) -> tuple[Candidate, ConflictInfo | None]:
        """Resolve kandidate za jedno polje. Vraca (chosen, conflict_or_None)."""
        if len(candidates) == 1:
            return candidates[0], None

        if strategy == ResolutionStrategy.FIRST_MATCH:
            # Deterministicki: prvi kandidat po producer_id
            sorted_cands = tuple(
                sorted(candidates, key=lambda c: _producer_sort_key(c.producer_id))
            )
            chosen = sorted_cands[0]
            conflict = ConflictInfo(
                field=field,
                candidates=candidates,
                chosen=chosen,
                reason="first_match: producer priority order",
            )
            return chosen, conflict

        elif strategy == ResolutionStrategy.HIGHEST_CONFIDENCE:
            sorted_cands = tuple(
                sorted(
                    candidates,
                    key=lambda c: -_confidence_for(c.producer_id),
                )
            )
            chosen = sorted_cands[0]
            conflict = ConflictInfo(
                field=field,
                candidates=candidates,
                chosen=chosen,
                reason="highest_confidence: highest producer confidence",
            )
            return chosen, conflict

        elif strategy == ResolutionStrategy.CONSENSUS:
            # Ako svi kandidat imaju istu normalized_value, ta je final
            unique_values = {
                str(c.normalized_value).strip() for c in candidates
            }
            if len(unique_values) == 1:
                chosen = candidates[0]  # svi setuju
                return chosen, None
            # Nema konsenzusa — fallback na FIRST_MATCH
            sorted_cands = tuple(
                sorted(candidates, key=lambda c: _producer_sort_key(c.producer_id))
            )
            chosen = sorted_cands[0]
            conflict = ConflictInfo(
                field=field,
                candidates=candidates,
                chosen=chosen,
                reason="consensus failed: producers disagree on value",
            )
            return chosen, conflict

        else:
            # Unknown strategy — fallback
            return candidates[0], None


def _producer_sort_key(producer_id: str) -> int:
    """Sort key: prioritet po confidence (viso confidence ide prvo)."""
    confidence = _DEFAULT_CONFIDENCE.get(producer_id, 0.0)
    # Sort ascending: -confidence (negative confidence = higher confidence first)
    return int(-confidence * 100)


def _confidence_for(producer_id: str) -> float:
    """Confidence score za dati producer_id."""
    return _DEFAULT_CONFIDENCE.get(producer_id, 0.0)


__all__ = [
    "ConflictInfo",
    "ResolutionStrategy",
    "ResolveCandidates",
    "ResolveRequest",
    "ResolveResult",
]

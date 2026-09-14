# Ports: advisor.
# Posjeduje: Advisor Protocol, AdvisorMode enum, AIAdvice dataclass.
# Ne zna za: AI provider SDK (openai, anthropic, httpx, ...), SQLite, presentation, contract.
"""Advisor port — apstrakcija za AI/LLM savjetnika.

Port definise STA advisor radi (consult), a adapteri (NullAdvisor, HttpVisionAdvisor)
odlucuju KAKO. Domain i application ovise samo o ovom portu.

Default rezim: OFF (NullAdvisor). LIVE rezim se aktivira eksplicitno kroz
PARSER_STUDIO_AI_MODE=live ili konfiguracijom u bootstrap.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from parser_studio.domain.evidence import Candidate, ExtractionContext, Locator


class AdvisorMode(str, Enum):
    """Rezim rada Advisor porta."""

    OFF = "off"
    CACHE_ONLY = "cache-only"
    LIVE = "live"


@dataclass(frozen=True, slots=True)
class AIAdvice:
    """Savjet AI advisor-a za jedan field.

    Sadrzi suggested_value (prijedlog), locator_evidence (gdje u dokumentu
    advisor misli da se nalazi), confidence (0.0..1.0) i reasoning
    (kratko objasnjenje ili None).
    """

    field: str
    suggested_value: object
    locator_evidence: Locator | None
    confidence: float
    reasoning: str | None = None

    def __post_init__(self) -> None:
        if not self.field:
            raise ValueError("field ne moze biti prazan string")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"confidence mora biti u [0.0, 1.0], dobijeno {self.confidence}"
            )
        if self.locator_evidence is not None and not isinstance(
            self.locator_evidence, Locator
        ):
            raise TypeError(
                f"locator_evidence mora biti Locator ili None, "
                f"dobijeno {type(self.locator_evidence).__name__}"
            )


@runtime_checkable
class Advisor(Protocol):
    """Port za AI/LLM savjetnika.

    Implementacije:
    - NullAdvisor: OFF rezim (default, nema mreznih poziva)
    - HttpVisionAdvisor: LIVE rezim (provider iza transport apstrakcije, G3)
    """

    mode: AdvisorMode

    def consult(
        self,
        *,
        field: str,
        candidates: tuple[Candidate, ...],
        context: ExtractionContext,
    ) -> tuple[AIAdvice, ...]:
        """Vrati AI savjete za dato polje.

        Args:
            field: Ime polja za koje se trazi savjet (npr. "invoice_number").
            candidates: Postojuci kandidati od deterministic extractor-a.
                Advisor moze koristiti kao hint ili anchor.
            context: Extraction state (document_id, language, target_fields, ...).

        Returns:
            Tuple AIAdvice objekata. Prazan tuple ako advisor nema prijedlog
            ili je u OFF rezimu.

        Note:
            Implementacija MORA biti thread-safe i idempotent za iste inpute
            (G5 cache zahtijeva reproducibilnost).
        """
        ...


__all__ = ["AIAdvice", "Advisor", "AdvisorMode"]

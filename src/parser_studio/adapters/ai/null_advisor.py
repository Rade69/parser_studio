# Adapters: ai/null_advisor.
# Posjeduje: NullAdvisor implementaciju Advisor porta za OFF rezim.
# Zna za: parser_studio.domain.evidence, parser_studio.ports.advisor.
# Ne zna za: openai/anthropic/httpx/bilo koji LLM library.
"""NullAdvisor — OFF rezim Advisor porta.

Uvijek vraca prazan tuple. Bez mreznih poziva, bez LLM-a, bez ikakvih
eksternih dependencija. Default adapter kada je AI off (prema V3 sekcija 29).
"""
from __future__ import annotations

from parser_studio.domain.evidence import Candidate, ExtractionContext
from parser_studio.ports.advisor import AdvisorMode, AIAdvice


class NullAdvisor:
    """Advisor koji uvijek vraca prazan tuple.

    Koristi se kada je PS_AI_MODE=off (default) ili kada aplikacija
    eksplicitno zeli "no AI" ponasanje. Thread-safe (bez stanja).

    Primjer:
        advisor = NullAdvisor()
        assert advisor.mode == AdvisorMode.OFF
        result = advisor.consult(field="kolicina", candidates=(), context=ctx)
        assert result == ()
    """

    mode: AdvisorMode = AdvisorMode.OFF

    def consult(
        self,
        *,
        field: str,
        candidates: tuple[Candidate, ...],
        context: ExtractionContext,
    ) -> tuple[AIAdvice, ...]:
        """Vrati prazan tuple. NullAdvisor nema prijedloga."""
        return ()


__all__ = ["NullAdvisor"]

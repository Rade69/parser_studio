# Application: learning/consult_advisor.
# Posjeduje: ConsultAdvisor use case + ConsultRequest/ConsultResult.
# Zna za: parser_studio.domain.evidence, parser_studio.ports.advisor.
# Ne zna za: parser_studio.adapters.* (kroz port), presentation, SQLite, contract.
"""ConsultAdvisor use case — wrapper oko Advisor porta.

Use case NE SMIJE importovati konkretan Advisor (NullAdvisor/HttpVisionAdvisor)
direktno; to je adapter dependency. Use case ovidi o portu i eksplicitno
prima advisor kroz konstruktor.

Pozivalac (ConfirmInvoice, Review GUI, CLI) odlucuje koji adapter instancirati.
"""
from __future__ import annotations

from dataclasses import dataclass

from parser_studio.domain.evidence import Candidate, ExtractionContext
from parser_studio.ports.advisor import Advisor, AdvisorMode, AIAdvice


@dataclass(frozen=True, slots=True)
class ConsultRequest:
    """Request za ConsultAdvisor use case."""

    field: str
    candidates: tuple[Candidate, ...]
    context: ExtractionContext

    def __post_init__(self) -> None:
        if not self.field:
            raise ValueError("field ne moze biti prazan string")
        if not isinstance(self.context, ExtractionContext):
            raise TypeError(
                f"context mora biti ExtractionContext instanca, "
                f"dobijeno {type(self.context).__name__}"
            )


@dataclass(frozen=True, slots=True)
class ConsultResult:
    """Rezultat ConsultAdvisor use case-a.

    Sadrzi field (echo), advice tuple od advisor-a, mode (za traceability)
    i advisor_id (identitet konkretne implementacije, npr. "null", "openai-gpt4").
    """

    field: str
    advice: tuple[AIAdvice, ...]
    mode: AdvisorMode
    advisor_id: str


class ConsultAdvisor:
    """Use case: konsultuj Advisor za dato polje.

    Konstruktor prima Advisor port (NE konkretan adapter). Aplikacija
    instancira NullAdvisor ili drugu implementaciju i proslijedi ovom
    use case-u.

    Primjer:
        from parser_studio.adapters.ai import NullAdvisor
        from parser_studio.ports.advisor import AdvisorMode

        advisor = NullAdvisor()  # OFF rezim
        consult_uc = ConsultAdvisor(advisor=advisor)
        result = consult_uc.execute(ConsultRequest(
            field="kolicina",
            candidates=(),
            context=ctx,
        ))
        assert result.mode == AdvisorMode.OFF
        assert result.advice == ()
    """

    def __init__(self, advisor: Advisor) -> None:
        if not isinstance(advisor, Advisor):
            # runtime_checkable Protocol — isinstance provjera prolazi
            # za svaku klasu koja ima mode atribut i consult metodu.
            # Ne importujemo Advisor u isinstance — ostaje runtime provjera.
            raise TypeError(
                f"advisor mora implementirati Advisor Protocol "
                f"(mode + consult), dobijeno {type(advisor).__name__}"
            )
        self._advisor = advisor

    def execute(self, request: ConsultRequest) -> ConsultResult:
        """Pozovi Advisor i vrati structured rezultat."""
        advice = self._advisor.consult(
            field=request.field,
            candidates=request.candidates,
            context=request.context,
        )
        return ConsultResult(
            field=request.field,
            advice=advice,
            mode=self._advisor.mode,
            advisor_id=type(self._advisor).__name__,
        )


__all__ = ["ConsultAdvisor", "ConsultRequest", "ConsultResult"]

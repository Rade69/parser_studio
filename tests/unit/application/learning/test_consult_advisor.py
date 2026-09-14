# Tests: application/learning/test_consult_advisor.
"""Testovi za ConsultAdvisor use case.

Verifikacija:
1. Use case pravilno wrap-uje Advisor port
2. ConsultRequest validacija
3. ConsultResult sadrzi mode + advisor_id
4. Use case radi sa NullAdvisor i custom Advisor implementacijama
5. Use case NE importuje adapters direktno (kroz port)
"""
from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from parser_studio.adapters.ai import NullAdvisor
from parser_studio.application.learning import (
    ConsultAdvisor,
    ConsultRequest,
    ConsultResult,
)
from parser_studio.domain.evidence import Candidate, ExtractionContext, Locator
from parser_studio.ports.advisor import AdvisorMode, AIAdvice


def _make_locator() -> Locator:
    return Locator(source_path="/tmp/test.xlsx", kind="excel")


def _make_candidate(field: str = "kolicina", value: object = 5) -> Candidate:
    return Candidate(
        field=field,
        raw_value=value,
        normalized_value=value,
        locator=_make_locator(),
        evidence="A1",
        producer_id="excel_header",
    )


def _make_context() -> ExtractionContext:
    return ExtractionContext(
        document_id="doc-001",
        target_fields=("kolicina", "naziv_robe"),
    )


class TestConsultRequest:
    def test_construction(self) -> None:
        ctx = _make_context()
        req = ConsultRequest(field="kolicina", candidates=(), context=ctx)
        assert req.field == "kolicina"
        assert req.candidates == ()
        assert req.context is ctx

    def test_with_candidates(self) -> None:
        req = ConsultRequest(
            field="naziv_robe",
            candidates=(_make_candidate(field="naziv_robe"),),
            context=_make_context(),
        )
        assert len(req.candidates) == 1

    def test_empty_field_raises(self) -> None:
        with pytest.raises(ValueError, match="field ne moze biti prazan"):
            ConsultRequest(field="", candidates=(), context=_make_context())

    def test_invalid_context_raises(self) -> None:
        with pytest.raises(TypeError, match="context mora biti"):
            ConsultRequest(
                field="kolicina",
                candidates=(),
                context="not-a-context",  # type: ignore[arg-type]
            )

    def test_frozen(self) -> None:
        req = ConsultRequest(field="kolicina", candidates=(), context=_make_context())
        with pytest.raises(FrozenInstanceError):
            req.field = "naziv_robe"  # type: ignore[misc]


class TestConsultResult:
    def test_construction(self) -> None:
        result = ConsultResult(
            field="kolicina",
            advice=(),
            mode=AdvisorMode.OFF,
            advisor_id="NullAdvisor",
        )
        assert result.field == "kolicina"
        assert result.advice == ()
        assert result.mode == AdvisorMode.OFF
        assert result.advisor_id == "NullAdvisor"

    def test_with_advice(self) -> None:
        advice = AIAdvice(
            field="kolicina",
            suggested_value=10,
            locator_evidence=_make_locator(),
            confidence=0.9,
        )
        result = ConsultResult(
            field="kolicina",
            advice=(advice,),
            mode=AdvisorMode.LIVE,
            advisor_id="FakeAdvisor",
        )
        assert len(result.advice) == 1
        assert result.advice[0].suggested_value == 10

    def test_frozen(self) -> None:
        result = ConsultResult(
            field="kolicina",
            advice=(),
            mode=AdvisorMode.OFF,
            advisor_id="X",
        )
        with pytest.raises(FrozenInstanceError):
            result.mode = AdvisorMode.LIVE  # type: ignore[misc]


class TestConsultAdvisorWithNull:
    def test_construction_with_null_advisor(self) -> None:
        advisor = NullAdvisor()
        uc = ConsultAdvisor(advisor=advisor)
        assert uc is not None

    def test_execute_returns_empty_advice(self) -> None:
        uc = ConsultAdvisor(advisor=NullAdvisor())
        result = uc.execute(
            ConsultRequest(field="kolicina", candidates=(), context=_make_context())
        )
        assert result.field == "kolicina"
        assert result.advice == ()
        assert result.mode == AdvisorMode.OFF
        assert result.advisor_id == "NullAdvisor"

    def test_execute_with_candidates_returns_empty(self) -> None:
        """NullAdvisor uvijek vraca prazno, neovisno o candidates."""
        uc = ConsultAdvisor(advisor=NullAdvisor())
        result = uc.execute(
            ConsultRequest(
                field="invoice_number",
                candidates=(_make_candidate(),),
                context=_make_context(),
            )
        )
        assert result.advice == ()


class TestConsultAdvisorWithCustomAdvisor:
    def test_with_live_advisor(self) -> None:
        class LiveAdvisor:
            mode: AdvisorMode = AdvisorMode.LIVE

            def consult(
                self,
                *,
                field: str,
                candidates: tuple[Candidate, ...],
                context: ExtractionContext,
            ) -> tuple[AIAdvice, ...]:
                return (
                    AIAdvice(
                        field=field,
                        suggested_value="LIVE-ANSWER",
                        locator_evidence=candidates[0].locator if candidates else None,
                        confidence=0.85,
                        reasoning="Custom test advisor",
                    ),
                )

        uc = ConsultAdvisor(advisor=LiveAdvisor())
        result = uc.execute(
            ConsultRequest(field="x", candidates=(), context=_make_context())
        )
        assert result.mode == AdvisorMode.LIVE
        assert result.advisor_id == "LiveAdvisor"
        assert len(result.advice) == 1
        assert result.advice[0].suggested_value == "LIVE-ANSWER"

    def test_advisor_with_cache_only_mode(self) -> None:
        class CacheOnlyAdvisor:
            mode: AdvisorMode = AdvisorMode.CACHE_ONLY

            def consult(
                self,
                *,
                field: str,
                candidates: tuple[Candidate, ...],
                context: ExtractionContext,
            ) -> tuple[AIAdvice, ...]:
                # Cache-only: vrati samo ako vec postoji cache hit
                return ()

        uc = ConsultAdvisor(advisor=CacheOnlyAdvisor())
        result = uc.execute(
            ConsultRequest(field="x", candidates=(), context=_make_context())
        )
        assert result.mode == AdvisorMode.CACHE_ONLY


class TestConsultAdvisorValidation:
    def test_non_advisor_raises(self) -> None:
        class NotAdvisor:
            """Nema mode atribut i/ili consult metodu."""

        with pytest.raises(TypeError, match="advisor mora implementirati"):
            ConsultAdvisor(advisor=NotAdvisor())  # type: ignore[arg-type]

    def test_class_without_consult_method_raises(self) -> None:
        class HalfAdvisor:
            mode: AdvisorMode = AdvisorMode.OFF
            # Nema consult metodu

        with pytest.raises(TypeError):
            ConsultAdvisor(advisor=HalfAdvisor())  # type: ignore[arg-type]

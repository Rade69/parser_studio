# Tests: ports/test_advisor.
"""Testovi za Advisor port Protocol, AdvisorMode enum i AIAdvice dataclass."""
from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from parser_studio.domain.evidence import Candidate, ExtractionContext, Locator
from parser_studio.ports.advisor import Advisor, AdvisorMode, AIAdvice


def _make_locator() -> Locator:
    return Locator(source_path="/tmp/test.xlsx", kind="excel", sheet="Faktura")


def _make_candidate(field: str = "kolicina", value: object = 5) -> Candidate:
    return Candidate(
        field=field,
        raw_value=value,
        normalized_value=value,
        locator=_make_locator(),
        evidence="A1:B1",
        producer_id="excel_header",
    )


def _make_context() -> ExtractionContext:
    return ExtractionContext(
        document_id="doc-001",
        target_fields=("kolicina", "naziv_robe"),
    )


class TestAdvisorMode:
    def test_three_modes_defined(self) -> None:
        assert AdvisorMode.OFF.value == "off"
        assert AdvisorMode.CACHE_ONLY.value == "cache-only"
        assert AdvisorMode.LIVE.value == "live"

    def test_string_enum(self) -> None:
        assert AdvisorMode("off") is AdvisorMode.OFF
        assert AdvisorMode("cache-only") is AdvisorMode.CACHE_ONLY
        assert AdvisorMode("live") is AdvisorMode.LIVE

    def test_invalid_value_raises(self) -> None:
        with pytest.raises(ValueError):
            AdvisorMode("nepoznato")


class TestAIAdvice:
    def test_minimal_construction(self) -> None:
        advice = AIAdvice(
            field="kolicina",
            suggested_value=10,
            locator_evidence=None,
            confidence=0.8,
        )
        assert advice.field == "kolicina"
        assert advice.suggested_value == 10
        assert advice.locator_evidence is None
        assert advice.confidence == 0.8
        assert advice.reasoning is None

    def test_with_locator_and_reasoning(self) -> None:
        locator = _make_locator()
        advice = AIAdvice(
            field="invoice_number",
            suggested_value="INV-2026-001",
            locator_evidence=locator,
            confidence=0.95,
            reasoning="Pronadjen u celiji B5",
        )
        assert advice.locator_evidence is locator
        assert advice.reasoning == "Pronadjen u celiji B5"

    def test_empty_field_raises(self) -> None:
        with pytest.raises(ValueError, match="field ne moze biti prazan"):
            AIAdvice(
                field="",
                suggested_value=None,
                locator_evidence=None,
                confidence=0.5,
            )

    def test_confidence_below_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="confidence mora biti u"):
            AIAdvice(
                field="kolicina",
                suggested_value=None,
                locator_evidence=None,
                confidence=-0.1,
            )

    def test_confidence_above_one_raises(self) -> None:
        with pytest.raises(ValueError, match="confidence mora biti u"):
            AIAdvice(
                field="kolicina",
                suggested_value=None,
                locator_evidence=None,
                confidence=1.5,
            )

    def test_confidence_boundary_zero(self) -> None:
        advice = AIAdvice(
            field="kolicina",
            suggested_value=None,
            locator_evidence=None,
            confidence=0.0,
        )
        assert advice.confidence == 0.0

    def test_confidence_boundary_one(self) -> None:
        advice = AIAdvice(
            field="kolicina",
            suggested_value=None,
            locator_evidence=None,
            confidence=1.0,
        )
        assert advice.confidence == 1.0

    def test_invalid_locator_type_raises(self) -> None:
        with pytest.raises(TypeError, match="locator_evidence mora biti"):
            AIAdvice(
                field="kolicina",
                suggested_value=None,
                locator_evidence="/tmp/test.xlsx",  # type: ignore[arg-type]
                confidence=0.5,
            )

    def test_frozen(self) -> None:
        advice = AIAdvice(
            field="kolicina",
            suggested_value=10,
            locator_evidence=None,
            confidence=0.8,
        )
        with pytest.raises(FrozenInstanceError):
            advice.field = "naziv_robe"  # type: ignore[misc]


class TestAdvisorProtocol:
    def test_null_advisor_satisfies_protocol(self) -> None:
        from parser_studio.adapters.ai import NullAdvisor

        advisor = NullAdvisor()
        assert isinstance(advisor, Advisor)

    def test_custom_class_satisfying_protocol(self) -> None:
        class FakeAdvisor:
            mode: AdvisorMode = AdvisorMode.LIVE

            def consult(
                self,
                *,
                field: str,
                candidates: tuple[Candidate, ...],
                context: ExtractionContext,
            ) -> tuple[AIAdvice, ...]:
                return ()

        fake = FakeAdvisor()
        assert isinstance(fake, Advisor)

    def test_class_without_mode_not_advisor(self) -> None:
        class NotAdvisor:
            def consult(
                self,
                *,
                field: str,
                candidates: tuple[Candidate, ...],
                context: ExtractionContext,
            ) -> tuple[AIAdvice, ...]:
                return ()

        assert not isinstance(NotAdvisor(), Advisor)

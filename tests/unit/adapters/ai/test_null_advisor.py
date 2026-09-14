# Tests: adapters/ai/test_null_advisor.
"""Testovi za NullAdvisor — OFF rezim Advisor porta.

Verifikacija da NullAdvisor:
1. Nema mreznih poziva (NE importuje openai/anthropic/httpx/requests)
2. Uvijek vraca prazan tuple
3. Ima mode=OFF
4. Radi sa praznim i nepraznim candidates
5. Thread-safe (bez stanja)
"""
from __future__ import annotations

import sys

from parser_studio.adapters.ai import NullAdvisor
from parser_studio.domain.evidence import Candidate, ExtractionContext, Locator
from parser_studio.ports.advisor import Advisor, AdvisorMode


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
    return ExtractionContext(document_id="doc-001")


class TestNullAdvisorBasics:
    def test_construction_no_args(self) -> None:
        advisor = NullAdvisor()
        assert advisor is not None

    def test_mode_is_off(self) -> None:
        advisor = NullAdvisor()
        assert advisor.mode == AdvisorMode.OFF

    def test_satisfies_advisor_protocol(self) -> None:
        advisor = NullAdvisor()
        assert isinstance(advisor, Advisor)

    def test_class_name(self) -> None:
        advisor = NullAdvisor()
        assert type(advisor).__name__ == "NullAdvisor"


class TestConsultReturnsEmpty:
    def test_empty_candidates_returns_empty_tuple(self) -> None:
        advisor = NullAdvisor()
        result = advisor.consult(
            field="kolicina",
            candidates=(),
            context=_make_context(),
        )
        assert result == ()
        assert isinstance(result, tuple)

    def test_with_candidates_returns_empty(self) -> None:
        advisor = NullAdvisor()
        candidates = (_make_candidate(), _make_candidate(field="naziv_robe"))
        result = advisor.consult(
            field="kolicina",
            candidates=candidates,
            context=_make_context(),
        )
        assert result == ()

    def test_with_ai_advice_candidates_returns_empty(self) -> None:
        """NullAdvisor ignorise AI-assisted candidate (mode=OFF)."""
        advisor = NullAdvisor()
        ai_candidate = Candidate(
            field="kolicina",
            raw_value=10,
            normalized_value=10,
            locator=_make_locator(),
            evidence="A1",
            producer_id="ai_advisor",
            ai_assisted=True,
        )
        result = advisor.consult(
            field="kolicina",
            candidates=(ai_candidate,),
            context=_make_context(),
        )
        assert result == ()

    def test_multiple_calls_return_empty(self) -> None:
        """Idempotentnost: vise poziva vraca isto."""
        advisor = NullAdvisor()
        for _ in range(10):
            assert advisor.consult(
                field="invoice_number",
                candidates=(_make_candidate(),),
                context=_make_context(),
            ) == ()


class TestNullAdvisorNoExternalDependencies:
    def test_no_openai_import(self) -> None:
        """NullAdvisor NE SMIJE importovati openai."""
        # Brisanje iz sys.modules simulira "nije importovao"
        openai_modules = [m for m in sys.modules if m.startswith("openai")]
        assert openai_modules == [], (
            f"NullAdvisor ne smije importovati openai, ali sys.modules sadrzi: {openai_modules}"
        )

    def test_no_anthropic_import(self) -> None:
        anthropic_modules = [m for m in sys.modules if m.startswith("anthropic")]
        assert anthropic_modules == [], (
            f"NullAdvisor ne smije importovati anthropic, ali sys.modules sadrzi: {anthropic_modules}"
        )

    def test_no_httpx_import(self) -> None:
        httpx_modules = [m for m in sys.modules if m.startswith("httpx")]
        assert httpx_modules == [], (
            f"NullAdvisor ne smije importovati httpx, ali sys.modules sadrzi: {httpx_modules}"
        )

    def test_no_requests_import(self) -> None:
        # requests moze biti importovan od strane test infrastructure
        # — samo provjeriti da null_advisor.py source ne sadrzi 'import requests'
        import inspect

        from parser_studio.adapters.ai import null_advisor

        source = inspect.getsource(null_advisor)
        assert "import requests" not in source
        assert "import httpx" not in source
        assert "import openai" not in source
        assert "import anthropic" not in source

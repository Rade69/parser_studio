# Tests: Candidate.
from __future__ import annotations

import pytest

from parser_studio.domain.evidence import Candidate, Locator


def _make_locator() -> Locator:
    return Locator(source_path="f.xlsx", kind="excel", sheet="S1", row=1, col=2)


class TestCandidateConstruction:
    def test_minimum(self) -> None:
        cand = Candidate(
            field="quantity",
            raw_value="10",
            normalized_value=10.0,
            locator=_make_locator(),
            evidence="header='Quantity'",
            producer_id="excel_header",
        )
        assert cand.field == "quantity"
        assert cand.normalized_value == 10.0
        assert cand.ai_assisted is False
        assert cand.issues == ()

    def test_ai_assisted_with_issues(self) -> None:
        cand = Candidate(
            field="tariff",
            raw_value="1234.56.78",
            normalized_value=None,
            locator=_make_locator(),
            evidence="header='Tariff'",
            producer_id="ai_vision",
            ai_assisted=True,
            issues=("AMBIGUOUS_FORMAT", "REQUIRES_HUMAN_REVIEW"),
        )
        assert cand.ai_assisted is True
        assert cand.issues == ("AMBIGUOUS_FORMAT", "REQUIRES_HUMAN_REVIEW")


class TestCandidateFrozen:
    def test_mutation_raises(self) -> None:
        cand = Candidate(
            field="quantity",
            raw_value="10",
            normalized_value=10.0,
            locator=_make_locator(),
            evidence="",
            producer_id="p",
        )
        with pytest.raises((AttributeError, Exception)):
            cand.field = "price"  # type: ignore[misc]


class TestCandidateValidation:
    def test_empty_field_raises(self) -> None:
        with pytest.raises(ValueError, match="field"):
            Candidate(
                field="",
                raw_value="x",
                normalized_value="x",
                locator=_make_locator(),
                evidence="",
                producer_id="p",
            )

    def test_empty_producer_id_raises(self) -> None:
        with pytest.raises(ValueError, match="producer_id"):
            Candidate(
                field="x",
                raw_value="x",
                normalized_value="x",
                locator=_make_locator(),
                evidence="",
                producer_id="",
            )

    def test_invalid_locator_raises(self) -> None:
        with pytest.raises(TypeError, match="locator"):
            Candidate(
                field="x",
                raw_value="x",
                normalized_value="x",
                locator="not-locator",  # type: ignore[arg-type]
                evidence="",
                producer_id="p",
            )

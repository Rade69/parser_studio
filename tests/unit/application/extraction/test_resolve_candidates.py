# Tests: application/extraction/test_resolve_candidates.
"""Testovi za ResolveCandidates use case (V3_2 C3)."""
from __future__ import annotations

import pytest

from parser_studio.application.extraction.resolve_candidates import (
    ResolutionStrategy,
    ResolveCandidates,
    ResolveRequest,
    ResolveResult,
)
from parser_studio.domain.evidence import Candidate, DocumentEvidence, Locator
from parser_studio.domain.extraction.extraction_draft import ExtractionDraft


def _make_locator() -> Locator:
    return Locator(source_path="/test.xlsx", kind="excel", sheet="Sheet1")


def _make_candidate(
    field: str,
    value: object,
    producer_id: str,
) -> Candidate:
    return Candidate(
        field=field,
        raw_value=value,
        normalized_value=str(value).strip(),
        locator=_make_locator(),
        evidence=f"{producer_id} extracted",
        producer_id=producer_id,
    )


def _make_doc(document_id: str = "doc-1") -> DocumentEvidence:
    return DocumentEvidence(document_id=document_id, source_path="/test.xlsx")


def _make_draft(*candidates: Candidate) -> ExtractionDraft:
    """Group candidates by field automatski."""
    by_field: dict[str, list[Candidate]] = {}
    for c in candidates:
        by_field.setdefault(c.field, []).append(c)
    return ExtractionDraft(
        document_id="doc-1",
        document=_make_doc(),
        candidates_by_field={f: tuple(cs) for f, cs in by_field.items()},
    )


class TestResolutionStrategy:
    def test_three_strategies_defined(self) -> None:
        assert ResolutionStrategy.FIRST_MATCH.value == "first_match"
        assert ResolutionStrategy.HIGHEST_CONFIDENCE.value == "highest_confidence"
        assert ResolutionStrategy.CONSENSUS.value == "consensus"


class TestResolveRequest:
    def test_default_first_match(self) -> None:
        draft = _make_draft(_make_candidate("x", "1", "excel_header"))
        req = ResolveRequest(draft=draft)
        assert req.strategy == ResolutionStrategy.FIRST_MATCH

    def test_invalid_draft_raises(self) -> None:
        with pytest.raises(TypeError, match="ExtractionDraft"):
            ResolveRequest(draft="not-a-draft")  # type: ignore[arg-type]

    def test_invalid_strategy_raises(self) -> None:
        with pytest.raises(TypeError, match="ResolutionStrategy"):
            ResolveRequest(
                draft=_make_draft(_make_candidate("x", "1", "excel_header")),
                strategy="invalid",  # type: ignore[arg-type]
            )


class TestResolveCandidatesFirstMatch:
    def test_single_candidate_no_conflict(self) -> None:
        draft = _make_draft(_make_candidate("invoice_number", "INV-001", "excel_header"))
        result = ResolveCandidates().execute(ResolveRequest(draft=draft))
        assert "invoice_number" in result.resolved_by_field
        assert result.resolved_by_field["invoice_number"].raw_value == "INV-001"
        assert result.conflicts == ()

    def test_multiple_candidates_with_conflict(self) -> None:
        """2+ kandidati za isto polje → conflict + first chosen."""
        draft = _make_draft(
            _make_candidate("invoice_number", "INV-001", "excel_header"),
            _make_candidate("invoice_number", "INV-001-label", "label_right"),
        )
        result = ResolveCandidates().execute(ResolveRequest(draft=draft))
        assert len(result.conflicts) == 1
        # First match: excel_header (priority 0.90) wins
        assert result.conflicts[0].chosen.producer_id == "excel_header"

    def test_priority_order(self) -> None:
        """excel_header > label_right > value_shape po confidence."""
        draft = _make_draft(
            _make_candidate("kolicina", "10", "value_shape"),       # 0.60
            _make_candidate("kolicina", "10", "label_right"),      # 0.80
            _make_candidate("kolicina", "10", "excel_header"),     # 0.90
        )
        result = ResolveCandidates().execute(ResolveRequest(draft=draft))
        assert result.conflicts[0].chosen.producer_id == "excel_header"

    def test_no_candidates_marks_unresolved(self) -> None:
        """Polje bez kandidata ide u unresolved."""
        draft = ExtractionDraft(
            document_id="doc-1",
            document=_make_doc(),
            candidates_by_field={},  # prazan dict
        )
        result = ResolveCandidates().execute(ResolveRequest(draft=draft))
        assert result.resolved_by_field == {}
        assert result.unresolved == ()

    def test_explicit_empty_field_unresolved(self) -> None:
        """Polje sa praznim tuple kandidata → unresolved."""
        draft = ExtractionDraft(
            document_id="doc-1",
            document=_make_doc(),
            candidates_by_field={"invoice_number": ()},
        )
        result = ResolveCandidates().execute(ResolveRequest(draft=draft))
        assert "invoice_number" in result.unresolved


class TestResolveCandidatesHighestConfidence:
    def test_highest_confidence_wins(self) -> None:
        draft = _make_draft(
            _make_candidate("x", "A", "value_shape"),     # 0.60
            _make_candidate("x", "A", "excel_header"),   # 0.90
            _make_candidate("x", "A", "label_right"),    # 0.80
        )
        result = ResolveCandidates().execute(
            ResolveRequest(draft=draft, strategy=ResolutionStrategy.HIGHEST_CONFIDENCE)
        )
        assert result.resolved_by_field["x"].producer_id == "excel_header"

    def test_unknown_producer_fallback(self) -> None:
        """Producer bez confidence defaulta — fallback."""
        draft = _make_draft(
            _make_candidate("x", "A", "unknown_producer"),  # default 0.0
            _make_candidate("x", "A", "excel_header"),     # 0.90
        )
        result = ResolveCandidates().execute(
            ResolveRequest(draft=draft, strategy=ResolutionStrategy.HIGHEST_CONFIDENCE)
        )
        assert result.resolved_by_field["x"].producer_id == "excel_header"


class TestResolveCandidatesConsensus:
    def test_consensus_when_all_agree(self) -> None:
        """Svi kandidati imaju istu vrijednost — consensus, BEZ conflict-a."""
        draft = _make_draft(
            _make_candidate("invoice_number", "INV-001", "excel_header"),
            _make_candidate("invoice_number", "INV-001", "label_right"),
            _make_candidate("invoice_number", "INV-001", "value_shape"),
        )
        result = ResolveCandidates().execute(
            ResolveRequest(draft=draft, strategy=ResolutionStrategy.CONSENSUS)
        )
        assert result.conflicts == ()
        assert result.resolved_by_field["invoice_number"].raw_value == "INV-001"

    def test_consensus_fails_on_disagreement(self) -> None:
        """Kandidati imaju RAZLICITE vrijednosti — fallback na FIRST_MATCH, conflict."""
        draft = _make_draft(
            _make_candidate("invoice_number", "INV-001", "excel_header"),
            _make_candidate("invoice_number", "INV-999", "label_right"),
        )
        result = ResolveCandidates().execute(
            ResolveRequest(draft=draft, strategy=ResolutionStrategy.CONSENSUS)
        )
        # Conflict + fallback na excel_header (priority)
        assert len(result.conflicts) == 1
        assert result.conflicts[0].reason.startswith("consensus failed")
        assert result.conflicts[0].chosen.producer_id == "excel_header"

    def test_consensus_case_insensitive(self) -> None:
        """Whitespace trim u normalized_value."""
        draft = _make_draft(
            _make_candidate("invoice_number", "INV-001", "excel_header"),
            _make_candidate("invoice_number", " INV-001 ", "label_right"),
        )
        result = ResolveCandidates().execute(
            ResolveRequest(draft=draft, strategy=ResolutionStrategy.CONSENSUS)
        )
        assert result.conflicts == ()

    def test_single_candidate_consensus_no_conflict(self) -> None:
        draft = _make_draft(_make_candidate("x", "1", "excel_header"))
        result = ResolveCandidates().execute(
            ResolveRequest(draft=draft, strategy=ResolutionStrategy.CONSENSUS)
        )
        assert result.conflicts == ()


class TestResolveResult:
    def test_construction(self) -> None:
        result = ResolveResult(
            resolved_by_field={"x": _make_candidate("x", "1", "excel_header")},
            conflicts=(),
            unresolved=(),
        )
        assert "x" in result.resolved_by_field
        assert result.conflicts == ()
        assert result.unresolved == ()

    def test_frozen(self) -> None:
        from dataclasses import FrozenInstanceError

        result = ResolveResult(resolved_by_field={}, conflicts=(), unresolved=())
        with pytest.raises(FrozenInstanceError):
            result.unresolved = ("x",)  # type: ignore[misc]


class TestDeterminism:
    def test_first_match_is_deterministic(self) -> None:
        """Isti input → isti output uvijek."""
        draft = _make_draft(
            _make_candidate("x", "A", "label_right"),
            _make_candidate("x", "A", "excel_header"),
            _make_candidate("x", "A", "value_shape"),
        )
        results = set()
        for _ in range(5):
            r = ResolveCandidates().execute(ResolveRequest(draft=draft))
            results.add(r.resolved_by_field["x"].producer_id)
        assert len(results) == 1
        assert results == {"excel_header"}

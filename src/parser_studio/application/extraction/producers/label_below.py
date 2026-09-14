# Application: extraction/producers/label_below.
# Posjeduje: LabelBelowProducer implementacija CandidateProducer.
# Zna za: domain.evidence, domain.concepts, ports.candidate_producer.
# Ne zna za: SQLite, PySide6, Docling, contract.
"""LabelBelowProducer — pronalazi vrijednost ISPOD labele u sljedecem redu.

Tipican pattern: u tabeli "Broj fakture" u A1, "12345" u A2.
Razlika od LabelRightProducer: trazi u ISTOM col, SLJEDECEM row.
"""
from __future__ import annotations

from parser_studio.domain.concepts import ConceptLibrary
from parser_studio.domain.evidence import Candidate, DocumentEvidence
from parser_studio.domain.extraction.header_matching import normalize_header
from parser_studio.ports.candidate_producer import (
    FieldContext,
)


class LabelBelowProducer:
    """Predlaze Candidate vrijednosti iz celije ispod labele."""

    producer_id: str = "label_below"

    def __init__(self, library: ConceptLibrary | None = None) -> None:
        self._library = library or ConceptLibrary()

    def supports(self, context: FieldContext) -> bool:
        return True

    def propose(
        self, document: DocumentEvidence, context: FieldContext
    ) -> list[Candidate]:
        concept = self._library.get(context.field, context.language)
        if concept is None:
            return []

        candidates: list[Candidate] = []
        # Index po (sheet, col) -> row -> Evidence
        cell_index: dict[tuple[str | None, int | None], dict[int | None, object]] = {}
        for ev in document.cells:
            key = (ev.locator.sheet, ev.locator.col)
            cell_index.setdefault(key, {})[ev.locator.row] = ev

        for ev in document.cells:
            if not ev.raw_text:
                continue
            normalized = normalize_header(ev.raw_text)
            if concept.matches_text(normalized):
                key = (ev.locator.sheet, ev.locator.col)
                col_cells = cell_index.get(key, {})
                below_cell = col_cells.get((ev.locator.row or 0) + 1 if ev.locator.row else None)
                if below_cell is None:
                    continue
                # type: ignore[assignment]
                if not isinstance(below_cell, type(ev)):
                    continue
                candidates.append(
                    Candidate(
                        field=context.field,
                        raw_value=below_cell.raw_value,
                        normalized_value=str(below_cell.raw_value).strip()
                        if below_cell.raw_value is not None
                        else "",
                        locator=below_cell.locator,
                        evidence=f"label-below match: '{ev.raw_text}' -> '{below_cell.raw_text}'",
                        producer_id=self.producer_id,
                    )
                )
        return candidates


__all__ = ["LabelBelowProducer"]

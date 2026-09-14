# Application: extraction/producers/label_right.
# Posjeduje: LabelRightProducer implementacija CandidateProducer.
# Zna za: domain.evidence, domain.concepts, ports.candidate_producer.
# Ne zna za: SQLite, PySide6, Docling, contract.
"""LabelRightProducer — pronalazi vrijednost DESNO od labele u istom redu.

Tipičan pattern: "Broj fakture: 12345" gdje je "Broj fakture" labela u celiji A1,
a "12345" je vrijednost u celiji B1.

Koristi ConceptLibrary (FAZA C/C1) za match labela prema canonical polju.
"""
from __future__ import annotations

from parser_studio.domain.concepts import ConceptLibrary
from parser_studio.domain.evidence import Candidate, DocumentEvidence
from parser_studio.domain.extraction.header_matching import normalize_header
from parser_studio.ports.candidate_producer import (
    FieldContext,
)


class LabelRightProducer:
    """Predlaze Candidate vrijednosti iz celije desno od labele u istom redu."""

    producer_id: str = "label_right"

    def __init__(self, library: ConceptLibrary | None = None) -> None:
        self._library = library or ConceptLibrary()

    def supports(self, context: FieldContext) -> bool:
        """Sva polja — label-right je generička strategija."""
        return True

    def propose(
        self, document: DocumentEvidence, context: FieldContext
    ) -> list[Candidate]:
        """Pronadji celiju gdje je normalized_text == concept.synonym (za zadano polje),
        vrati Candidate sa vrijednoscu iz iste sheet/row, col+1.
        """
        # Pronadji sinonime za trazeno polje
        concept = self._library.get(context.field, context.language)
        if concept is None:
            return []

        candidates: list[Candidate] = []
        # Build index po (sheet, row) -> col -> Evidence
        cell_index: dict[tuple[str | None, int | None], dict[int | None, object]] = {}
        for ev in document.cells:
            sheet = ev.locator.sheet
            row = ev.locator.row
            col = ev.locator.col
            key = (sheet, row)
            cell_index.setdefault(key, {})[col] = ev

        # Iteracija kroz celije; ako match-uje labelu, uzmi celiju desno
        for ev in document.cells:
            if not ev.raw_text:
                continue
            normalized = normalize_header(ev.raw_text)
            if concept.matches_text(normalized):
                # Nadi celiju desno (col + 1)
                key = (ev.locator.sheet, ev.locator.row)
                row_cells = cell_index.get(key, {})
                right_cell = row_cells.get((ev.locator.col or 0) + 1 if ev.locator.col else None)
                if right_cell is None:
                    continue
                # type: ignore[assignment]
                if not isinstance(right_cell, type(ev)):
                    continue
                candidates.append(
                    Candidate(
                        field=context.field,
                        raw_value=right_cell.raw_value,
                        normalized_value=str(right_cell.raw_value).strip()
                        if right_cell.raw_value is not None
                        else "",
                        locator=right_cell.locator,
                        evidence=f"label-right match: '{ev.raw_text}' -> '{right_cell.raw_text}'",
                        producer_id=self.producer_id,
                    )
                )
        return candidates


__all__ = ["LabelRightProducer"]

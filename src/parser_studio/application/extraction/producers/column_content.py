# Application: extraction/producers/column_content.
# Posjeduje: ColumnContentProducer implementacija CandidateProducer.
# Zna za: domain.evidence, domain.concepts, ports.candidate_producer.
# Ne zna za: SQLite, PySide6, Docling, contract.
"""ColumnContentProducer — vraca SVE vrijednosti u identificiranoj koloni.

Alternativa za TableHeaderProducer: umjesto jednog Kandidata po row,
vraca tuple Kandidata gdje svaki kandidat predstavlja jednu celiju u koloni.
"""
from __future__ import annotations

from parser_studio.domain.concepts import ConceptLibrary
from parser_studio.domain.evidence import Candidate, DocumentEvidence
from parser_studio.domain.extraction.header_matching import normalize_header
from parser_studio.ports.candidate_producer import (
    FieldContext,
)


class ColumnContentProducer:
    """Vraca Kandidate za SVE celije u koloni identificiranoj po concept labeli.

    Strategija:
    1. Pronadji prvi red gdje bilo koja celija match-a concept labelu
    2. Zabiljezi col index
    3. Vrati SVE celije ispod u tom col-u (po row-u)
    """

    producer_id: str = "column_content"

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
        # Group by sheet
        sheets: dict[str, list[object]] = {}
        for ev in document.cells:
            sheet = ev.locator.sheet or ""
            sheets.setdefault(sheet, []).append(ev)

        for sheet, cells in sheets.items():
            sheet_candidates = self._column_candidates_for_sheet(sheet, cells, context.field, concept)
            candidates.extend(sheet_candidates)

        return candidates

    def _column_candidates_for_sheet(
        self,
        sheet: str,
        cells: list[object],
        field: str,
        concept: object,
    ) -> list[Candidate]:
        """Za jedan sheet: pronadji header row, target col, vrati sve celije u target col."""
        cell_by_row: dict[int, dict[int, object]] = {}
        for ev in cells:
            row = ev.locator.row or 0
            col = ev.locator.col or 0
            cell_by_row.setdefault(row, {})[col] = ev

        # Find header row + target col (prvi match)
        target_col = None
        header_row_idx = None
        for row_idx in sorted(cell_by_row.keys()):
            for col_idx, ev in cell_by_row[row_idx].items():
                if not ev.raw_text:
                    continue
                normalized = normalize_header(ev.raw_text)
                if concept.matches_text(normalized):
                    target_col = col_idx
                    header_row_idx = row_idx
                    break
            if target_col is not None:
                break

        if target_col is None:
            return []

        # Vrati sve celije u target_col IZNAD header-a (za invoice) — NE za items
        # Za items, vrati sve ispod header-a (bez prvog reda ispod, jer je to vec value row)
        candidates: list[Candidate] = []
        for row_idx in sorted(cell_by_row.keys()):
            ev = cell_by_row[row_idx].get(target_col)
            if ev is None or ev.raw_value is None:
                continue
            # type: ignore[attr-defined]
            candidates.append(
                Candidate(
                    field=field,
                    raw_value=ev.raw_value,
                    normalized_value=str(ev.raw_value).strip(),
                    locator=ev.locator,
                    evidence=(
                        f"column-content match: sheet={sheet}, "
                        f"header_row={header_row_idx}, target_col={target_col}, "
                        f"value_row={row_idx}"
                    ),
                    producer_id=self.producer_id,
                )
            )
        return candidates


__all__ = ["ColumnContentProducer"]

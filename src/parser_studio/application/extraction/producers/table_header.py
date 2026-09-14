# Application: extraction/producers/table_header.
# Posjeduje: TableHeaderProducer implementacija CandidateProducer.
# Zna za: domain.evidence, domain.concepts, ports.candidate_producer.
# Ne zna za: SQLite, PySide6, Docling, contract.
"""TableHeaderProducer — identifikuje header red tabele i mapira kolone.

Koristi ConceptLibrary za match header kolona prema canonical polju.
Vraca Kandidate za SVE redove u tabeli ispod header reda (za items).

Razlika od ExcelHeaderProducer (A4): ovaj producer je fokusiran na items
tabele (sa vise redova), gdje svaki red je jedan item. Vraca vise kandidata
po polju (jedan po item row-u), dok ExcelHeaderProducer vraca jedan
kandidat po polju (za invoice header).
"""
from __future__ import annotations

from parser_studio.domain.concepts import ConceptLibrary
from parser_studio.domain.evidence import Candidate, DocumentEvidence
from parser_studio.domain.extraction.header_matching import normalize_header
from parser_studio.ports.candidate_producer import (
    FieldContext,
)


class TableHeaderProducer:
    """Identifikuje header red items tabele i vraca Candidate za svaki row.

    Za razliku od ExcelHeaderProducer (koji vraca jedan best-match kandidat),
    TableHeaderProducer vraca JEDAN Candidate po item row-u, gdje svaki
    Candidate ima:
    - field: canonical polje (iz header match-a)
    - raw_value: vrijednost u celiji (row, identified_col)
    - locator: pozicija u dokumentu
    """

    producer_id: str = "table_header"

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

        # Grupiraj celije po sheet-u
        sheets: dict[str, list[object]] = {}
        for ev in document.cells:
            sheet = ev.locator.sheet or ""
            sheets.setdefault(sheet, []).append(ev)

        candidates: list[Candidate] = []
        for sheet, cells in sheets.items():
            sheet_candidates = self._find_column_candidates_in_sheet(
                sheet, cells, context.field, concept
            )
            candidates.extend(sheet_candidates)

        return candidates

    def _find_column_candidates_in_sheet(
        self,
        sheet: str,
        cells: list[object],
        field: str,
        concept: object,
    ) -> list[Candidate]:
        """Za jedan sheet, pronadji header red, identificiraj kolonu za field,
        vrati Candidate za svaki row ispod header-a.
        """
        # Pronadji header row (prvi row koji sadrzi celiju ciji normalized_text
        # match-a bilo koji concept za trazeno polje)
        cell_by_row: dict[int, dict[int, object]] = {}
        for ev in cells:
            row = ev.locator.row or 0
            col = ev.locator.col or 0
            cell_by_row.setdefault(row, {})[col] = ev

        # Pronadji prvi red gdje neka celija match-a nas concept
        header_row_idx = None
        target_col = None
        for row_idx in sorted(cell_by_row.keys()):
            row_cells = cell_by_row[row_idx]
            for col_idx, ev in row_cells.items():
                if not ev.raw_text:
                    continue
                normalized = normalize_header(ev.raw_text)
                if concept.matches_text(normalized):
                    header_row_idx = row_idx
                    target_col = col_idx
                    break
            if header_row_idx is not None:
                break

        if header_row_idx is None or target_col is None:
            return []

        # Za svaki row ispod header-a, vrati Candidate iz target_col
        candidates: list[Candidate] = []
        for row_idx in sorted(cell_by_row.keys()):
            if row_idx <= header_row_idx:
                continue
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
                        f"table-header match: sheet={sheet}, "
                        f"header_row={header_row_idx}, target_col={target_col}"
                    ),
                    producer_id=self.producer_id,
                )
            )
        return candidates


__all__ = ["TableHeaderProducer"]

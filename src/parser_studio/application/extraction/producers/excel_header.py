# Application: extraction/producers/excel_header.
# Posjeduje: ExcelHeaderProducer implementacija CandidateProducer.
# Zna za: domain.evidence, domain.invoice.fields, domain.extraction.header_matching, ports.candidate_producer.
# Ne zna za: SQLite, PySide6, Docling, openpyxl/xlrd, contract (radi nad DocumentEvidence).
"""ExcelHeaderProducer — predlaze Candidate vrijednosti iz Excel sheet-ova.

Orkestracija:
1. Pronadji sheet koji izgleda kao items tabela
2. Pronadji header red
3. Identificiraj kolone (identify_columns)
4. Za trazeno polje, vrati kandidate iz svih redova ispod header-a

Implementira CandidateProducer Protocol iz ports/candidate_producer.py.
"""
from __future__ import annotations

from typing import Any

from parser_studio.application.extraction.producers._sheet_utils import (
    extract_rows_from_document,
)
from parser_studio.domain.evidence import Candidate, DocumentEvidence, Evidence, Locator
from parser_studio.domain.extraction.header_matching import (
    identify_columns,
    is_footer_text,
    normalize_header,
)
from parser_studio.domain.invoice.fields import (
    _ESSENTIAL_FIELDS,
    _FOOTER_PREFIXES,
    COLUMN_ALIASES,
)
from parser_studio.ports.candidate_producer import (
    CandidateProducer,
    FieldContext,
)


class ExcelHeaderProducer:
    """Predlaze Candidate vrijednosti iz Excel sheet header-a."""

    producer_id: str = "excel_header"

    def supports(self, context: FieldContext) -> bool:
        """Podrzava sva polja; specificnost moze ici kroz context.profile_version."""
        return True

    def propose(
        self, document: DocumentEvidence, context: FieldContext
    ) -> list[Candidate]:
        """Pronadji header red, identificiraj kolone, vrati Candidate za trazeno polje."""
        sheet_data = self._find_header_sheet(document)
        if sheet_data is None:
            return []

        sheet_name = sheet_data["name"]
        rows = sheet_data["rows"]
        header_row_idx = self._find_header_row(rows)
        if header_row_idx < 0:
            return []

        header_cells = rows[header_row_idx]
        column_map = identify_columns(header_cells)

        if context.field not in column_map:
            return []

        col_idx = column_map[context.field]

        candidates: list[Candidate] = []
        for row_idx in range(header_row_idx + 1, len(rows)):
            if not self._is_data_row(rows, row_idx, column_map):
                continue
            if col_idx >= len(rows[row_idx]):
                continue
            value = rows[row_idx][col_idx]
            if value is None or value == "":
                continue
            locator = Locator(
                source_path=document.source_path,
                kind="excel",
                sheet=sheet_name,
                row=row_idx + 1,
                col=col_idx + 1,
            )
            raw_text = "" if value is None else str(value).strip()
            evidence_obj = Evidence(
                raw_value=value,
                raw_text=raw_text,
                locator=locator,
                element_type="excel_cell",
                source_id=self.producer_id,
            )
            evidence_desc = (
                f"{evidence_obj.element_type}@{evidence_obj.locator.sheet}!"
                f"r{evidence_obj.locator.row}c{evidence_obj.locator.col}"
            )
            candidate = Candidate(
                field=context.field,
                raw_value=value,
                normalized_value=raw_text,
                locator=locator,
                evidence=evidence_desc,
                producer_id=self.producer_id,
            )
            candidates.append(candidate)
        return candidates

    def _find_header_sheet(
        self, document: DocumentEvidence
    ) -> dict[str, Any] | None:
        """Pronadji sheet koji sadrzi prepoznatljiv header red."""
        for sheet_name in document.pages:
            rows = extract_rows_from_document(document, sheet_name)
            if not rows:
                continue
            if self._find_header_row(rows) >= 0:
                return {"name": sheet_name, "rows": rows}
        return None

    def _find_header_row(self, rows: list[list[Any]]) -> int:
        """Pronadji prvi red koji ima 2+ prepoznata alias-a (ILI sadrzi _ESSENTIAL)."""
        best_idx = -1
        best_count = 0
        for idx, row in enumerate(rows[:30]):
            cells = ["" if v is None else str(v) for v in row]
            if not any(c.strip() for c in cells):
                continue
            mapping = identify_columns(cells)
            essential_match = any(f in mapping for f in _ESSENTIAL_FIELDS)
            count = len(mapping)
            if essential_match and (count > best_count or best_idx == -1):
                best_idx = idx
                best_count = count
            elif count > best_count + 1 and best_idx == -1:
                # Fallback: samo po broju matcheva (>= 3)
                best_idx = idx
                best_count = count
        if best_count < 2 and best_idx == -1:
            return -1
        return best_idx

    def _is_data_row(
        self,
        rows: list[list[Any]],
        row_idx: int,
        mapping: dict[str, int],
    ) -> bool:
        """Red je stavka ako ima sadrzaj u bar jednoj _ESSENTIAL koloni I nije footer."""
        if row_idx >= len(rows):
            return False
        has_content = False
        for field_name in _ESSENTIAL_FIELDS:
            col = mapping.get(field_name)
            if col is not None and col < len(rows[row_idx]):
                if str(rows[row_idx][col]).strip():
                    has_content = True
                    break
        if not has_content:
            return False
        return not self._is_footer_row(rows, row_idx, mapping)

    def _is_footer_row(
        self,
        rows: list[list[Any]],
        row_idx: int,
        mapping: dict[str, int],
    ) -> bool:
        """Da li red pocinje nekim od poznatih footer pojmova."""
        for field_name in _ESSENTIAL_FIELDS:
            col = mapping.get(field_name)
            if col is None or col >= len(rows[row_idx]):
                continue
            text = normalize_header(rows[row_idx][col])
            if text and is_footer_text(text):
                return True
        return False


__all__ = ["ExcelHeaderProducer"]

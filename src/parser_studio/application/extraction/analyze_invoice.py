# Application: extraction/analyze_invoice.
# Posjeduje: AnalyzeInvoice use case + AnalyzeRequest.
# Zna za: ports.candidate_producer, domain.extraction.extraction_draft.
# Ne zna za: SQLite, PySide6, Docling, openpyxl/xlrd, contract.
"""AnalyzeInvoice use case — pokreće Producer-e, agregira Candidate-e u ExtractionDraft.
"""
from __future__ import annotations

from dataclasses import dataclass

from parser_studio.domain.evidence import Candidate, DocumentEvidence
from parser_studio.domain.extraction.extraction_draft import ExtractionDraft
from parser_studio.ports.candidate_producer import (
    CandidateProducer,
    FieldContext,
)


@dataclass(frozen=True, slots=True)
class AnalyzeRequest:
    document: DocumentEvidence
    target_fields: tuple[str, ...]
    language: str = "bs"


class AnalyzeInvoice:
    """Use case: pokreće CandidateProducer-e, agregira kandidate po polju."""

    def __init__(self, producers: tuple[CandidateProducer, ...]) -> None:
        if not producers:
            raise ValueError("AnalyzeInvoice zahtijeva bar jedan CandidateProducer")
        self._producers = producers

    def execute(self, request: AnalyzeRequest) -> ExtractionDraft:
        """Pokreni sve Producer-e za sva target_fields, vrati ExtractionDraft."""
        candidates_by_field: dict[str, list[Candidate]] = {}
        for producer in self._producers:
            for field in request.target_fields:
                ctx = FieldContext(
                    document_id=request.document.document_id,
                    field=field,
                    language=request.language,
                )
                if not producer.supports(ctx):
                    continue
                for cand in producer.propose(request.document, ctx):
                    candidates_by_field.setdefault(field, []).append(cand)
        frozen = {f: tuple(cs) for f, cs in candidates_by_field.items()}
        return ExtractionDraft(
            document_id=request.document.document_id,
            document=request.document,
            candidates_by_field=frozen,
        )

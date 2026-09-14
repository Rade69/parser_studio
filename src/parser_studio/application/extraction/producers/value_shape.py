# Application: extraction/producers/value_shape.
# Posjeduje: ValueShapeProducer implementacija CandidateProducer.
# Zna za: domain.evidence, ports.candidate_producer.
# Ne zna za: SQLite, PySide6, Docling, contract.
r"""ValueShapeProducer — regex/shape match po tipu polja.

Za razliku od ostalih producer-a (koji match-uju labelu), ValueShapeProducer
match-uje SAMU VRIJEDNOST prema shape-u polja:
- invoice_number: pattern "^[A-Z]{0,4}[-/]?\d{1,5}[-/]?\d{0,5}$"
- invoice_date: ISO 8601 datum pattern
- currency: 3 slova (ISO 4217)
- iznos, jedinicna_cijena, kolicina, bruto_masa, neto_masa: numeričke vrijednosti

Vraca Kandidate za SVE celije ciji sadrzaj match-uje shape-u polja.
"""
from __future__ import annotations

import re

from parser_studio.domain.evidence import Candidate, DocumentEvidence
from parser_studio.ports.candidate_producer import (
    FieldContext,
)

# Pattern po polju
_PATTERNS: dict[str, re.Pattern[str]] = {
    # Invoice No / Faktura-1 / 1234 / 1234-56
    "invoice_number": re.compile(
        r"^[A-Z]{0,4}[-/]?\d{1,5}[-/]?\d{0,5}$",
        re.IGNORECASE,
    ),
    # Datum: ISO 8601 (YYYY-MM-DD) ili DD.MM.YYYY ili DD/MM/YYYY
    "invoice_date": re.compile(
        r"^\d{4}[-/.]\d{1,2}[-/.]\d{1,2}$|^\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}$",
    ),
    # Currency: 3 slova (EUR, USD, BAM, ...)
    "currency": re.compile(r"^[A-Z]{3}$"),
    # Seller/Buyer tax ID: cifre, moze imati prefix
    "seller_tax_id": re.compile(r"^\d{8,15}$|^\d{4}\d{6,13}$"),
    "buyer_tax_id": re.compile(r"^\d{8,15}$|^\d{4}\d{6,13}$"),
    # Numerička polja: decimal ili integer
    "kolicina": re.compile(r"^\d+([.,]\d+)?$"),
    "jedinicna_cijena": re.compile(r"^\d+([.,]\d+)?$"),
    "iznos": re.compile(r"^\d+([.,]\d+)?$"),
    "neto_masa": re.compile(r"^\d+([.,]\d+)?$"),
    "bruto_masa": re.compile(r"^\d+([.,]\d+)?$"),
    # Tarifni broj: digits, moze imati tacku
    "tarifni_broj": re.compile(r"^\d{6,10}(\.\d+)?$"),
    # Jedinica mjere: 2-4 slova
    "jedinica_mjere": re.compile(r"^[A-Za-z]{2,5}$"),
    # Zemlja porijekla: 2 velika slova (ISO 3166-1 alpha-2)
    "zemlja_porijekla": re.compile(r"^[A-Z]{2}$"),
}


class ValueShapeProducer:
    """Predlaze Candidate za celije cije vrijednosti match-uju shape-u polja."""

    producer_id: str = "value_shape"

    def supports(self, context: FieldContext) -> bool:
        return context.field in _PATTERNS

    def propose(
        self, document: DocumentEvidence, context: FieldContext
    ) -> list[Candidate]:
        pattern = _PATTERNS.get(context.field)
        if pattern is None:
            return []

        candidates: list[Candidate] = []
        for ev in document.cells:
            if not ev.raw_text:
                continue
            text = ev.raw_text.strip()
            if pattern.match(text):
                candidates.append(
                    Candidate(
                        field=context.field,
                        raw_value=ev.raw_value,
                        normalized_value=text,
                        locator=ev.locator,
                        evidence=f"value-shape match: '{text}' matches {context.field} pattern",
                        producer_id=self.producer_id,
                    )
                )
        return candidates


__all__ = ["ValueShapeProducer"]

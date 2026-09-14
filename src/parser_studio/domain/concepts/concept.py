# Domain: concepts/concept.
# Posjeduje: Concept dataclass.
# Ne zna za: SQLite, PySide6, Docling, openpyxl, contract, adapters.
"""Concept — sinonimi i kontekstualne fraze za jedno polje u jednom jeziku.

Koriste ga Producer-i (C2) za match labela u dokumentu.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Concept:
    """Sinonimi i kontekstualne fraze za jedno polje u jednom jeziku.

    Atributi:
        field: Canonical ime polja (npr. "invoice_number", "datum_fakture").
        language: ISO 639-1 kod (npr. "bs", "hr", "sr", "en").
        synonyms: Lista sinonima/aliasa (npr. ["Broj fakture", "Invoice No", "Inv No"]).
        context_phrases: Fraze koje ukazuju na polje u kontekstu
            (npr. ["ukupno za plaćanje", "total invoice amount"]).
    """

    field: str
    language: str
    synonyms: tuple[str, ...]
    context_phrases: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.field:
            raise ValueError("field ne moze biti prazan string")
        if not self.language:
            raise ValueError("language ne moze biti prazan string")
        if len(self.language) != 2:
            raise ValueError(
                f"language mora biti ISO 639-1 2-char kod, dobijeno {self.language!r}"
            )
        if not self.synonyms:
            raise ValueError(
                f"synonyms mora imati bar jedan element za field={self.field}, "
                f"language={self.language}"
            )
        if not all(isinstance(s, str) and s for s in self.synonyms):
            raise TypeError("synonyms moraju biti neprazni stringovi")
        if not all(isinstance(p, str) and p for p in self.context_phrases):
            raise TypeError("context_phrases moraju biti neprazni stringovi")

    def matches_text(self, normalized_text: str) -> bool:
        """True ako normalized_text match-a bilo koji sinonim ovog koncepta.

        Koristi exact match (case-insensitive, već normalized).
        Za fuzzy match koristiti ConceptLibrary.match_alias sa rapidfuzz.
        """
        if not normalized_text:
            return False
        text = normalized_text.strip().lower()
        return any(syn.strip().lower() == text for syn in self.synonyms)

    def has_phrase(self, normalized_text: str) -> bool:
        """True ako normalized_text SADRZI bilo koju context_phrase."""
        if not normalized_text:
            return False
        text = normalized_text.lower()
        return any(phrase.lower() in text for phrase in self.context_phrases)


__all__ = ["Concept"]

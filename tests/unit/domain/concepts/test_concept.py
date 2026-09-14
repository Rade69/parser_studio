# Tests: domain/concepts/test_concept.
"""Testovi za Concept dataclass (V3_2 C1)."""
from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from parser_studio.domain.concepts import Concept


class TestConceptConstruction:
    def test_minimal(self) -> None:
        c = Concept(
            field="invoice_number",
            language="bs",
            synonyms=("Broj fakture",),
        )
        assert c.field == "invoice_number"
        assert c.language == "bs"
        assert c.synonyms == ("Broj fakture",)
        assert c.context_phrases == ()

    def test_with_phrases(self) -> None:
        c = Concept(
            field="invoice_number",
            language="bs",
            synonyms=("Broj fakture",),
            context_phrases=("broj fakture",),
        )
        assert c.context_phrases == ("broj fakture",)

    def test_empty_field_raises(self) -> None:
        with pytest.raises(ValueError, match="field ne moze biti prazan"):
            Concept(field="", language="bs", synonyms=("x",))

    def test_empty_language_raises(self) -> None:
        with pytest.raises(ValueError, match="language ne moze biti prazan"):
            Concept(field="x", language="", synonyms=("y",))

    def test_long_language_raises(self) -> None:
        with pytest.raises(ValueError, match="ISO 639-1"):
            Concept(field="x", language="bs-Latn", synonyms=("y",))

    def test_empty_synonyms_raises(self) -> None:
        with pytest.raises(ValueError, match="synonyms mora imati"):
            Concept(field="x", language="bs", synonyms=())

    def test_empty_string_synonym_raises(self) -> None:
        with pytest.raises(TypeError, match="neprazni stringovi"):
            Concept(field="x", language="bs", synonyms=("y", ""))

    def test_frozen(self) -> None:
        c = Concept(field="x", language="bs", synonyms=("y",))
        with pytest.raises(FrozenInstanceError):
            c.field = "z"  # type: ignore[misc]


class TestConceptMatchesText:
    def test_exact_match(self) -> None:
        c = Concept(field="x", language="bs", synonyms=("Broj fakture",))
        assert c.matches_text("Broj fakture")

    def test_case_insensitive(self) -> None:
        c = Concept(field="x", language="bs", synonyms=("Broj fakture",))
        assert c.matches_text("broj fakture")
        assert c.matches_text("BROJ FAKTURE")

    def test_whitespace_stripped(self) -> None:
        c = Concept(field="x", language="bs", synonyms=("Broj fakture",))
        assert c.matches_text("  Broj fakture  ")

    def test_no_match(self) -> None:
        c = Concept(field="x", language="bs", synonyms=("Broj fakture",))
        assert not c.matches_text("Datum")
        assert not c.matches_text("")

    def test_multiple_synonyms(self) -> None:
        c = Concept(
            field="x", language="bs",
            synonyms=("Broj fakture", "Invoice No", "Inv. br."),
        )
        assert c.matches_text("Broj fakture")
        assert c.matches_text("Invoice No")
        assert c.matches_text("Inv. br.")


class TestConceptHasPhrase:
    def test_phrase_in_text(self) -> None:
        c = Concept(
            field="x", language="bs",
            synonyms=("x",),
            context_phrases=("ukupno za plaćanje",),
        )
        assert c.has_phrase("Ovo je ukupno za plaćanje EUR 100.00")
        assert c.has_phrase("ukupno za plaćanje")

    def test_phrase_not_in_text(self) -> None:
        c = Concept(
            field="x", language="bs",
            synonyms=("x",),
            context_phrases=("ukupno za plaćanje",),
        )
        assert not c.has_phrase("neto masa")
        assert not c.has_phrase("")

    def test_empty_concept_phrase(self) -> None:
        c = Concept(field="x", language="bs", synonyms=("y",))
        # Nema context_phrases, has_phrase uvijek False
        assert not c.has_phrase("bilo sta")

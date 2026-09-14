# Tests: domain/concepts/test_concept_library.
"""Testovi za ConceptLibrary (V3_2 C1).

V3 B5 acceptance: 9 invoice polja + 11 item polja = 20 ukupno.
Biblioteka mora pokrivati sva 20 polja u 4 jezika.
"""
from __future__ import annotations

import pytest

from parser_studio.domain.concepts import Concept, ConceptLibrary

# 20 canonical field names (9 invoice + 11 item)
INVOICE_FIELDS = (
    "invoice_number", "invoice_date", "currency",
    "seller_name", "seller_tax_id",
    "buyer_name", "buyer_tax_id",
    "incoterm", "origin_statement",
)
ITEM_FIELDS = (
    "redni_broj", "sifra_proizvoda", "naziv_robe",
    "tarifni_broj", "jedinica_mjere", "kolicina",
    "jedinicna_cijena", "iznos",
    "zemlja_porijekla", "neto_masa", "bruto_masa",
)
ALL_FIELDS = INVOICE_FIELDS + ITEM_FIELDS
assert len(ALL_FIELDS) == 20


class TestConceptLibraryDefaults:
    def test_default_library_covers_all_20_fields(self) -> None:
        library = ConceptLibrary()
        for field in ALL_FIELDS:
            assert field in library.all_fields(), f"Missing field: {field}"
        assert len(library.all_fields()) == 20

    def test_default_library_4_languages(self) -> None:
        assert ConceptLibrary.SUPPORTED_LANGUAGES == ("bs", "hr", "sr", "en")
        library = ConceptLibrary()
        for lang in ConceptLibrary.SUPPORTED_LANGUAGES:
            for field in ALL_FIELDS:
                assert library.get(field, lang) is not None, (
                    f"Missing Concept for field={field}, language={lang}"
                )

    def test_total_concept_count(self) -> None:
        library = ConceptLibrary()
        # 20 polja × 4 jezika = 80 koncepata
        assert len(library) == 80


class TestConceptLibraryGet:
    def test_get_existing(self) -> None:
        library = ConceptLibrary()
        c = library.get("invoice_number", "bs")
        assert c is not None
        assert c.field == "invoice_number"
        assert c.language == "bs"

    def test_get_nonexistent_field(self) -> None:
        library = ConceptLibrary()
        assert library.get("nonexistent", "bs") is None

    def test_get_nonexistent_language(self) -> None:
        library = ConceptLibrary()
        assert library.get("invoice_number", "de") is None


class TestConceptLibraryMatchAlias:
    def test_match_bosnian_synonym(self) -> None:
        library = ConceptLibrary()
        result = library.match_alias("Broj fakture")
        assert result == ("invoice_number", "bs")

    def test_match_english_synonym(self) -> None:
        library = ConceptLibrary()
        result = library.match_alias("Invoice No")
        assert result == ("invoice_number", "en")

    def test_match_case_insensitive(self) -> None:
        library = ConceptLibrary()
        assert library.match_alias("broj fakture") == ("invoice_number", "bs")
        assert library.match_alias("INVOICE NO") == ("invoice_number", "en")

    def test_match_with_whitespace(self) -> None:
        library = ConceptLibrary()
        assert library.match_alias("  Broj fakture  ") == ("invoice_number", "bs")

    def test_no_match(self) -> None:
        library = ConceptLibrary()
        assert library.match_alias("neki random tekst") is None
        assert library.match_alias("") is None


class TestConceptLibraryAllFields:
    def test_all_fields_sorted(self) -> None:
        library = ConceptLibrary()
        fields = library.all_fields()
        assert fields == tuple(sorted(fields))
        assert len(fields) == 20


class TestConceptLibraryLanguagesFor:
    def test_languages_for_invoice_number(self) -> None:
        library = ConceptLibrary()
        langs = library.languages_for("invoice_number")
        assert set(langs) == {"bs", "hr", "sr", "en"}

    def test_languages_for_unknown(self) -> None:
        library = ConceptLibrary()
        assert library.languages_for("unknown") == ()


class TestConceptLibraryCustom:
    def test_custom_concepts(self) -> None:
        custom = (
            Concept(field="my_field", language="en", synonyms=("My Field",)),
        )
        library = ConceptLibrary(custom)
        assert library.get("my_field", "en") is not None
        assert library.all_fields() == ("my_field",)

    def test_duplicate_field_language_raises(self) -> None:
        c1 = Concept(field="x", language="bs", synonyms=("a",))
        c2 = Concept(field="x", language="bs", synonyms=("b",))
        with pytest.raises(ValueError, match="Duplicate"):
            ConceptLibrary((c1, c2))


class TestConceptLibrarySynonymCoverage:
    """Coverage test: svako polje ima 3-10 sinonima."""

    def test_invoice_fields_have_3_to_10_synonyms(self) -> None:
        library = ConceptLibrary()
        for field in INVOICE_FIELDS:
            for lang in ("bs", "hr", "sr", "en"):
                concept = library.get(field, lang)
                assert concept is not None
                n_syn = len(concept.synonyms)
                assert 3 <= n_syn <= 10, (
                    f"Field={field}, lang={lang}: {n_syn} synonyms (expected 3-10)"
                )

    def test_item_fields_have_3_to_10_synonyms(self) -> None:
        library = ConceptLibrary()
        for field in ITEM_FIELDS:
            for lang in ("bs", "hr", "sr", "en"):
                concept = library.get(field, lang)
                assert concept is not None
                n_syn = len(concept.synonyms)
                assert 3 <= n_syn <= 10, (
                    f"Field={field}, lang={lang}: {n_syn} synonyms (expected 3-10)"
                )

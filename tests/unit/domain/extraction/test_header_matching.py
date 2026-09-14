# Tests: extraction/header_matching.
from __future__ import annotations

import pytest

from parser_studio.domain.extraction.header_matching import (
    identify_columns,
    is_footer_text,
    match_score,
    normalize_header,
)


class TestNormalizeHeader:
    def test_empty_string(self) -> None:
        assert normalize_header("") == ""

    def test_none_input(self) -> None:
        assert normalize_header(None) == ""

    def test_lowercase(self) -> None:
        assert normalize_header("Kolicina") == "kolicina"

    def test_nfkc_compatibility(self) -> None:
        # NFKC kompatibilne forme (npr. rimski brojevi, ligature)
        assert normalize_header("Količina") == "kolicina"  # č -> c

    def test_d_stripped(self) -> None:
        # đ nema NFD dekompoziciju; mora rucno
        assert normalize_header("Đačka") == "dacka"

    def test_dots_stripped(self) -> None:
        assert normalize_header("U.M.") == "um"
        assert normalize_header("Kol.") == "kol"

    def test_whitespace_collapsed(self) -> None:
        assert normalize_header("Kolicina   robe") == "kolicina robe"
        assert normalize_header("  Kolicina  ") == "kolicina"

    def test_preserves_words(self) -> None:
        assert normalize_header("Tariff Number") == "tariff number"


class TestMatchScore:
    def test_exact_match(self) -> None:
        assert match_score("kolicina", "kolicina") == 1.0

    def test_no_match(self) -> None:
        assert match_score("kolicina", "cijena") == 0.0

    def test_case_insensitive(self) -> None:
        assert match_score("Kolicina", "kolicina") == 1.0
        assert match_score("KOLICINA", "kolicina") == 1.0

    def test_starts_with_long_alias(self) -> None:
        assert match_score("tariff number", "tariff") == 1.0

    def test_substring_match(self) -> None:
        # Substring "tarifni" in "tarifni broj" (cijeli substring)
        assert match_score("tarifni broj", "tarifni") == 1.0

    def test_short_alias_word_match(self) -> None:
        # Kratki alias "kol" smije pogoditi samo kao zasebna rijec
        assert match_score("neto kol robe", "kol") == 1.0
        assert match_score("kol robe", "kol") == 1.0

    def test_short_alias_no_word_match(self) -> None:
        # "kol" u "kolona" NIJE match (kratki alias)
        assert match_score("kolona", "kol") == 0.0

    def test_dots_in_header(self) -> None:
        assert match_score("U.M.", "um") == 1.0

    def test_empty_inputs(self) -> None:
        assert match_score("", "kolicina") == 0.0
        assert match_score("kolicina", "") == 0.0


class TestIdentifyColumns:
    def test_basic(self) -> None:
        headers = ["Pos.", "Description", "Quantity", "Unit Price", "Amount"]
        mapping = identify_columns(headers)
        assert "naziv_robe" in mapping
        assert "kolicina" in mapping
        assert "cijena_jed" in mapping
        assert "iznos" in mapping

    def test_bosnian_headers(self) -> None:
        headers = ["Naziv", "Kolicina", "Cijena", "Iznos"]
        mapping = identify_columns(headers)
        assert mapping.get("naziv_robe") == 0
        assert mapping.get("kolicina") == 1
        assert mapping.get("cijena_jed") == 2
        assert mapping.get("iznos") == 3

    def test_short_alias_disambiguation(self) -> None:
        headers = ["Opis", "Kolona", "Kolicina"]
        # "kol" u "kolona" ne smije pogoditi, ali "kolicina" treba
        mapping = identify_columns(headers)
        assert mapping.get("naziv_robe") == 0
        assert "kolicina" in mapping
        # "kolona" NE SMIJE biti mapiran kao "kolicina" (jer "kol" je samo prefix)
        assert mapping.get("kolicina") == 2

    def test_unique_mapping(self) -> None:
        # Svaka kolona najvise jedan field
        headers = ["Description", "Item Description", "Product Description"]
        mapping = identify_columns(headers)
        # Svi opisi su isti field, ali samo jedna kolona treba biti mapirana
        assert mapping.get("naziv_robe") is not None
        # Ostali ne smiju biti mapirani
        assert len([k for k in mapping if mapping[k] == 0]) == 1

    def test_empty_headers(self) -> None:
        mapping = identify_columns(["", "", ""])
        assert mapping == {}

    def test_no_match(self) -> None:
        mapping = identify_columns(["Random Column 1", "Another Column"])
        assert mapping == {}

    def test_custom_aliases(self) -> None:
        headers = ["Custom Field"]
        custom_aliases = {"my_field": ["custom field"]}
        mapping = identify_columns(headers, custom_aliases)
        assert mapping.get("my_field") == 0


class TestIsFooterText:
    def test_footer_ukupno(self) -> None:
        assert is_footer_text("UKUPNO: 100") is True

    def test_footer_total(self) -> None:
        assert is_footer_text("TOTAL: 500") is True

    def test_footer_pdv(self) -> None:
        assert is_footer_text("PDV: 19%") is True

    def test_not_footer_totalizator(self) -> None:
        # "totalizator" pocinje sa "total" ali je stvarna roba
        assert is_footer_text("TOTALIZATOR ZA KOSILICU") is False

    def test_empty_text(self) -> None:
        assert is_footer_text("") is False

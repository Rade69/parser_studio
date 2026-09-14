# Tests: invoice/fields.
from __future__ import annotations

import pytest

from parser_studio.domain.invoice.fields import COLUMN_ALIASES


class TestColumnAliasesStructure:
    def test_all_aliases_non_empty_list(self) -> None:
        for canonical, aliases in COLUMN_ALIASES.items():
            assert isinstance(aliases, list)
            assert len(aliases) > 0, f"{canonical} ima praznu listu aliasa"

    def test_all_aliases_non_empty_strings(self) -> None:
        for canonical, aliases in COLUMN_ALIASES.items():
            for alias in aliases:
                assert isinstance(alias, str)
                assert alias.strip() != "", f"{canonical} ima prazan alias"

    def test_has_essential_fields(self) -> None:
        assert "naziv_robe" in COLUMN_ALIASES
        assert "product_code" in COLUMN_ALIASES
        assert "kolicina" in COLUMN_ALIASES
        assert "cijena_jed" in COLUMN_ALIASES
        assert "iznos" in COLUMN_ALIASES
        assert "tarifni_broj" in COLUMN_ALIASES

    def test_has_invoice_metadata_fields(self) -> None:
        assert "invoice_number" in COLUMN_ALIASES
        assert "valuta" in COLUMN_ALIASES
        assert "zemlja_porijekla" in COLUMN_ALIASES
        assert "povlastica" in COLUMN_ALIASES

    def test_has_weight_fields(self) -> None:
        assert "bruto_kg" in COLUMN_ALIASES
        assert "neto_kg" in COLUMN_ALIASES

    def test_has_unit_field(self) -> None:
        assert "jm" in COLUMN_ALIASES

    def test_minimum_30_aliases(self) -> None:
        total = sum(len(aliases) for aliases in COLUMN_ALIASES.values())
        assert total >= 30, f"COLUMN_ALIASES ima {total} aliasa, očekivano >= 30"


class TestColumnAliasesCoverage:
    def test_bosnian_aliases_present(self) -> None:
        assert "kolicina" in COLUMN_ALIASES["kolicina"]
        assert "naziv" in COLUMN_ALIASES["naziv_robe"]
        assert "cijena" in COLUMN_ALIASES["cijena_jed"]
        assert "iznos" in COLUMN_ALIASES["iznos"]

    def test_english_aliases_present(self) -> None:
        assert "quantity" in COLUMN_ALIASES["kolicina"]
        assert "description" in COLUMN_ALIASES["naziv_robe"]
        assert "price" in COLUMN_ALIASES["cijena_jed"]
        assert "amount" in COLUMN_ALIASES["iznos"]

    def test_croatian_aliases_present(self) -> None:
        assert "opis" in COLUMN_ALIASES["naziv_robe"]
        assert "tarifni broj" in COLUMN_ALIASES["tarifni_broj"]

    def test_short_aliases_present(self) -> None:
        # Kratki aliasi (≤3 znaka) zahtijevaju posebnu logiku
        assert "kol" in COLUMN_ALIASES["kolicina"]
        assert "jm" in COLUMN_ALIASES["jm"]
        assert "um" in COLUMN_ALIASES["jm"]
        assert "hs" in COLUMN_ALIASES["tarifni_broj"]
        assert "cn" in COLUMN_ALIASES["tarifni_broj"]

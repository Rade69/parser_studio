"""
Testovi vendorovanog ugovora.

Najvažniji je `test_drift_protiv_zivog_deklarant_pro` — on je jedina odbrana od
tihe greške: ako deklarant_pro doda polje na InvoiceLine, alat bi i dalje
generisao parsere koji to polje ne popunjavaju, a verifikacija nivoa 8
(preview == generisano) bi PROŠLA jer obje strane koriste istu zastarjelu kopiju.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from contract.draft_types import InvoiceLine, Party
from contract.import_result import ImportResult


def _deklarant_pro_root() -> Path | None:
    """Putanja do živog deklarant_pro, ako je dostupna na ovoj mašini."""
    env = os.getenv("DEKLARANT_PRO_ROOT")
    if env:
        p = Path(env)
        return p if p.is_dir() else None
    default = Path.home() / "Desktop" / "deklarant_pro"
    return default if default.is_dir() else None


class TestUgovorOsnovno:
    def test_invoice_line_ima_srpske_nazive_polja(self):
        """Projektno pravilo deklarant_pro (AGENTS.md): srpski nazivi su namjerni."""
        line = InvoiceLine()
        for field_name in (
            "naziv_robe", "tarifni_broj", "zemlja_porijekla", "povlastica",
            "bruto_kg", "neto_kg", "kolicina", "cijena_jed", "iznos", "jm",
        ):
            assert hasattr(line, field_name), f"nedostaje polje {field_name}"

    def test_from_any_prihvata_engleske_aliase(self):
        line = InvoiceLine.from_any({
            "description": "Grejac spirala",
            "hs": "85168020",
            "origin": "IT",
            "qty": "5",
            "price": "10,50",
        })
        assert line.naziv_robe == "Grejac spirala"
        assert line.tarifni_broj == "85168020"
        assert line.zemlja_porijekla == "IT"
        assert line.kolicina == 5.0
        assert line.cijena_jed == 10.5

    def test_from_any_cuva_original_u_raw(self):
        src = {"description": "X", "nepoznato_polje": "vrijednost"}
        line = InvoiceLine.from_any(src)
        assert line.raw["nepoznato_polje"] == "vrijednost"

    def test_key_grupise_po_tri_polja(self):
        line = InvoiceLine(tarifni_broj="85168020", zemlja_porijekla="IT", povlastica="EUP")
        assert line.key() == ("85168020", "IT", "EUP")

    def test_party_from_any_prihvata_srpske_i_engleske_kljuceve(self):
        p = Party.from_any({"naziv": "ACME DOO", "JIB": "123456789"})
        assert p.name == "ACME DOO"
        assert p.vat_or_id == "123456789"


class TestImportResultValidate:
    def test_prazan_rezultat_je_greska(self):
        ok, errors, _ = ImportResult().validate()
        assert ok is False
        assert any("0 stavki" in e for e in errors)

    def test_prazan_rezultat_ok_kad_je_allow_empty(self):
        ok, errors, _ = ImportResult().validate(allow_empty=True)
        assert ok is True
        assert errors == []

    def test_neto_veci_od_bruto_je_greska(self):
        r = ImportResult(items=[InvoiceLine(naziv_robe="X", kolicina=1)],
                         bruto_kg=10.0, neto_kg=15.0)
        ok, errors, _ = r.validate()
        assert ok is False
        assert any("fizički nemoguće" in e for e in errors)

    def test_negativna_tezina_je_greska(self):
        ok, errors, _ = ImportResult(items=[InvoiceLine(naziv_robe="X", kolicina=1)],
                                     bruto_kg=-1.0).validate()
        assert ok is False
        assert any("Negativna bruto" in e for e in errors)

    def test_nepoznata_valuta_je_samo_upozorenje(self):
        r = ImportResult(items=[InvoiceLine(naziv_robe="X", kolicina=1)], currency="XYZ")
        ok, _, warnings = r.validate()
        assert ok is True
        assert any("Nepoznata valuta" in w for w in warnings)

    def test_warnings_se_ne_dupliraju_pri_ponovnom_validate(self):
        r = ImportResult(items=[InvoiceLine(naziv_robe="", kolicina=1)])
        r.validate()
        prvi_broj = len(r.warnings)
        r.validate()
        assert len(r.warnings) == prvi_broj

    def test_len_i_indeksiranje(self):
        a, b = InvoiceLine(naziv_robe="A"), InvoiceLine(naziv_robe="B")
        r = ImportResult(items=[a, b])
        assert len(r) == 2
        assert r[0] is a
        assert r[1:] == [b]

    def test_prazan_result_je_falsy_zamka(self):
        """Poznata zamka deklarant_pro: prazan ImportResult je falsy zbog __len__.
        Kod MORA koristiti `result is not None`, ne `if result`."""
        assert not ImportResult()
        assert ImportResult() is not None


class TestDrift:
    def test_drift_protiv_zivog_deklarant_pro(self):
        root = _deklarant_pro_root()
        if root is None:
            pytest.skip("deklarant_pro nije dostupan na ovoj masini (postavi DEKLARANT_PRO_ROOT)")

        from contract.drift_check import check

        ok, messages = check(root)
        assert ok, "Vendorovani ugovor je odstupio:\n" + "\n".join(messages)

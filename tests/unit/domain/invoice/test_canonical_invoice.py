# Tests: domain/invoice/canonical_invoice.
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from parser_studio.domain.evidence import Evidence, Locator
from parser_studio.domain.invoice import (
    CanonicalInvoice,
    InvoiceField,
    InvoiceLine,
    InvoiceStatus,
    canonical_field_count,
    canonical_invoice_field_names,
    canonical_item_field_names,
    known_currencies,
)
from parser_studio.domain.invoice.canonical_invoice import (
    _date_field,
    _decimal_field,
    _str_field,
)

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _locator() -> Locator:
    return Locator(source_path="inv.xlsx", kind="excel", sheet="S1", row=2, col=3)


def _evidence() -> Evidence:
    return Evidence(
        raw_value="INV-001",
        raw_text="INV-001",
        locator=_locator(),
        element_type="excel_cell",
        source_id="src-1",
    )


def _found(value: object) -> InvoiceField:
    return InvoiceField(value=value, status=InvoiceStatus.FOUND, provenance=_evidence())


def _not_present() -> InvoiceField:
    return InvoiceField(value=None, status=InvoiceStatus.NOT_PRESENT)


def _failed() -> InvoiceField:
    return InvoiceField(value=None, status=InvoiceStatus.FAILED)


def _make_line(line_no: int = 1) -> InvoiceLine:
    return InvoiceLine(
        line_no=line_no,
        product_code=_found("ART-001"),
        naziv_robe=_found("Proizvod A"),
        tarifni_broj=_found("1234.56.78"),
        jm=_found("kom"),
        kolicina=_found(Decimal(10)),
        cijena_jed=_found(Decimal("5.50")),
        iznos=_found(Decimal("55.00")),
        zemlja_porijekla=_found("BA"),
        neto_kg=_found(Decimal("1.5")),
        bruto_kg=_found(Decimal("1.7")),
    )


def _make_invoice(items: tuple[InvoiceLine, ...] = ()) -> CanonicalInvoice:
    return CanonicalInvoice(
        invoice_number=_found("INV-001"),
        invoice_date=_found(date(2026, 1, 15)),
        currency=_found("EUR"),
        exporter=_found("ACME d.o.o."),
        importer=_found("Buyer Co"),
        incoterm_code=_found("DAP"),
        total_bruto_kg=_found(Decimal("100.5")),
        total_neto_kg=_found(Decimal("90.0")),
        origin_statement=_found("EUR.1"),
        items=items,
    )


# --------------------------------------------------------------------------- #
# InvoiceStatus
# --------------------------------------------------------------------------- #


class TestInvoiceStatus:
    def test_has_four_values(self) -> None:
        values = {s.value for s in InvoiceStatus}
        assert values == {"FOUND", "NOT_PRESENT", "AMBIGUOUS", "FAILED"}

    def test_is_str_enum(self) -> None:
        for s in InvoiceStatus:
            assert isinstance(s, str)
            assert isinstance(s, InvoiceStatus)

    def test_lookup_by_value(self) -> None:
        assert InvoiceStatus("FOUND") is InvoiceStatus.FOUND
        assert InvoiceStatus("NOT_PRESENT") is InvoiceStatus.NOT_PRESENT


# --------------------------------------------------------------------------- #
# InvoiceField
# --------------------------------------------------------------------------- #


class TestInvoiceFieldConstruction:
    def test_minimal_no_provenance(self) -> None:
        f = InvoiceField(value="x", status=InvoiceStatus.FOUND)
        assert f.value == "x"
        assert f.status is InvoiceStatus.FOUND
        assert f.provenance is None

    def test_with_provenance(self) -> None:
        ev = _evidence()
        f = InvoiceField(value="x", status=InvoiceStatus.FOUND, provenance=ev)
        assert f.provenance is ev

    def test_not_present_with_none_value(self) -> None:
        f = InvoiceField(value=None, status=InvoiceStatus.NOT_PRESENT)
        assert f.value is None
        assert f.status is InvoiceStatus.NOT_PRESENT

    def test_decimal_value(self) -> None:
        f = InvoiceField(value=Decimal("10.50"), status=InvoiceStatus.FOUND)
        assert f.value == Decimal("10.50")

    def test_date_value(self) -> None:
        d = date(2026, 5, 1)
        f = InvoiceField(value=d, status=InvoiceStatus.FOUND)
        assert f.value == d


class TestInvoiceFieldValidation:
    def test_invalid_status_type_raises(self) -> None:
        with pytest.raises(TypeError, match="status mora biti"):
            InvoiceField(value="x", status="FOUND")  # type: ignore[arg-type]

    def test_invalid_provenance_type_raises(self) -> None:
        with pytest.raises(TypeError, match="provenance mora biti"):
            InvoiceField(
                value="x",
                status=InvoiceStatus.FOUND,
                provenance={"not": "evidence"},  # type: ignore[arg-type]
            )


class TestInvoiceFieldFrozen:
    def test_mutation_raises(self) -> None:
        f = InvoiceField(value="x", status=InvoiceStatus.FOUND)
        with pytest.raises((AttributeError, Exception)):
            f.value = "y"  # type: ignore[misc]

    def test_no_dict(self) -> None:
        f = InvoiceField(value="x", status=InvoiceStatus.FOUND)
        assert not hasattr(f, "__dict__")


# --------------------------------------------------------------------------- #
# InvoiceLine
# --------------------------------------------------------------------------- #


class TestInvoiceLineConstruction:
    def test_minimal_line(self) -> None:
        line = _make_line(line_no=1)
        assert line.line_no == 1
        assert line.naziv_robe.value == "Proizvod A"
        assert line.cijena_jed.value == Decimal("5.50")

    def test_zero_line_no_allowed(self) -> None:
        line = _make_line(line_no=0)
        assert line.line_no == 0


class TestInvoiceLineValidation:
    def test_negative_line_no_raises(self) -> None:
        with pytest.raises(ValueError, match="line_no"):
            _make_line(line_no=-1)

    def test_non_int_line_no_raises(self) -> None:
        with pytest.raises(TypeError, match="line_no"):
            InvoiceLine(
                line_no="1",  # type: ignore[arg-type]
                product_code=_not_present(),
                naziv_robe=_not_present(),
                tarifni_broj=_not_present(),
                jm=_not_present(),
                kolicina=_not_present(),
                cijena_jed=_not_present(),
                iznos=_not_present(),
                zemlja_porijekla=_not_present(),
                neto_kg=_not_present(),
                bruto_kg=_not_present(),
            )

    def test_non_invoice_field_raises(self) -> None:
        with pytest.raises(TypeError, match="naziv_robe"):
            InvoiceLine(
                line_no=1,
                product_code=_not_present(),
                naziv_robe="not a field",  # type: ignore[arg-type]
                tarifni_broj=_not_present(),
                jm=_not_present(),
                kolicina=_not_present(),
                cijena_jed=_not_present(),
                iznos=_not_present(),
                zemlja_porijekla=_not_present(),
                neto_kg=_not_present(),
                bruto_kg=_not_present(),
            )


class TestInvoiceLineFrozen:
    def test_mutation_raises(self) -> None:
        line = _make_line()
        with pytest.raises((AttributeError, Exception)):
            line.line_no = 999  # type: ignore[misc]


# --------------------------------------------------------------------------- #
# CanonicalInvoice
# --------------------------------------------------------------------------- #


class TestCanonicalInvoiceConstruction:
    def test_empty_invoice(self) -> None:
        inv = CanonicalInvoice(
            invoice_number=_not_present(),
            invoice_date=_not_present(),
            currency=_not_present(),
            exporter=_not_present(),
            importer=_not_present(),
            incoterm_code=_not_present(),
            total_bruto_kg=_not_present(),
            total_neto_kg=_not_present(),
            origin_statement=_not_present(),
        )
        assert inv.items == ()
        assert inv.source_path is None
        assert inv.document_id is None

    def test_full_invoice(self) -> None:
        line = _make_line(line_no=1)
        inv = _make_invoice(items=(line,))
        assert inv.invoice_number.value == "INV-001"
        assert inv.invoice_date.value == date(2026, 1, 15)
        assert inv.currency.value == "EUR"
        assert inv.exporter.value == "ACME d.o.o."
        assert inv.importer.value == "Buyer Co"
        assert inv.incoterm_code.value == "DAP"
        assert inv.total_bruto_kg.value == Decimal("100.5")
        assert inv.total_neto_kg.value == Decimal("90.0")
        assert inv.origin_statement.value == "EUR.1"
        assert len(inv.items) == 1

    def test_with_metadata(self) -> None:
        inv = _make_invoice()
        inv2 = CanonicalInvoice(
            invoice_number=inv.invoice_number,
            invoice_date=inv.invoice_date,
            currency=inv.currency,
            exporter=inv.exporter,
            importer=inv.importer,
            incoterm_code=inv.incoterm_code,
            total_bruto_kg=inv.total_bruto_kg,
            total_neto_kg=inv.total_neto_kg,
            origin_statement=inv.origin_statement,
            source_path="/tmp/inv.xlsx",
            document_id="doc-001",
        )
        assert inv2.source_path == "/tmp/inv.xlsx"
        assert inv2.document_id == "doc-001"


class TestCanonicalInvoiceValidation:
    def test_non_invoice_field_raises(self) -> None:
        with pytest.raises(TypeError, match="invoice_number"):
            CanonicalInvoice(
                invoice_number="INV-001",  # type: ignore[arg-type]
                invoice_date=_not_present(),
                currency=_not_present(),
                exporter=_not_present(),
                importer=_not_present(),
                incoterm_code=_not_present(),
                total_bruto_kg=_not_present(),
                total_neto_kg=_not_present(),
                origin_statement=_not_present(),
            )

    def test_non_tuple_items_raises(self) -> None:
        inv = _make_invoice()
        with pytest.raises(TypeError, match="items"):
            CanonicalInvoice(
                invoice_number=inv.invoice_number,
                invoice_date=inv.invoice_date,
                currency=inv.currency,
                exporter=inv.exporter,
                importer=inv.importer,
                incoterm_code=inv.incoterm_code,
                total_bruto_kg=inv.total_bruto_kg,
                total_neto_kg=inv.total_neto_kg,
                origin_statement=inv.origin_statement,
                items=[_make_line()],  # type: ignore[arg-type]
            )

    def test_non_invoice_line_in_items_raises(self) -> None:
        inv = _make_invoice()
        with pytest.raises(TypeError, match="items"):
            CanonicalInvoice(
                invoice_number=inv.invoice_number,
                invoice_date=inv.invoice_date,
                currency=inv.currency,
                exporter=inv.exporter,
                importer=inv.importer,
                incoterm_code=inv.incoterm_code,
                total_bruto_kg=inv.total_bruto_kg,
                total_neto_kg=inv.total_neto_kg,
                origin_statement=inv.origin_statement,
                items=("not a line",),  # type: ignore[arg-type]
            )


class TestCanonicalInvoiceFrozen:
    def test_mutation_raises(self) -> None:
        inv = _make_invoice()
        with pytest.raises((AttributeError, Exception)):
            inv.source_path = "/x"  # type: ignore[misc]


# --------------------------------------------------------------------------- #
# Vendor agnostic test (V3 B1 acceptance)
# --------------------------------------------------------------------------- #


class TestVendorAgnostic:
    def test_no_vendor_names_in_class_names(self) -> None:
        """B1 acceptance: CanonicalInvoice ne smije imati vendor-specific imena."""
        assert CanonicalInvoice.__name__ == "CanonicalInvoice"
        assert InvoiceLine.__name__ == "InvoiceLine"
        assert InvoiceField.__name__ == "InvoiceField"
        assert InvoiceStatus.__name__ == "InvoiceStatus"

    def test_canonical_field_count_is_20(self) -> None:
        assert canonical_field_count() == 20

    def test_invoice_field_names_count(self) -> None:
        assert len(canonical_invoice_field_names()) == 9

    def test_item_field_names_count(self) -> None:
        assert len(canonical_item_field_names()) == 11

    def test_invoice_field_names_content(self) -> None:
        names = canonical_invoice_field_names()
        assert "invoice_number" in names
        assert "invoice_date" in names
        assert "currency" in names
        assert "exporter" in names
        assert "importer" in names
        assert "incoterm_code" in names
        assert "total_bruto_kg" in names
        assert "total_neto_kg" in names
        assert "origin_statement" in names

    def test_item_field_names_content(self) -> None:
        names = canonical_item_field_names()
        assert "line_no" in names
        assert "product_code" in names
        assert "naziv_robe" in names
        assert "tarifni_broj" in names
        assert "jm" in names
        assert "kolicina" in names
        assert "cijena_jed" in names
        assert "iznos" in names
        assert "zemlja_porijekla" in names
        assert "neto_kg" in names
        assert "bruto_kg" in names


# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #


class TestStrFieldHelper:
    def test_with_string(self) -> None:
        f = _str_field("EUR", InvoiceStatus.FOUND)
        assert isinstance(f, InvoiceField)
        assert f.value == "EUR"

    def test_with_none(self) -> None:
        f = _str_field(None, InvoiceStatus.NOT_PRESENT)
        assert f.value is None

    def test_with_non_string_raises(self) -> None:
        with pytest.raises(TypeError):
            _str_field(123, InvoiceStatus.FOUND)  # type: ignore[arg-type]


class TestDecimalFieldHelper:
    def test_with_decimal(self) -> None:
        f = _decimal_field(Decimal("10.5"), InvoiceStatus.FOUND)
        assert f.value == Decimal("10.5")

    def test_with_none(self) -> None:
        f = _decimal_field(None, InvoiceStatus.NOT_PRESENT)
        assert f.value is None

    def test_with_non_decimal_raises(self) -> None:
        with pytest.raises(TypeError):
            _decimal_field(10.5, InvoiceStatus.FOUND)  # type: ignore[arg-type]

    def test_with_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="negativna"):
            _decimal_field(Decimal("-1.0"), InvoiceStatus.FOUND)


class TestDateFieldHelper:
    def test_with_date(self) -> None:
        d = date(2026, 5, 1)
        f = _date_field(d, InvoiceStatus.FOUND)
        assert f.value == d

    def test_with_none(self) -> None:
        f = _date_field(None, InvoiceStatus.NOT_PRESENT)
        assert f.value is None

    def test_with_non_date_raises(self) -> None:
        with pytest.raises(TypeError):
            _date_field("2026-05-01", InvoiceStatus.FOUND)  # type: ignore[arg-type]


class TestKnownCurrencies:
    def test_contains_eur(self) -> None:
        assert "EUR" in known_currencies()

    def test_returns_frozenset(self) -> None:
        assert isinstance(known_currencies(), frozenset)
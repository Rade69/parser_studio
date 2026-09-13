"""Sintetički invoice fixtures za regression testove (TEST 17).

NE sadrži poslovne podatke. Koristi generička imena.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class SyntheticRow:
    """Jedan item red u sintetičkoj fakturi."""
    position: int
    description: str
    quantity: float
    unit: str
    unit_price: float
    discount: float = 0.0
    line_amount: float = 0.0  # izračunat
    tariff: str = ""
    origin: str = ""
    net_weight: float | None = None
    gross_weight: float | None = None


@dataclass
class SyntheticInvoice:
    """Kompletna sintetička faktura."""
    name: str
    invoice_no: str
    invoice_date: str
    exporter: str
    importer: str
    currency: str
    incoterm: str = ""
    rows: list[SyntheticRow] = field(default_factory=list)
    total_net_weight: float | None = None
    total_gross_weight: float | None = None


# ─────────────────────────────────────────────────────────
# Fixture 1: Jednostavna tabela
# ─────────────────────────────────────────────────────────
FIXTURE_SIMPLE = SyntheticInvoice(
    name="simple_invoice",
    invoice_no="INV-001",
    invoice_date="2024-01-15",
    exporter="Generic Supplier GmbH",
    importer="Generic Buyer d.o.o.",
    currency="EUR",
    incoterm="EXW",
    rows=[
        SyntheticRow(1, "Widget A", 10, "pcs", 5.50),
        SyntheticRow(2, "Widget B", 20, "pcs", 3.20),
        SyntheticRow(3, "Widget C", 5, "pcs", 12.00),
        SyntheticRow(4, "Widget D", 15, "pcs", 2.75),
        SyntheticRow(5, "Widget E", 8, "pcs", 8.40),
    ],
)

# ─────────────────────────────────────────────────────────
# Fixture 2: Decimalni zarez
# ─────────────────────────────────────────────────────────
FIXTURE_DECIMAL_COMMA = SyntheticInvoice(
    name="decimal_comma_invoice",
    invoice_no="INV-002",
    invoice_date="2024-02-20",
    exporter="Supplier d.o.o.",
    importer="Buyer d.o.o.",
    currency="EUR",
    rows=[
        SyntheticRow(1, "Item Alpha", 100, "kg", 1.20),
        SyntheticRow(2, "Item Beta", 50, "kg", 2.40),
        SyntheticRow(3, "Item Gamma", 25, "pcs", 5.00),
        SyntheticRow(4, "Item Delta", 12, "l", 8.50),
        SyntheticRow(5, "Item Epsilon", 30, "pcs", 0.95),
    ],
)

# ─────────────────────────────────────────────────────────
# Fixture 3: US decimal (tačka)
# ─────────────────────────────────────────────────────────
FIXTURE_US_DECIMAL = SyntheticInvoice(
    name="us_decimal_invoice",
    invoice_no="INV-003",
    invoice_date="2024-03-10",
    exporter="US Supplier Inc.",
    importer="International Buyer",
    currency="USD",
    rows=[
        SyntheticRow(1, "Part One", 5, "pcs", 199.99),
        SyntheticRow(2, "Part Two", 10, "pcs", 49.50),
        SyntheticRow(3, "Part Three", 25, "pcs", 12.75),
        SyntheticRow(4, "Part Four", 100, "pcs", 1.25),
        SyntheticRow(5, "Part Five", 50, "pcs", 5.00),
    ],
)

# ─────────────────────────────────────────────────────────
# Fixture 4: Sa rabatom
# ─────────────────────────────────────────────────────────
FIXTURE_WITH_DISCOUNT = SyntheticInvoice(
    name="discount_invoice",
    invoice_no="INV-004",
    invoice_date="2024-04-05",
    exporter="Discount Supplier Ltd.",
    importer="Volume Buyer S.A.",
    currency="EUR",
    rows=[
        SyntheticRow(1, "Bulk Item A", 100, "pcs", 10.00, discount=10.0),
        SyntheticRow(2, "Bulk Item B", 50, "pcs", 20.00, discount=15.0),
        SyntheticRow(3, "Bulk Item C", 200, "pcs", 5.00, discount=5.0),
        SyntheticRow(4, "Bulk Item D", 25, "pcs", 40.00, discount=20.0),
        SyntheticRow(5, "Bulk Item E", 75, "pcs", 8.00, discount=12.5),
    ],
)

# ─────────────────────────────────────────────────────────
# Fixture 5: Multiline description
# ─────────────────────────────────────────────────────────
FIXTURE_MULTILINE = SyntheticInvoice(
    name="multiline_invoice",
    invoice_no="INV-005",
    invoice_date="2024-05-12",
    exporter="Multiline Goods GmbH",
    importer="Detail Buyer",
    currency="EUR",
    rows=[
        SyntheticRow(1, "Premium Steel\nPipe 50mm\nGrade A", 10, "pcs", 25.50),
        SyntheticRow(2, "Industrial\nBearing Set\nModel X-200", 5, "pcs", 89.00),
        SyntheticRow(3, "Hydraulic\nHose Assembly\nLength 3m", 15, "pcs", 12.75),
        SyntheticRow(4, "Electrical\nMotor 5kW\n3-phase", 2, "pcs", 450.00),
        SyntheticRow(5, "Stainless\nFittings Set\nComplete Kit", 20, "pcs", 18.90),
    ],
)

# ─────────────────────────────────────────────────────────
# Fixture 6: Ponovljeni header (multi-page)
# ─────────────────────────────────────────────────────────
FIXTURE_REPEATED_HEADER = SyntheticInvoice(
    name="repeated_header_invoice",
    invoice_no="INV-006",
    invoice_date="2024-06-20",
    exporter="Large Supplier Co.",
    importer="Multi-page Buyer",
    currency="EUR",
    rows=[
        SyntheticRow(i, f"Long List Item {i}", 10, "pcs", 1.00)
        for i in range(1, 101)  # 100 redova za više stranica
    ],
)

# ─────────────────────────────────────────────────────────
# Fixture 7: Bez tarife
# ─────────────────────────────────────────────────────────
FIXTURE_NO_TARIFF = SyntheticInvoice(
    name="no_tariff_invoice",
    invoice_no="INV-007",
    invoice_date="2024-07-08",
    exporter="Domestic Supplier",
    importer="Local Buyer",
    currency="BAM",
    rows=[
        SyntheticRow(1, "Local Product X", 20, "pcs", 15.00),
        SyntheticRow(2, "Local Product Y", 10, "pcs", 8.50),
        SyntheticRow(3, "Local Product Z", 5, "pcs", 32.00),
        SyntheticRow(4, "Local Product W", 8, "pcs", 12.00),
        SyntheticRow(5, "Local Product V", 12, "pcs", 4.50),
    ],
)

# ─────────────────────────────────────────────────────────
# Fixture 8: Bez origin
# ─────────────────────────────────────────────────────────
FIXTURE_NO_ORIGIN = SyntheticInvoice(
    name="no_origin_invoice",
    invoice_no="INV-008",
    invoice_date="2024-08-01",
    exporter="Anonymous Supplier",
    importer="Generic Importer",
    currency="EUR",
    rows=[
        SyntheticRow(1, "Generic Good A", 100, "pcs", 2.00),
        SyntheticRow(2, "Generic Good B", 50, "pcs", 5.00),
        SyntheticRow(3, "Generic Good C", 25, "pcs", 10.00),
        SyntheticRow(4, "Generic Good D", 10, "pcs", 25.00),
        SyntheticRow(5, "Generic Good E", 5, "pcs", 50.00),
    ],
)

# ─────────────────────────────────────────────────────────
# Fixture 9: Broken cell (OCR simulacija)
# ─────────────────────────────────────────────────────────
FIXTURE_BROKEN_CELL = SyntheticInvoice(
    name="broken_cell_invoice",
    invoice_no="INV-009",
    invoice_date="2024-09-15",
    exporter="Supplier",
    importer="Buyer",
    currency="EUR",
    rows=[
        SyntheticRow(1, "Item A", 10, "pcs", 5.50),
        SyntheticRow(2, "Item B", 20, "pcs", 3.20),
        SyntheticRow(3, "Item C", 5, "pcs", 12.00),
        SyntheticRow(4, "Item D", 15, "pcs", 2.75),
        SyntheticRow(5, "Item E", 8, "pcs", 8.40),
    ],
)
# Note: u realnoj situaciji, jedna od ćelija bi imala OCR grešku (npr. "1880(" umjesto "1880")

# ─────────────────────────────────────────────────────────
# Fixture 10: Merged numeric values (dvije vrijednosti u istoj ćeliji)
# ─────────────────────────────────────────────────────────
FIXTURE_MERGED_NUMERIC = SyntheticInvoice(
    name="merged_numeric_invoice",
    invoice_no="INV-010",
    invoice_date="2024-10-22",
    exporter="Confused Supplier",
    importer="Importer",
    currency="EUR",
    rows=[
        SyntheticRow(1, "Item A", 10, "pcs", 5.50),
        SyntheticRow(2, "Item B", 20, "pcs", 3.20),
        SyntheticRow(3, "Item C", 5, "pcs", 12.00),
        SyntheticRow(4, "Item D", 15, "pcs", 2.75),
        SyntheticRow(5, "Item E", 8, "pcs", 8.40),
    ],
)
# Note: u realnoj situaciji, jedna ćelija bi sadržavala "5 55,00" (5 i 55,00 spojeno)

# ─────────────────────────────────────────────────────────
# Fixture 11: Ambiguous numeric columns (dvije kolone sa sličnim vrijednostima)
# ─────────────────────────────────────────────────────────
FIXTURE_AMBIGUOUS_NUMERIC = SyntheticInvoice(
    name="ambiguous_numeric_invoice",
    invoice_no="INV-011",
    invoice_date="2024-11-10",
    exporter="Supplier",
    importer="Buyer",
    currency="EUR",
    rows=[
        SyntheticRow(1, "Item A", 10, "pcs", 5.50),
        SyntheticRow(2, "Item B", 20, "pcs", 3.20),
        SyntheticRow(3, "Item C", 5, "pcs", 12.00),
        SyntheticRow(4, "Item D", 15, "pcs", 2.75),
        SyntheticRow(5, "Item E", 8, "pcs", 8.40),
    ],
)
# Note: realna situacija bi imala dvije numeričke kolone sa istim rasponom (price=5.50 i rebate=5.50)


ALL_FIXTURES = [
    FIXTURE_SIMPLE,
    FIXTURE_DECIMAL_COMMA,
    FIXTURE_US_DECIMAL,
    FIXTURE_WITH_DISCOUNT,
    FIXTURE_MULTILINE,
    FIXTURE_REPEATED_HEADER,
    FIXTURE_NO_TARIFF,
    FIXTURE_NO_ORIGIN,
    FIXTURE_BROKEN_CELL,
    FIXTURE_MERGED_NUMERIC,
    FIXTURE_AMBIGUOUS_NUMERIC,
]


def compute_amounts(invoice: SyntheticInvoice) -> SyntheticInvoice:
    """Izračunaj line_amount za svaki red (sa discount ako postoji)."""
    for row in invoice.rows:
        if row.discount > 0:
            row.line_amount = round(row.quantity * row.unit_price * (1 - row.discount / 100), 2)
        else:
            row.line_amount = round(row.quantity * row.unit_price, 2)
    return invoice


def all_fixtures_with_amounts():
    return [compute_amounts(SyntheticInvoice(
        name=f.name,
        invoice_no=f.invoice_no,
        invoice_date=f.invoice_date,
        exporter=f.exporter,
        importer=f.importer,
        currency=f.currency,
        incoterm=f.incoterm,
        rows=[SyntheticRow(
            position=r.position,
            description=r.description,
            quantity=r.quantity,
            unit=r.unit,
            unit_price=r.unit_price,
            discount=r.discount,
            tariff=r.tariff,
            origin=r.origin,
            net_weight=r.net_weight,
            gross_weight=r.gross_weight,
        ) for r in f.rows],
        total_net_weight=f.total_net_weight,
        total_gross_weight=f.total_gross_weight,
    )) for f in ALL_FIXTURES]

# Tests: fixtures/gold/generator.
"""Generator za 4 sintetičke fakture (V3 B5 acceptance: 237 itema).

NE sadrzi stvarne poslovne podatke (V3 ARCH-010). Koristi se iskljucivo
za Gold Corpus integration test.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from openpyxl import Workbook

# V3 B5 spec: Faktura-1 (11), Faktura-2 (4), Medicopharm (84), Sumaprom (138)
SYNTHETIC_FACTORIES: dict[str, dict[str, object]] = {
    "faktura-1": {
        "vendor_id": "FACT-A",
        "vendor_name": "FACT-A Synthetic d.o.o.",
        "item_count": 11,
        "currency": "EUR",
        "seller_tax_id": "SYN-0001",
        "buyer_tax_id": "SYN-9001",
    },
    "faktura-2": {
        "vendor_id": "FACT-B",
        "vendor_name": "FACT-B Synthetic d.o.o.",
        "item_count": 4,
        "currency": "EUR",
        "seller_tax_id": "SYN-0002",
        "buyer_tax_id": "SYN-9002",
    },
    "medicopharm": {
        "vendor_id": "MED-1",
        "vendor_name": "MED-1 Synthetic d.o.o.",
        "item_count": 84,
        "currency": "EUR",
        "seller_tax_id": "SYN-0011",
        "buyer_tax_id": "SYN-9011",
    },
    "sumaprom": {
        "vendor_id": "SUM-1",
        "vendor_name": "SUM-1 Synthetic d.o.o.",
        "item_count": 138,
        "currency": "EUR",
        "seller_tax_id": "SYN-0021",
        "buyer_tax_id": "SYN-9021",
    },
}


def expected_item_count() -> int:
    """Ukupan broj itema u svim 4 fakture (V3 B5 acceptance: 237)."""
    return sum(int(f["item_count"]) for f in SYNTHETIC_FACTORIES.values())


def _deterministic_value(seed: str, salt: str) -> str:
    """Deterministička vrijednost iz seed+salt (sha256 prefix).

    Koristi se za generisanje reproducible test podataka.
    """
    h = hashlib.sha256(f"{seed}:{salt}".encode()).hexdigest()
    return h[:12]


def generate_synthetic_factory(
    factory_id: str,
    output_dir: Path,
) -> Path:
    """Generiši jednu sintetičku .xlsx fakturu u output_dir.

    Struktura:
    - Sheet "Header": 9 invoice polja (2 kolone: field, value)
    - Sheet "Items": N redova × 11 item polja

    Output path: output_dir / f"{factory_id}.xlsx"
    """
    if factory_id not in SYNTHETIC_FACTORIES:
        raise ValueError(
            f"Nepoznat factory_id: {factory_id}. "
            f"Dozvoljeni: {list(SYNTHETIC_FACTORIES.keys())}"
        )

    cfg = SYNTHETIC_FACTORIES[factory_id]
    item_count = int(cfg["item_count"])

    wb = Workbook()

    # Sheet 1: Header (9 invoice polja)
    ws_header = wb.active
    ws_header.title = "Header"
    ws_header.append(["field", "value"])

    invoice_number = f"SYN-INV-{factory_id.upper()}-001"
    invoice_date = "2026-09-14"
    currency = str(cfg["currency"])
    seller_name = str(cfg["vendor_name"])
    buyer_name = "Synthetic Buyer d.o.o. (Mavis Test)"
    incoterm = "EXW"
    gross_mass = str(item_count * 10) + " kg"
    net_mass = str(item_count * 9) + " kg"
    origin_statement = f"SYNTHETIC ORIGIN STATEMENT for {factory_id}"

    header_rows = [
        ("invoice_number", invoice_number),
        ("invoice_date", invoice_date),
        ("currency", currency),
        ("seller_name", seller_name),
        ("seller_tax_id", str(cfg["seller_tax_id"])),
        ("buyer_name", buyer_name),
        ("buyer_tax_id", str(cfg["buyer_tax_id"])),
        ("incoterm", incoterm),
        ("origin_statement", origin_statement),
        # Dodatna polja (nije u 9 obaveznih, ali ExcelHeaderProducer ocekuje):
        ("gross_mass", gross_mass),
        ("net_mass", net_mass),
    ]
    for field_name, value in header_rows:
        ws_header.append([field_name, value])

    # Sheet 2: Items (11 kolona × N redova)
    ws_items = wb.create_sheet("Items")
    ws_items.append([
        "redni_broj",         # 1
        "sifra_proizvoda",    # 2
        "naziv_robe",         # 3
        "tarifni_broj",       # 4
        "jedinica_mjere",     # 5
        "kolicina",           # 6
        "jedinicna_cijena",   # 7
        "iznos",              # 8
        "zemlja_porijekla",   # 9
        "neto_masa",          # 10
        "bruto_masa",         # 11
    ])

    for i in range(1, item_count + 1):
        salt = f"item-{i:04d}"
        ws_items.append([
            str(i),                                            # redni_broj
            f"S-{_deterministic_value(factory_id, salt)}",      # sifra_proizvoda
            f"Synthetic Item {i} for {factory_id}",             # naziv_robe
            f"{_deterministic_value(factory_id, salt)[:8]}",   # tarifni_broj
            "PCS",                                              # jedinica_mjere
            str(i * 10),                                        # kolicina
            f"{_deterministic_value(factory_id, salt + 'p')}", # jedinicna_cijena
            str(i * 100),                                       # iznos
            "MK",                                               # zemlja_porijekla
            str(i),                                             # neto_masa
            str(i + 1),                                         # bruto_masa
        ])

    # Save
    output_path = output_dir / f"{factory_id}.xlsx"
    wb.save(output_path)
    wb.close()
    return output_path


def generate_all_synthetic_factories(output_dir: Path) -> dict[str, Path]:
    """Generiši sve 4 sintetičke fakture. Vrati dict {factory_id: path}."""
    paths: dict[str, Path] = {}
    for factory_id in SYNTHETIC_FACTORIES:
        paths[factory_id] = generate_synthetic_factory(factory_id, output_dir)
    return paths

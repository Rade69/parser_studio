# Tests: fixtures/gold.
"""Sintetički faktura generator za Gold Corpus test (V3 ARCH-010 zabrana stvarnih faktura).

NE generira stvarne poslovne podatke. Koristi se SAMO u testovima.
Output ide u tmp_path, NE u Git.
"""
from .generator import (
    SYNTHETIC_FACTORIES,
    expected_item_count,
    generate_all_synthetic_factories,
    generate_synthetic_factory,
)

__all__ = [
    "SYNTHETIC_FACTORIES",
    "expected_item_count",
    "generate_all_synthetic_factories",
    "generate_synthetic_factory",
]

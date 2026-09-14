# Domain: profiles/layout_fingerprint.
# Posjeduje: LayoutFingerprint dataclass + FingerprintComponent.
# Ne zna za: SQLite, PySide6, Docling, openpyxl, contract, adapters.
"""LayoutFingerprint — hash vrijednost layout detection pravila dokumenta.

V3 E1: Implementirati LayoutFingerprint.
Koristi se za:
- Identifikaciju layout detection uzorka dokumenta
- Grupiranje slicnih dokumenata u Profile Builder (V3 E2)
- Drift detection (V3 E4) — novi fingerprint iste firme = nova verzija profila

Algoritam:
1. Prikupi komponente (npr. header_row_count, column_signature, sheet_names)
2. Sortiraj po name (deterministicki)
3. Konkateniraj "name:value|name:value|..."
4. SHA-256 hex digest
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FingerprintComponent:
    """Jedna komponenta fingerprint-a (npr. header_row_count=1)."""

    name: str
    value: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name ne moze biti prazan string")
        if not self.value:
            raise ValueError("value ne moze biti prazan string")


@dataclass(frozen=True, slots=True)
class LayoutFingerprint:
    """Hash vrijednost layout detection pravila. Immutable value object.

    Hash se racuna deterministicki iz components (sortiranih po name).
    Dva fingerprinta sa istim components imaju isti hash.
    """

    hash: str
    components: tuple[FingerprintComponent, ...]

    def __post_init__(self) -> None:
        if not self.hash:
            raise ValueError("hash ne moze biti prazan string")
        if len(self.hash) != 64:
            raise ValueError(
                f"hash mora biti 64-char SHA-256 hex, dobijeno {len(self.hash)} chars"
            )
        if not all(isinstance(c, FingerprintComponent) for c in self.components):
            raise TypeError(
                "components moraju biti FingerprintComponent instances"
            )

    @staticmethod
    def compute(components: tuple[FingerprintComponent, ...]) -> LayoutFingerprint:
        """Izracunaj hash iz components (sortirano po name).

        Primjer:
            components = (
                FingerprintComponent(name="header_row_count", value="1"),
                FingerprintComponent(name="column_count", value="6"),
            )
            fp = LayoutFingerprint.compute(components)
        """
        sorted_components = tuple(sorted(components, key=lambda c: c.name))
        joined = "|".join(f"{c.name}:{c.value}" for c in sorted_components)
        digest = hashlib.sha256(joined.encode("utf-8")).hexdigest()
        return LayoutFingerprint(hash=digest, components=sorted_components)

    def matches(self, other: LayoutFingerprint) -> bool:
        """True ako dva fingerprinta imaju isti hash (isti layout pattern)."""
        return self.hash == other.hash


__all__ = ["FingerprintComponent", "LayoutFingerprint"]

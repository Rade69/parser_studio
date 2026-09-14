# Domain: profiles/layout_profile.
# Posjeduje: LayoutProfile + ProfileRule + RuleParameter.
# Ne zna za: SQLite, PySide6, Docling, openpyxl, contract, adapters.
"""LayoutProfile — izvedeni artefakt iz Gold ground truth (V3 E2 + ARCH-004).

Profil se gradi iz Gold-a, nikad obrnuto. Verzioniran je (int version: 1, 2, 3, ...).
Moze se obrisati i ponovo izgraditi bez gubitka podataka (Gold je source-of-truth).

V3 ARCH-004: "Profil se mora moci obrisati i ponovo izgraditi."
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .layout_fingerprint import LayoutFingerprint


@dataclass(frozen=True, slots=True)
class RuleParameter:
    """Key=value par unutar ProfileRule."""

    key: str
    value: str

    def __post_init__(self) -> None:
        if not self.key:
            raise ValueError("key ne moze biti prazan string")
        if not self.value:
            raise ValueError("value ne moze biti prazan string")


@dataclass(frozen=True, slots=True)
class ProfileRule:
    """Jedno pravilo u profilu (npr. header_row=1, total_pattern=RXX)."""

    rule_type: str  # npr. "header_row", "column_match", "fallback", "normalization"
    parameters: tuple[RuleParameter, ...]

    def __post_init__(self) -> None:
        if not self.rule_type:
            raise ValueError("rule_type ne moze biti prazan string")
        if not all(isinstance(p, RuleParameter) for p in self.parameters):
            raise TypeError("parameters moraju biti RuleParameter instances")


@dataclass(frozen=True, slots=True)
class LayoutProfile:
    """Izvedeni profil jednog vendora. Versiran, deletable, re-buildable.

    Izveden iz Gold ground truth (V3 ARCH-004). NE smije biti source-of-truth.

    Atributi:
        vendor_id: Identifikator vendora (npr. "faktura-1", "medicopharm").
        version: 1-based verzija (bumped on drift, V3 E4).
        fingerprint: Hash layout detection pravila (V3 E1).
        rules: Tuple ProfileRule-ova izvedenih iz Gold primjera.
        source_documents: Putanje do Gold dokumenata koji su generisali profil.
        built_at: Timestamp izgradnje (immutable datetime).
        sample_count: Broj Gold primjera koristenih za izgradnju.
    """

    vendor_id: str
    version: int
    fingerprint: LayoutFingerprint
    rules: tuple[ProfileRule, ...]
    source_documents: tuple[str, ...]
    built_at: datetime
    sample_count: int

    def __post_init__(self) -> None:
        if not self.vendor_id:
            raise ValueError("vendor_id ne moze biti prazan string")
        if self.version < 1:
            raise ValueError(f"version mora biti >= 1, dobijeno {self.version}")
        if not isinstance(self.fingerprint, LayoutFingerprint):
            raise TypeError(
                f"fingerprint mora biti LayoutFingerprint, "
                f"dobijeno {type(self.fingerprint).__name__}"
            )
        if self.sample_count < 1:
            raise ValueError(
                f"sample_count mora biti >= 1, dobijeno {self.sample_count}"
            )

    def next_version(self) -> int:
        """Vrati version+1 (za drift, V3 E4)."""
        return self.version + 1


__all__ = ["LayoutProfile", "ProfileRule", "RuleParameter"]

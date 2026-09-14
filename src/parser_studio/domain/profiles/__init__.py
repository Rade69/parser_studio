# Domain: profiles.
# Posjeduje: LayoutFingerprint, FingerprintComponent, LayoutProfile, ProfileRule, RuleParameter.
# Ne zna za: SQLite, PySide6, Docling, openpyxl, contract.
"""Domain model za Profile Builder (V3 E1+E2).

LayoutProfile je izvedeni artefakt iz Gold ground truth (V3 ARCH-004):
profil se gradi iz Gold-a, nikad obrnuto. Profil je verzioniran i
moze se obrisati i ponovo izgraditi.
"""
from .layout_fingerprint import FingerprintComponent, LayoutFingerprint
from .layout_profile import LayoutProfile, ProfileRule, RuleParameter

__all__ = [
    "FingerprintComponent",
    "LayoutFingerprint",
    "LayoutProfile",
    "ProfileRule",
    "RuleParameter",
]

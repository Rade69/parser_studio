# Tests: domain/profiles/test_layout_fingerprint.
"""Testovi za LayoutFingerprint + FingerprintComponent (V3 E1)."""
from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from parser_studio.domain.profiles import (
    FingerprintComponent,
    LayoutFingerprint,
)


class TestFingerprintComponent:
    def test_construction(self) -> None:
        comp = FingerprintComponent(name="header_row", value="1")
        assert comp.name == "header_row"
        assert comp.value == "1"

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValueError, match="name ne moze biti prazan"):
            FingerprintComponent(name="", value="x")

    def test_empty_value_raises(self) -> None:
        with pytest.raises(ValueError, match="value ne moze biti prazan"):
            FingerprintComponent(name="x", value="")

    def test_frozen(self) -> None:
        comp = FingerprintComponent(name="x", value="y")
        with pytest.raises(FrozenInstanceError):
            comp.name = "z"  # type: ignore[misc]


class TestLayoutFingerprintConstruction:
    def test_minimal_construction(self) -> None:
        # 64-char SHA-256 hex string
        h = "0" * 64
        fp = LayoutFingerprint(hash=h, components=())
        assert fp.hash == h
        assert fp.components == ()

    def test_empty_hash_raises(self) -> None:
        with pytest.raises(ValueError, match="hash ne moze biti prazan"):
            LayoutFingerprint(hash="", components=())

    def test_wrong_length_hash_raises(self) -> None:
        with pytest.raises(ValueError, match="64-char SHA-256 hex"):
            LayoutFingerprint(hash="abc", components=())

    def test_invalid_component_type_raises(self) -> None:
        with pytest.raises(TypeError, match="FingerprintComponent instances"):
            LayoutFingerprint(
                hash="0" * 64,
                components=("not-a-component",),  # type: ignore[arg-type]
            )

    def test_frozen(self) -> None:
        fp = LayoutFingerprint(hash="0" * 64, components=())
        with pytest.raises(FrozenInstanceError):
            fp.hash = "1" * 64  # type: ignore[misc]


class TestLayoutFingerprintCompute:
    def test_compute_empty_components(self) -> None:
        fp = LayoutFingerprint.compute(())
        assert len(fp.hash) == 64
        assert fp.components == ()

    def test_compute_single_component(self) -> None:
        comp = FingerprintComponent(name="header_row", value="1")
        fp = LayoutFingerprint.compute((comp,))
        assert len(fp.hash) == 64
        assert fp.components == (comp,)

    def test_compute_is_deterministic(self) -> None:
        """Isti components uvijek daju isti hash."""
        comps = (
            FingerprintComponent(name="header_row", value="1"),
            FingerprintComponent(name="column_count", value="6"),
        )
        fp1 = LayoutFingerprint.compute(comps)
        fp2 = LayoutFingerprint.compute(comps)
        assert fp1.hash == fp2.hash

    def test_compute_sorts_components_by_name(self) -> None:
        """Komponente se sortiraju po name prije hash-a."""
        a = FingerprintComponent(name="aaa", value="1")
        b = FingerprintComponent(name="bbb", value="2")
        c = FingerprintComponent(name="ccc", value="3")

        fp_forward = LayoutFingerprint.compute((a, b, c))
        fp_reverse = LayoutFingerprint.compute((c, b, a))
        fp_mixed = LayoutFingerprint.compute((b, a, c))

        # Sve tri ordje daju isti hash (jer sortiraju)
        assert fp_forward.hash == fp_reverse.hash == fp_mixed.hash
        # I komponente su sortirane
        assert fp_forward.components == (a, b, c)
        assert fp_reverse.components == (a, b, c)

    def test_different_components_produce_different_hash(self) -> None:
        fp1 = LayoutFingerprint.compute(
            (FingerprintComponent("header_row", "1"),)
        )
        fp2 = LayoutFingerprint.compute(
            (FingerprintComponent("header_row", "2"),)
        )
        assert fp1.hash != fp2.hash

    def test_compute_with_unicode(self) -> None:
        """Unicode vrijednosti se pravilno enkoduju (utf-8)."""
        comp = FingerprintComponent(name="jezik", value="bosanski")
        fp = LayoutFingerprint.compute((comp,))
        assert len(fp.hash) == 64
        assert fp.components == (comp,)


class TestLayoutFingerprintMatches:
    def test_matches_identical_hashes(self) -> None:
        comps = (FingerprintComponent("x", "y"),)
        fp1 = LayoutFingerprint.compute(comps)
        fp2 = LayoutFingerprint.compute(comps)
        assert fp1.matches(fp2)

    def test_does_not_match_different_hashes(self) -> None:
        fp1 = LayoutFingerprint.compute(
            (FingerprintComponent("x", "y"),)
        )
        fp2 = LayoutFingerprint.compute(
            (FingerprintComponent("x", "z"),)
        )
        assert not fp1.matches(fp2)

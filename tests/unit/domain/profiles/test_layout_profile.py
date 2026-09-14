# Tests: domain/profiles/test_layout_profile.
"""Testovi za LayoutProfile + ProfileRule + RuleParameter (V3 E2)."""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from parser_studio.domain.profiles import (
    FingerprintComponent,
    LayoutFingerprint,
    LayoutProfile,
    ProfileRule,
    RuleParameter,
)


def _make_fingerprint() -> LayoutFingerprint:
    return LayoutFingerprint.compute(
        (FingerprintComponent("header_row", "1"),)
    )


def _make_rule(rule_type: str = "test_rule") -> ProfileRule:
    return ProfileRule(
        rule_type=rule_type,
        parameters=(RuleParameter(key="x", value="y"),),
    )


class TestRuleParameter:
    def test_construction(self) -> None:
        p = RuleParameter(key="column", value="6")
        assert p.key == "column"
        assert p.value == "6"

    def test_empty_key_raises(self) -> None:
        with pytest.raises(ValueError, match="key ne moze biti prazan"):
            RuleParameter(key="", value="x")

    def test_empty_value_raises(self) -> None:
        with pytest.raises(ValueError, match="value ne moze biti prazan"):
            RuleParameter(key="x", value="")

    def test_frozen(self) -> None:
        p = RuleParameter(key="x", value="y")
        with pytest.raises(FrozenInstanceError):
            p.key = "z"  # type: ignore[misc]


class TestProfileRule:
    def test_construction(self) -> None:
        rule = _make_rule()
        assert rule.rule_type == "test_rule"
        assert len(rule.parameters) == 1

    def test_empty_rule_type_raises(self) -> None:
        with pytest.raises(ValueError, match="rule_type ne moze biti prazan"):
            ProfileRule(rule_type="", parameters=())

    def test_invalid_parameter_type_raises(self) -> None:
        with pytest.raises(TypeError, match="RuleParameter instances"):
            ProfileRule(
                rule_type="x",
                parameters=("not-a-parameter",),  # type: ignore[arg-type]
            )

    def test_frozen(self) -> None:
        rule = _make_rule()
        with pytest.raises(FrozenInstanceError):
            rule.rule_type = "z"  # type: ignore[misc]


class TestLayoutProfileConstruction:
    def test_minimal_construction(self) -> None:
        now = datetime.now(UTC)
        profile = LayoutProfile(
            vendor_id="faktura-1",
            version=1,
            fingerprint=_make_fingerprint(),
            rules=(),
            source_documents=("/gold/f1.xlsx",),
            built_at=now,
            sample_count=1,
        )
        assert profile.vendor_id == "faktura-1"
        assert profile.version == 1
        assert profile.sample_count == 1
        assert profile.built_at == now

    def test_empty_vendor_id_raises(self) -> None:
        with pytest.raises(ValueError, match="vendor_id ne moze biti prazan"):
            LayoutProfile(
                vendor_id="",
                version=1,
                fingerprint=_make_fingerprint(),
                rules=(),
                source_documents=(),
                built_at=datetime.now(UTC),
                sample_count=1,
            )

    def test_version_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="version mora biti >= 1"):
            LayoutProfile(
                vendor_id="x",
                version=0,
                fingerprint=_make_fingerprint(),
                rules=(),
                source_documents=(),
                built_at=datetime.now(UTC),
                sample_count=1,
            )

    def test_invalid_fingerprint_raises(self) -> None:
        with pytest.raises(TypeError, match="fingerprint mora biti"):
            LayoutProfile(
                vendor_id="x",
                version=1,
                fingerprint="not-a-fingerprint",  # type: ignore[arg-type]
                rules=(),
                source_documents=(),
                built_at=datetime.now(UTC),
                sample_count=1,
            )

    def test_sample_count_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="sample_count mora biti >= 1"):
            LayoutProfile(
                vendor_id="x",
                version=1,
                fingerprint=_make_fingerprint(),
                rules=(),
                source_documents=(),
                built_at=datetime.now(UTC),
                sample_count=0,
            )

    def test_frozen(self) -> None:
        profile = LayoutProfile(
            vendor_id="x",
            version=1,
            fingerprint=_make_fingerprint(),
            rules=(),
            source_documents=(),
            built_at=datetime.now(UTC),
            sample_count=1,
        )
        with pytest.raises(FrozenInstanceError):
            profile.version = 2  # type: ignore[misc]


class TestLayoutProfileNextVersion:
    def test_next_version(self) -> None:
        profile = LayoutProfile(
            vendor_id="x",
            version=3,
            fingerprint=_make_fingerprint(),
            rules=(),
            source_documents=(),
            built_at=datetime.now(UTC),
            sample_count=1,
        )
        assert profile.next_version() == 4

    def test_next_version_from_one(self) -> None:
        profile = LayoutProfile(
            vendor_id="x",
            version=1,
            fingerprint=_make_fingerprint(),
            rules=(),
            source_documents=(),
            built_at=datetime.now(UTC),
            sample_count=1,
        )
        assert profile.next_version() == 2

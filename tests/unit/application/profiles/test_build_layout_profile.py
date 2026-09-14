# Tests: application/profiles/test_build_layout_profile.
"""Testovi za BuildLayoutProfile use case (V3 E2)."""
from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from parser_studio.adapters.profiles import InMemoryProfileRepository
from parser_studio.application.profiles import (
    BuildLayoutProfile,
    BuildRequest,
    BuildResult,
    GoldSample,
)
from parser_studio.domain.profiles import (
    FingerprintComponent,
    LayoutFingerprint,
    RuleParameter,
)


def _make_fp(**components: str) -> LayoutFingerprint:
    """Helper: napravi LayoutFingerprint od keyword argumenata."""
    comps = tuple(
        FingerprintComponent(name=k, value=v) for k, v in components.items()
    )
    return LayoutFingerprint.compute(comps)


def _make_sample(
    source: str = "/gold/f1.xlsx",
    fingerprint: LayoutFingerprint | None = None,
    metadata: tuple[RuleParameter, ...] = (),
) -> GoldSample:
    if fingerprint is None:
        fingerprint = _make_fp(header_row="1")
    return GoldSample(
        source_path=source,
        fingerprint=fingerprint,
        sample_metadata=metadata,
    )


class TestGoldSample:
    def test_construction(self) -> None:
        fp = _make_fp(x="y")
        sample = GoldSample(source_path="/x.xlsx", fingerprint=fp)
        assert sample.source_path == "/x.xlsx"
        assert sample.fingerprint is fp
        assert sample.sample_metadata == ()

    def test_construction_with_metadata(self) -> None:
        sample = GoldSample(
            source_path="/x.xlsx",
            fingerprint=_make_fp(),
            sample_metadata=(RuleParameter("col", "6"),),
        )
        assert len(sample.sample_metadata) == 1

    def test_empty_source_raises(self) -> None:
        with pytest.raises(ValueError, match="source_path ne moze biti prazan"):
            GoldSample(source_path="", fingerprint=_make_fp())

    def test_invalid_fingerprint_raises(self) -> None:
        with pytest.raises(TypeError, match="fingerprint mora biti"):
            GoldSample(
                source_path="/x.xlsx",
                fingerprint="not-fp",  # type: ignore[arg-type]
            )

    def test_frozen(self) -> None:
        sample = _make_sample()
        with pytest.raises(FrozenInstanceError):
            sample.source_path = "/z.xlsx"  # type: ignore[misc]


class TestBuildRequest:
    def test_construction(self) -> None:
        repo = InMemoryProfileRepository()
        sample = _make_sample()
        req = BuildRequest(
            vendor_id="faktura-1",
            gold_samples=(sample,),
            repo=repo,
        )
        assert req.vendor_id == "faktura-1"
        assert req.repo is repo

    def test_empty_vendor_id_raises(self) -> None:
        with pytest.raises(ValueError, match="vendor_id ne moze biti prazan"):
            BuildRequest(
                vendor_id="",
                gold_samples=(_make_sample(),),
                repo=InMemoryProfileRepository(),
            )

    def test_empty_samples_raises(self) -> None:
        with pytest.raises(ValueError, match="gold_samples ne moze biti prazan"):
            BuildRequest(
                vendor_id="x",
                gold_samples=(),
                repo=InMemoryProfileRepository(),
            )

    def test_invalid_repo_raises(self) -> None:
        with pytest.raises(TypeError, match="ProfileRepository Protocol"):
            BuildRequest(
                vendor_id="x",
                gold_samples=(_make_sample(),),
                repo="not-a-repo",  # type: ignore[arg-type]
            )


class TestBuildResult:
    def test_construction_no_warnings(self) -> None:
        # Just ensure BuildResult accepts profile + empty warnings tuple
        from parser_studio.application.profiles.build_layout_profile import (
            BuildLayoutProfile,
        )

        repo = InMemoryProfileRepository()
        uc = BuildLayoutProfile()
        result = uc.execute(
            BuildRequest(vendor_id="x", gold_samples=(_make_sample(),), repo=repo)
        )
        assert isinstance(result, BuildResult)
        assert result.warnings == ()

    def test_frozen(self) -> None:
        from parser_studio.application.profiles.build_layout_profile import (
            BuildLayoutProfile,
        )

        repo = InMemoryProfileRepository()
        uc = BuildLayoutProfile()
        result = uc.execute(
            BuildRequest(vendor_id="x", gold_samples=(_make_sample(),), repo=repo)
        )
        with pytest.raises(FrozenInstanceError):
            result.warnings = ("x",)  # type: ignore[misc]


class TestBuildLayoutProfileHappyPath:
    def test_single_sample_version_one(self) -> None:
        repo = InMemoryProfileRepository()
        uc = BuildLayoutProfile()
        sample = _make_sample(
            metadata=(
                RuleParameter("invoice_count", "10"),
                RuleParameter("column_count", "6"),
            ),
        )
        result = uc.execute(
            BuildRequest(
                vendor_id="faktura-1",
                gold_samples=(sample,),
                repo=repo,
            )
        )

        assert result.profile.vendor_id == "faktura-1"
        assert result.profile.version == 1
        assert result.profile.sample_count == 1
        assert result.warnings == ()
        # Spremljeno u repo
        assert repo.find("faktura-1") is result.profile

    def test_multiple_samples_same_fingerprint_no_warnings(self) -> None:
        repo = InMemoryProfileRepository()
        uc = BuildLayoutProfile()
        fp = _make_fp(header_row="1")
        samples = (
            _make_sample(source="/gold/f1.xlsx", fingerprint=fp),
            _make_sample(source="/gold/f2.xlsx", fingerprint=fp),
            _make_sample(source="/gold/f3.xlsx", fingerprint=fp),
        )
        result = uc.execute(
            BuildRequest(
                vendor_id="faktura-1",
                gold_samples=samples,
                repo=repo,
            )
        )
        assert result.profile.version == 1
        assert result.profile.sample_count == 3
        assert result.warnings == ()
        assert result.profile.source_documents == (
            "/gold/f1.xlsx",
            "/gold/f2.xlsx",
            "/gold/f3.xlsx",
        )

    def test_drift_bumps_version(self) -> None:
        """Ako postoji profil za vendor_id, nova verzija = max+1."""
        repo = InMemoryProfileRepository()
        uc = BuildLayoutProfile()

        # Prvo kreiranje
        sample = _make_sample()
        uc.execute(
            BuildRequest(
                vendor_id="faktura-1",
                gold_samples=(sample,),
                repo=repo,
            )
        )
        # Drugo kreiranje (drift)
        result2 = uc.execute(
            BuildRequest(
                vendor_id="faktura-1",
                gold_samples=(sample,),
                repo=repo,
            )
        )
        assert result2.profile.version == 2
        # Spremljeno
        assert repo.find("faktura-1", version=1) is not None
        assert repo.find("faktura-1", version=2) is result2.profile

    def test_multiple_vendors_independent(self) -> None:
        repo = InMemoryProfileRepository()
        uc = BuildLayoutProfile()
        result1 = uc.execute(
            BuildRequest(
                vendor_id="faktura-1",
                gold_samples=(_make_sample(),),
                repo=repo,
            )
        )
        result2 = uc.execute(
            BuildRequest(
                vendor_id="medicopharm",
                gold_samples=(_make_sample(),),
                repo=repo,
            )
        )
        # Obje imaju version=1 (jer su razliciti vendors)
        assert result1.profile.version == 1
        assert result2.profile.version == 1


class TestBuildLayoutProfileFingerprintDrift:
    def test_fingerprint_mismatch_adds_warning(self) -> None:
        """Ako se fingerprint razlikuje medu samples, dodaj warning."""
        repo = InMemoryProfileRepository()
        uc = BuildLayoutProfile()

        fp1 = _make_fp(header_row="1")
        fp2 = _make_fp(header_row="2")  # razlicit
        samples = (
            _make_sample(source="/gold/f1.xlsx", fingerprint=fp1),
            _make_sample(source="/gold/f2.xlsx", fingerprint=fp2),
        )
        result = uc.execute(
            BuildRequest(
                vendor_id="faktura-1",
                gold_samples=samples,
                repo=repo,
            )
        )
        assert len(result.warnings) == 1
        assert "fingerprint mismatch" in result.warnings[0]
        assert "/gold/f2.xlsx" in result.warnings[0]
        # Profil je i dalje kreiran (sa fp1 fingerprint-om)
        assert result.profile.fingerprint is fp1


class TestBuildLayoutProfileCommonRules:
    def test_common_metadata_extracted(self) -> None:
        """Zajednicki metadata key=value parovi postaju ProfileRule."""
        repo = InMemoryProfileRepository()
        uc = BuildLayoutProfile()

        common_meta = (
            RuleParameter("has_header", "true"),
            RuleParameter("language", "bs"),
        )
        unique_meta_1 = (RuleParameter("invoice_count", "10"),)
        unique_meta_2 = (RuleParameter("invoice_count", "12"),)

        fp = _make_fp(header_row="1")
        samples = (
            _make_sample(
                source="/gold/f1.xlsx",
                fingerprint=fp,
                metadata=common_meta + unique_meta_1,
            ),
            _make_sample(
                source="/gold/f2.xlsx",
                fingerprint=fp,
                metadata=common_meta + unique_meta_2,
            ),
        )
        result = uc.execute(
            BuildRequest(
                vendor_id="faktura-1",
                gold_samples=samples,
                repo=repo,
            )
        )
        # Trebao bi imati jedno ProfileRule sa zajednickim parametrima
        assert len(result.profile.rules) == 1
        rule = result.profile.rules[0]
        assert rule.rule_type == "common_metadata"
        # Samo ZAJEDNICKI parametri (bez invoice_count jer se razlikuje)
        param_keys = [p.key for p in rule.parameters]
        assert "has_header" in param_keys
        assert "language" in param_keys
        assert "invoice_count" not in param_keys

    def test_no_common_metadata_no_rules(self) -> None:
        """Ako nema zajednickih metadata, rules je prazan tuple."""
        repo = InMemoryProfileRepository()
        uc = BuildLayoutProfile()

        fp = _make_fp()
        samples = (
            _make_sample(
                source="/gold/f1.xlsx",
                fingerprint=fp,
                metadata=(RuleParameter("col", "6"),),
            ),
            _make_sample(
                source="/gold/f2.xlsx",
                fingerprint=fp,
                metadata=(RuleParameter("col", "8"),),
            ),
        )
        result = uc.execute(
            BuildRequest(
                vendor_id="faktura-1",
                gold_samples=samples,
                repo=repo,
            )
        )
        assert result.profile.rules == ()

    def test_no_metadata_no_rules(self) -> None:
        """Ako samples nemaju metadata uopste, rules je prazan."""
        repo = InMemoryProfileRepository()
        uc = BuildLayoutProfile()
        result = uc.execute(
            BuildRequest(
                vendor_id="faktura-1",
                gold_samples=(_make_sample(), _make_sample(source="/gold/f2.xlsx")),
                repo=repo,
            )
        )
        assert result.profile.rules == ()


class TestBuildLayoutProfileIntegration:
    def test_profile_persisted_with_correct_metadata(self) -> None:
        """Integration: build + find kroz repo."""
        repo = InMemoryProfileRepository()
        uc = BuildLayoutProfile()

        fp = _make_fp(header_row="1", column_count="6")
        samples = (
            _make_sample(
                source="/gold/faktura1-2026-01.xlsx",
                fingerprint=fp,
                metadata=(
                    RuleParameter("vendor", "faktura-1"),
                    RuleParameter("year", "2026"),
                ),
            ),
            _make_sample(
                source="/gold/faktura1-2026-02.xlsx",
                fingerprint=fp,
                metadata=(
                    RuleParameter("vendor", "faktura-1"),
                    RuleParameter("year", "2026"),
                ),
            ),
        )
        result = uc.execute(
            BuildRequest(
                vendor_id="faktura-1",
                gold_samples=samples,
                repo=repo,
            )
        )

        # Spremljeno i dohvatljivo
        loaded = repo.find("faktura-1")
        assert loaded is result.profile
        assert loaded.vendor_id == "faktura-1"
        assert loaded.version == 1
        assert loaded.sample_count == 2
        assert loaded.source_documents == (
            "/gold/faktura1-2026-01.xlsx",
            "/gold/faktura1-2026-02.xlsx",
        )
        # Common metadata pravilo
        assert len(loaded.rules) == 1
        rule = loaded.rules[0]
        param_dict = {p.key: p.value for p in rule.parameters}
        assert param_dict == {"vendor": "faktura-1", "year": "2026"}

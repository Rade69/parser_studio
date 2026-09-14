# Application: profiles/build_layout_profile.
# Posjeduje: BuildLayoutProfile use case + BuildRequest/BuildResult + GoldSample.
# Zna za: parser_studio.domain.profiles, parser_studio.ports.profile_repository.
# Ne zna za: parser_studio.adapters.* (kroz port), presentation, contract.
"""BuildLayoutProfile use case (V3 E2).

Gold primjeri (source_path + LayoutFingerprint + metadata) -> LayoutProfile.

Workflow:
1. Dohvati existing versions za vendor_id iz repo-a
2. Odredi version: 1 ako nema postojecih, inace max(versions)+1 (drift)
3. Provjeri fingerprint consistency medu gold_samples
4. Ako se fingerprints razlikuju: warning, ali NE fail (drift scenario)
5. Izvedi zajednicka pravila iz metadata svih samples
6. Spremi profil u repo
7. Vrati BuildResult
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from parser_studio.domain.profiles.layout_fingerprint import LayoutFingerprint
from parser_studio.domain.profiles.layout_profile import (
    LayoutProfile,
    ProfileRule,
    RuleParameter,
)
from parser_studio.ports.profile_repository import ProfileRepository


@dataclass(frozen=True, slots=True)
class GoldSample:
    """Jedan gold primjer (source path + extracted LayoutFingerprint + metadata).

    Metadata su RuleParameter key=value parovi koji opisuju uzorak
    (npr. invoice_count=10, has_header_row=True, column_count=6).
    """

    source_path: str
    fingerprint: LayoutFingerprint
    sample_metadata: tuple[RuleParameter, ...] = ()

    def __post_init__(self) -> None:
        if not self.source_path:
            raise ValueError("source_path ne moze biti prazan string")
        if not isinstance(self.fingerprint, LayoutFingerprint):
            raise TypeError(
                f"fingerprint mora biti LayoutFingerprint, "
                f"dobijeno {type(self.fingerprint).__name__}"
            )


@dataclass(frozen=True, slots=True)
class BuildRequest:
    """Request za BuildLayoutProfile use case."""

    vendor_id: str
    gold_samples: tuple[GoldSample, ...]
    repo: ProfileRepository

    def __post_init__(self) -> None:
        if not self.vendor_id:
            raise ValueError("vendor_id ne moze biti prazan string")
        if not self.gold_samples:
            raise ValueError("gold_samples ne moze biti prazan tuple")
        if not isinstance(self.repo, ProfileRepository):
            raise TypeError(
                f"repo mora implementirati ProfileRepository Protocol, "
                f"dobijeno {type(self.repo).__name__}"
            )


@dataclass(frozen=True, slots=True)
class BuildResult:
    """Rezultat BuildLayoutProfile use case-a."""

    profile: LayoutProfile
    warnings: tuple[str, ...]


class BuildLayoutProfile:
    """Use case: gold primjeri -> LayoutProfile.

    Algoritam:
    - version = 1 ako nema postojecih, inace max(versions)+1
    - fingerprint = fingerprint PRVOG gold sample-a (ostali se warning log-uju)
    - rules = derivacija iz sample_metadata (zajednicki key=value parovi)
    - source_documents = tuple source_path svih samples

    Primjer:
        from parser_studio.adapters.profiles import InMemoryProfileRepository
        from parser_studio.domain.profiles import (
            FingerprintComponent, LayoutFingerprint,
        )
        from parser_studio.application.profiles import (
            BuildLayoutProfile, BuildRequest, GoldSample,
        )

        repo = InMemoryProfileRepository()
        fp = LayoutFingerprint.compute((
            FingerprintComponent("header_row", "1"),
        ))
        sample = GoldSample(source_path="/gold/f1.xlsx", fingerprint=fp)
        uc = BuildLayoutProfile()
        result = uc.execute(BuildRequest("faktura-1", (sample,), repo))
    """

    def execute(self, request: BuildRequest) -> BuildResult:
        """Izvedi build iz gold primjera."""
        warnings: list[str] = []

        # 1. Odredi version
        existing_versions = request.repo.list_versions(request.vendor_id)
        if existing_versions:
            new_version = max(existing_versions) + 1
        else:
            new_version = 1

        # 2. Provjeri fingerprint consistency
        first_fingerprint = request.gold_samples[0].fingerprint
        for sample in request.gold_samples[1:]:
            if not sample.fingerprint.matches(first_fingerprint):
                warnings.append(
                    f"fingerprint mismatch: {sample.source_path} "
                    f"({sample.fingerprint.hash[:12]}...) vs "
                    f"first ({first_fingerprint.hash[:12]}...)"
                )

        # 3. Izvedi zajednicka pravila iz metadata
        # Algoritam: samo kljucevi koji imaju ISTU vrijednost u SVIM samples
        common_rules = self._extract_common_rules(request.gold_samples)

        # 4. Kreiraj profil
        source_docs = tuple(s.source_path for s in request.gold_samples)
        profile = LayoutProfile(
            vendor_id=request.vendor_id,
            version=new_version,
            fingerprint=first_fingerprint,
            rules=common_rules,
            source_documents=source_docs,
            built_at=datetime.now(UTC),
            sample_count=len(request.gold_samples),
        )

        # 5. Spremi
        request.repo.save(profile)

        return BuildResult(profile=profile, warnings=tuple(warnings))

    @staticmethod
    def _extract_common_rules(
        samples: tuple[GoldSample, ...],
    ) -> tuple[ProfileRule, ...]:
        """Izvuci zajednicka pravila iz sample_metadata.

        Za svaki key koji se pojavljuje u SVIM samples sa ISTOM vrijednoscu:
        kreiraj RuleParameter(key, value).

        Pravila su grupisana po key u ProfileRule(rule_type='metadata', parameters=(...)).
        """
        if not samples:
            return ()

        # Skup kljuceva iz PRVOG sample-a
        first_keys = {p.key: p.value for p in samples[0].sample_metadata}
        common: dict[str, str] = dict(first_keys)

        # Presjek sa ostalim samples
        for sample in samples[1:]:
            sample_dict = {p.key: p.value for p in sample.sample_metadata}
            for key in list(common.keys()):
                if key not in sample_dict or sample_dict[key] != common[key]:
                    common.pop(key, None)

        if not common:
            return ()

        # Jedno ProfileRule sa svim zajednickim parametrima
        parameters = tuple(
            RuleParameter(key=k, value=v)
            for k, v in sorted(common.items())
        )
        return (ProfileRule(rule_type="common_metadata", parameters=parameters),)


__all__ = ["BuildLayoutProfile", "BuildRequest", "BuildResult", "GoldSample"]

# Tests: ports/test_profile_repository.
"""Testovi za ProfileRepository Protocol (runtime_checkable)."""
from __future__ import annotations

from datetime import UTC, datetime

from parser_studio.adapters.profiles import InMemoryProfileRepository
from parser_studio.domain.profiles import (
    FingerprintComponent,
    LayoutFingerprint,
    LayoutProfile,
)
from parser_studio.ports.profile_repository import ProfileRepository


def _make_fingerprint() -> LayoutFingerprint:
    return LayoutFingerprint.compute(
        (FingerprintComponent("header_row", "1"),)
    )


def _make_profile(vendor_id: str = "faktura-1", version: int = 1) -> LayoutProfile:
    return LayoutProfile(
        vendor_id=vendor_id,
        version=version,
        fingerprint=_make_fingerprint(),
        rules=(),
        source_documents=("/gold/f1.xlsx",),
        built_at=datetime.now(UTC),
        sample_count=1,
    )


class TestProfileRepositoryProtocol:
    def test_in_memory_satisfies_protocol(self) -> None:
        repo = InMemoryProfileRepository()
        assert isinstance(repo, ProfileRepository)

    def test_custom_implementation_satisfies_protocol(self) -> None:
        class FakeRepo:
            def save(self, profile: LayoutProfile) -> None:
                pass

            def find(
                self,
                vendor_id: str,
                version: int | None = None,
            ) -> LayoutProfile | None:
                return None

            def list_versions(self, vendor_id: str) -> tuple[int, ...]:
                return ()

            def delete(self, vendor_id: str, version: int) -> None:
                pass

        assert isinstance(FakeRepo(), ProfileRepository)

    def test_class_without_methods_not_protocol(self) -> None:
        class NotRepo:
            pass

        assert not isinstance(NotRepo(), ProfileRepository)


class TestInMemoryProfileRepository:
    def test_construction_empty(self) -> None:
        repo = InMemoryProfileRepository()
        assert len(repo) == 0

    def test_save_and_find(self) -> None:
        repo = InMemoryProfileRepository()
        profile = _make_profile()
        repo.save(profile)
        found = repo.find("faktura-1")
        assert found is profile

    def test_find_returns_none_for_missing(self) -> None:
        repo = InMemoryProfileRepository()
        assert repo.find("unknown") is None

    def test_find_by_specific_version(self) -> None:
        repo = InMemoryProfileRepository()
        p1 = _make_profile(version=1)
        p2 = _make_profile(version=2)
        repo.save(p1)
        repo.save(p2)
        assert repo.find("faktura-1", version=1) is p1
        assert repo.find("faktura-1", version=2) is p2
        assert repo.find("faktura-1", version=99) is None

    def test_find_latest_when_no_version(self) -> None:
        repo = InMemoryProfileRepository()
        repo.save(_make_profile(version=1))
        repo.save(_make_profile(version=2))
        repo.save(_make_profile(version=3))
        latest = repo.find("faktura-1")
        assert latest is not None
        assert latest.version == 3

    def test_save_overwrites(self) -> None:
        repo = InMemoryProfileRepository()
        p1 = _make_profile(version=1)
        repo.save(p1)
        # Novi profil sa istim (vendor_id, version) — overwrite
        p1_v2 = _make_profile(version=1)
        repo.save(p1_v2)
        assert repo.find("faktura-1", version=1) is p1_v2

    def test_list_versions(self) -> None:
        repo = InMemoryProfileRepository()
        repo.save(_make_profile(version=1))
        repo.save(_make_profile(version=3))
        repo.save(_make_profile(version=2))
        versions = repo.list_versions("faktura-1")
        assert versions == (1, 2, 3)  # sortirano ascending

    def test_list_versions_empty_for_unknown(self) -> None:
        repo = InMemoryProfileRepository()
        assert repo.list_versions("unknown") == ()

    def test_delete_existing(self) -> None:
        repo = InMemoryProfileRepository()
        repo.save(_make_profile(version=1))
        repo.save(_make_profile(version=2))
        repo.delete("faktura-1", 1)
        assert repo.find("faktura-1", version=1) is None
        assert repo.find("faktura-1", version=2) is not None

    def test_delete_nonexistent_is_noop(self) -> None:
        repo = InMemoryProfileRepository()
        # Should not raise
        repo.delete("unknown", 1)
        repo.delete("faktura-1", 99)

    def test_multiple_vendors_isolation(self) -> None:
        repo = InMemoryProfileRepository()
        repo.save(_make_profile(vendor_id="faktura-1", version=1))
        repo.save(_make_profile(vendor_id="medicopharm", version=1))
        assert repo.list_versions("faktura-1") == (1,)
        assert repo.list_versions("medicopharm") == (1,)
        assert repo.find("faktura-1", version=1) is not None
        assert repo.find("medicopharm", version=1) is not None
        # Ensure they are different objects
        p1 = repo.find("faktura-1")
        p2 = repo.find("medicopharm")
        assert p1 is not p2

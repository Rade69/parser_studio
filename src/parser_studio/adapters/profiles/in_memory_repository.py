# Adapters: profiles/in_memory_repository.
# Posjeduje: InMemoryProfileRepository implementaciju ProfileRepository porta.
# Zna za: parser_studio.domain.profiles, parser_studio.ports.profile_repository.
# Ne zna za: SQLite, presentation, contract.
"""InMemoryProfileRepository — in-memory implementacija ProfileRepository porta.

Koristi se za:
- Unit testove (bez SQLite dependency)
- Brzu validaciju u FAZA E razvoju

Thread-safety: NIJE thread-safe (dict-based). Za production SQLiteRepository
ce dodati thread-safety.
"""
from __future__ import annotations

from parser_studio.domain.profiles.layout_profile import LayoutProfile


class InMemoryProfileRepository:
    """In-memory implementacija ProfileRepository porta.

    Storage: dict[(vendor_id, version)] -> LayoutProfile

    Primjer:
        repo = InMemoryProfileRepository()
        repo.save(profile)
        found = repo.find("faktura-1")  # latest
        versions = repo.list_versions("faktura-1")
        repo.delete("faktura-1", version=1)
    """

    def __init__(self) -> None:
        self._store: dict[tuple[str, int], LayoutProfile] = {}

    def save(self, profile: LayoutProfile) -> None:
        """Persistiraj profil. Overwrite ako vec postoji."""
        self._store[(profile.vendor_id, profile.version)] = profile

    def find(
        self,
        vendor_id: str,
        version: int | None = None,
    ) -> LayoutProfile | None:
        """Vrati profil. version=None znaci najnovija."""
        if version is not None:
            return self._store.get((vendor_id, version))

        # latest = max(version) za vendor_id
        versions = [v for (vid, v) in self._store if vid == vendor_id]
        if not versions:
            return None
        latest_version = max(versions)
        return self._store.get((vendor_id, latest_version))

    def list_versions(self, vendor_id: str) -> tuple[int, ...]:
        """Vrati sortirane verzije (ascending)."""
        versions = sorted(v for (vid, v) in self._store if vid == vendor_id)
        return tuple(versions)

    def delete(self, vendor_id: str, version: int) -> None:
        """Obrisi (vendor_id, version). No-op ako ne postoji."""
        self._store.pop((vendor_id, version), None)

    def __len__(self) -> int:
        """Broj spremljenih profila (za testiranje)."""
        return len(self._store)


__all__ = ["InMemoryProfileRepository"]

# Ports: profile_repository.
# Posjeduje: ProfileRepository Protocol (runtime_checkable).
# Ne zna za: SQLite, PySide6, Docling, openpyxl, contract, adapters.
"""ProfileRepository port — apstrakcija za cuvanje LayoutProfile-a.

Implementacije:
- InMemoryProfileRepository (M2 default, za testiranje)
- SQLiteProfileRepository (FAZA E kasnije, koristi learning_events shemu)
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from parser_studio.domain.profiles.layout_profile import LayoutProfile


@runtime_checkable
class ProfileRepository(Protocol):
    """Port za cuvanje i dohvat LayoutProfile-a."""

    def save(self, profile: LayoutProfile) -> None:
        """Persistiraj profil. Ako vec postoji (vendor_id, version), overwrite."""
        ...

    def find(
        self,
        vendor_id: str,
        version: int | None = None,
    ) -> LayoutProfile | None:
        """Vrati profil. Ako version=None, vrati najnoviju verziju.

        Vraca None ako vendor_id ne postoji ili version ne postoji.
        """
        ...

    def list_versions(self, vendor_id: str) -> tuple[int, ...]:
        """Vrati sortirane verzije (ascending) za vendor_id.

        Prazan tuple ako vendor_id ne postoji.
        """
        ...

    def delete(self, vendor_id: str, version: int) -> None:
        """Obrisi (vendor_id, version). Tihi no-op ako ne postoji.

        V3 ARCH-004: "Profil se mora moci obrisati i ponovo izgraditi."
        """
        ...


__all__ = ["ProfileRepository"]

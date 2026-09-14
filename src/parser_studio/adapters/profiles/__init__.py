# Adapters: profiles.
# Posjeduje: InMemoryProfileRepository (default, M2 testiranje).
# Zna za: parser_studio.domain.profiles, parser_studio.ports.profile_repository.
# Ne zna za: SQLite direktno, presentation, contract.
"""Profile adapters — implementacije ProfileRepository porta.

Trenutno sadrzi samo InMemoryProfileRepository (M2 default).
SQLiteProfileRepository dolazi u FAZA E.
"""
from .in_memory_repository import InMemoryProfileRepository

__all__ = ["InMemoryProfileRepository"]

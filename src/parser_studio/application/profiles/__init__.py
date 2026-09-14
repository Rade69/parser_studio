# Application: profiles.
# Sadrzi: BuildLayoutProfile use case (V3 E2).
# Zna za: domain.profiles, ports.profile_repository.
# Ne zna za: AI provider SDK, SQLite direktno, presentation.
"""Application layer — profile building workflow.

Trenutno sadrzi BuildLayoutProfile (M2, V3 E2). Buduci use case-ovi:
- MatchLayoutProfile (V3 E3)
- DetectProfileDrift (V3 E4)
"""
from .build_layout_profile import (
    BuildLayoutProfile,
    BuildRequest,
    BuildResult,
    GoldSample,
)

__all__ = [
    "BuildLayoutProfile",
    "BuildRequest",
    "BuildResult",
    "GoldSample",
]

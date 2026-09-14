# Application: learning.
# Sadrzi: use case-ove za learning workflow (ConsultAdvisor, ApplyLearning, ...).
# Zna za: domain.evidence, domain.learning, ports.advisor, ports.learning_repository.
# Ne zna za: AI provider SDK, SQLite direktno, presentation.
"""Application layer — learning workflow.

Trenutno sadrzi ConsultAdvisor (M3/G1+G2). Buduci use case-ovi:
- ApplyLearning (azuriranje profile na osnovu potvrde)
- ExportLearningEvents (za trening/analitiku)
"""
from .consult_advisor import (
    ConsultAdvisor,
    ConsultRequest,
    ConsultResult,
)

__all__ = ["ConsultAdvisor", "ConsultRequest", "ConsultResult"]

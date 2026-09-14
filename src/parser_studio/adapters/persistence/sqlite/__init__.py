# Adapter: persistence/sqlite.
# Eksportuje: SQLiteLearningRepository, GoldDataset, GoldEntry, open_connection.
# Ne zna za: domain (apstrahira; samo DTO), application, presentation.
"""SQLite persistence adapter za Parser Studio.

Implementira:
- LearningRepository port (application/review/confirm_invoice.py)
- Gold Dataset projection (read-only VIEW)

Schema:
- learning_events: append-only tabela svih promjena
- gold_dataset_projection: VIEW agregiran iz USER_CONFIRMED/USER_VERIFIED evenata
"""
from .connection import open_connection
from .gold_dataset import GoldDataset, GoldEntry
from .learning_repository import SQLiteLearningRepository

__all__ = ["GoldDataset", "GoldEntry", "SQLiteLearningRepository", "open_connection"]

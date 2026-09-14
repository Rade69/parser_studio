# Adapter: persistence.
# Eksportuje: SQLiteLearningRepository, GoldDataset, GoldEntry, open_connection, run_migrations.
# Ne zna za: domain, application, presentation.
"""Persistence adapters za Parser Studio.

Trenutno samo SQLite (in-memory + file-based).
Za buduću verziju: PostgreSQL, Redis, itd.
"""
from .migrations.runner import MIGRATION_ORDER, run_migrations
from .sqlite import GoldDataset, GoldEntry, SQLiteLearningRepository, open_connection

__all__ = [
    "GoldDataset",
    "GoldEntry",
    "MIGRATION_ORDER",
    "SQLiteLearningRepository",
    "open_connection",
    "run_migrations",
]

# Adapter: persistence/migrations/runner.
# Posjeduje: run_migrations(conn) funkcija.
# Ne zna za: domain, application (samo persistence).
"""Migration runner.

MVP: pokreće sve migracije po redu, idempotentno (CREATE IF NOT EXISTS).
Za buduću verziju: schema_migrations tabela za pracenje verzije.
"""
from __future__ import annotations

import sqlite3
from importlib import resources


MIGRATION_ORDER: tuple[str, ...] = (
    "001_learning_events",
    "002_gold_dataset",
)


def run_migrations(conn: sqlite3.Connection) -> int:
    """Pokreni sve SQL migracije iz migrations paketa.

    Returns: broj uspjesno pokrenutih migracija.
    """
    count = 0
    for name in MIGRATION_ORDER:
        sql_file = resources.files(
            "parser_studio.adapters.persistence.sqlite.migrations"
        ).joinpath(f"{name}.sql")
        sql = sql_file.read_text(encoding="utf-8")
        conn.executescript(sql)
        conn.commit()
        count += 1
    return count


__all__ = ["run_migrations", "MIGRATION_ORDER"]

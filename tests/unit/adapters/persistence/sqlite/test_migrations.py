# Tests: persistence/migrations/runner.
from __future__ import annotations

import sqlite3

import pytest

from parser_studio.adapters.persistence.migrations.runner import (
    MIGRATION_ORDER,
    run_migrations,
)
from parser_studio.adapters.persistence.sqlite.connection import open_connection


class TestMigrations:
    def test_run_migrations_creates_tables(self) -> None:
        conn = open_connection(":memory:")
        count = run_migrations(conn)
        assert count == len(MIGRATION_ORDER)

        # learning_events tabela postoji
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [row["name"] for row in tables]
        assert "learning_events" in table_names

        # gold_dataset_projection VIEW postoji
        views = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='view'"
        ).fetchall()
        view_names = [v["name"] for v in views]
        assert "gold_dataset_projection" in view_names
        conn.close()

    def test_run_migrations_is_idempotent(self) -> None:
        conn = open_connection(":memory:")
        # Prvi run
        run_migrations(conn)
        # Drugi run treba biti OK (CREATE IF NOT EXISTS)
        count = run_migrations(conn)
        assert count == len(MIGRATION_ORDER)
        conn.close()

    def test_indexes_exist(self) -> None:
        conn = open_connection(":memory:")
        run_migrations(conn)
        indexes = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        ).fetchall()
        index_names = [row["name"] for row in indexes]
        assert "idx_learning_events_document_id" in index_names
        assert "idx_learning_events_field_name" in index_names
        assert "idx_learning_events_created_at" in index_names
        assert "idx_learning_events_event_type" in index_names
        conn.close()

    def test_migration_order_is_complete(self) -> None:
        assert "001_learning_events" in MIGRATION_ORDER
        assert "002_gold_dataset" in MIGRATION_ORDER

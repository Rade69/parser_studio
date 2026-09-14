# Adapter: persistence/sqlite/gold_dataset.
# Posjeduje: GoldDataset projection (read-only pristup).
# Ne zna za: domain (apstrahira; samo importuje gold dataset view).
"""Gold Dataset projection — read-only pristup preko VIEW.

Gold Dataset je VIEW u SQLite bazi (ne zasebna tabela) — izveden iz
learning_events filtriran na USER_CONFIRMED i USER_VERIFIED evente.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from parser_studio.adapters.persistence.sqlite.connection import open_connection


@dataclass(frozen=True, slots=True)
class GoldEntry:
    """Jedan entry u Gold Dataset-u."""

    document_id: str
    field_name: str
    confirmed_value: object
    item_id: str | None
    event_type: str
    confirmed_at: datetime
    source: str
    locator_json: str | None


class GoldDataset:
    """Read-only pristup Gold Dataset projection-u."""

    def __init__(self, db_path: str | Path) -> None:
        self._conn = open_connection(db_path)

    def entries(
        self,
        document_id: str | None = None,
        field: str | None = None,
    ) -> list[GoldEntry]:
        """Vrati Gold Dataset entries; opciono filtrirano po dokumentu ili polju."""
        query = (
            "SELECT document_id, item_id, field_name, confirmed_value, "
            "event_type, locator_json, source, confirmed_at "
            "FROM gold_dataset_projection"
        )
        params: tuple = ()
        conditions: list[str] = []
        if document_id is not None:
            conditions.append("document_id = ?")
            params = params + (document_id,)
        if field is not None:
            conditions.append("field_name = ?")
            params = params + (field,)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY confirmed_at"
        rows = self._conn.execute(query, params).fetchall()
        return [
            GoldEntry(
                document_id=row["document_id"],
                field_name=row["field_name"],
                confirmed_value=row["confirmed_value"],
                item_id=row["item_id"],
                event_type=row["event_type"],
                confirmed_at=datetime.fromisoformat(row["confirmed_at"]),
                source=row["source"],
                locator_json=row["locator_json"],
            )
            for row in rows
        ]

    def close(self) -> None:
        self._conn.close()


__all__ = ["GoldDataset", "GoldEntry"]

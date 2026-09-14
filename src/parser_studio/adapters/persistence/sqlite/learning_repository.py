# Adapter: persistence/sqlite/learning_repository.
# Posjeduje: SQLiteLearningRepository implementacija LearningRepository porta.
# Implementira: application/review/confirm_invoice.py::LearningRepository
# Ne zna za: domain (apstrahira; samo importuje LearningEvent kao DTO).
"""SQLite implementacija LearningRepository porta.

Append-only 'learning_events' tabela + Gold Dataset projection VIEW.

V3 sekcija 13/14:
- append: dodaj LearningEvent u learning_events
- events_for: vrati sve evente za dokument (opcionalno po polju)
- events_since: vrati evente poslije datuma (opcionalno po polju)
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from parser_studio.adapters.persistence.migrations.runner import run_migrations
from parser_studio.adapters.persistence.sqlite.connection import open_connection
from parser_studio.domain.evidence.locator import Locator
from parser_studio.domain.learning.learning_event import EventType, LearningEvent


def _serialize_locator(locator: Locator | None) -> str | None:
    if locator is None:
        return None
    return json.dumps(
        {
            "source_path": locator.source_path,
            "kind": locator.kind,
            "page": locator.page,
            "bbox": locator.bbox,
            "sheet": locator.sheet,
            "row": locator.row,
            "col": locator.col,
            "char_span": locator.char_span,
        }
    )


def _deserialize_locator(data: str | None) -> Locator | None:
    if data is None:
        return None
    d = json.loads(data)
    return Locator(
        source_path=d["source_path"],
        kind=d["kind"],
        page=d.get("page"),
        bbox=d.get("bbox"),
        sheet=d.get("sheet"),
        row=d.get("row"),
        col=d.get("col"),
        char_span=d.get("char_span"),
    )


def _serialize_value(value: object) -> str | None:
    if value is None:
        return None
    return json.dumps(value, default=str)


def _deserialize_value(data: str | None) -> object:
    if data is None:
        return None
    return json.loads(data)


class SQLiteLearningRepository:
    """SQLite implementacija LearningRepository porta.

    Koristi append-only 'learning_events' tabelu sa JSON-serializovanim
    old_value/new_value/locator. Locator je round-trip safe.
    """

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = str(db_path)
        self._conn = open_connection(self._db_path)
        run_migrations(self._conn)

    def append(self, event: LearningEvent) -> None:
        """Dodaj LearningEvent u learning_events."""
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO learning_events (
                    document_id, item_id, field_name, event_type,
                    old_value, new_value, locator_json, source, note,
                    created_at, schema_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    event.document_id,
                    event.item_id,
                    event.field_name,
                    event.event_type.value,
                    _serialize_value(event.old_value),
                    _serialize_value(event.new_value),
                    _serialize_locator(event.locator),
                    event.source,
                    event.note,
                    event.created_at.isoformat(),
                ),
            )

    def events_for(
        self, document_id: str, field: str | None = None
    ) -> list[LearningEvent]:
        """Vrati sve evente za dati dokument (opcionalno filtrirano po polju)."""
        if field is None:
            rows = self._conn.execute(
                """
                SELECT id, document_id, item_id, field_name, event_type,
                       old_value, new_value, locator_json, source, note, created_at
                FROM learning_events
                WHERE document_id = ?
                ORDER BY created_at, id
                """,
                (document_id,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT id, document_id, item_id, field_name, event_type,
                       old_value, new_value, locator_json, source, note, created_at
                FROM learning_events
                WHERE document_id = ? AND field_name = ?
                ORDER BY created_at, id
                """,
                (document_id, field),
            ).fetchall()
        return [_row_to_event(row) for row in rows]

    def events_since(
        self, since: datetime, field: str | None = None
    ) -> list[LearningEvent]:
        """Vrati evente kreirane poslije 'since' (opcionalno filtrirano po polju)."""
        since_iso = since.isoformat()
        if field is None:
            rows = self._conn.execute(
                """
                SELECT id, document_id, item_id, field_name, event_type,
                       old_value, new_value, locator_json, source, note, created_at
                FROM learning_events
                WHERE created_at >= ?
                ORDER BY created_at, id
                """,
                (since_iso,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT id, document_id, item_id, field_name, event_type,
                       old_value, new_value, locator_json, source, note, created_at
                FROM learning_events
                WHERE created_at >= ? AND field_name = ?
                ORDER BY created_at, id
                """,
                (since_iso, field),
            ).fetchall()
        return [_row_to_event(row) for row in rows]

    def close(self) -> None:
        """Zatvori SQLite konekciju."""
        self._conn.close()

    def __enter__(self) -> "SQLiteLearningRepository":
        return self

    def __exit__(self, *args) -> None:
        self.close()


def _row_to_event(row: sqlite3.Row) -> LearningEvent:
    return LearningEvent(
        document_id=row["document_id"],
        field_name=row["field_name"],
        event_type=EventType(row["event_type"]),
        new_value=_deserialize_value(row["new_value"]),
        locator=_deserialize_locator(row["locator_json"]),
        source=row["source"],
        item_id=row["item_id"],
        old_value=_deserialize_value(row["old_value"]),
        note=row["note"] or "",
        created_at=datetime.fromisoformat(row["created_at"]),
    )


__all__ = ["SQLiteLearningRepository"]

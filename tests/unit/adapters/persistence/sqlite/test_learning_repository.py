# Tests: persistence/sqlite/learning_repository.
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone, timedelta

import pytest

from parser_studio.adapters.persistence import SQLiteLearningRepository
from parser_studio.domain.evidence.locator import Locator
from parser_studio.domain.learning.learning_event import EventType, LearningEvent


def _make_locator() -> Locator:
    return Locator(source_path="f.xlsx", kind="excel", sheet="S1", row=1, col=2)


def _make_event(
    document_id: str = "doc-1",
    field_name: str = "kolicina",
    event_type: EventType = EventType.USER_CONFIRMED,
    new_value: object = 5,
    source: str = "user:radovan",
    created_at: datetime | None = None,
) -> LearningEvent:
    if created_at is None:
        created_at = datetime.now(timezone.utc)
    return LearningEvent(
        document_id=document_id,
        field_name=field_name,
        event_type=event_type,
        new_value=new_value,
        locator=_make_locator(),
        source=source,
        created_at=created_at,
    )


class TestSQLiteLearningRepositoryConstruction:
    def test_in_memory_creates_tables(self) -> None:
        repo = SQLiteLearningRepository(":memory:")
        # Ako tabele nisu kreirane, events_for baca gresku
        events = repo.events_for("any-doc")
        assert events == []
        repo.close()

    def test_file_based_creates_file(self, tmp_path) -> None:
        db_file = tmp_path / "test.db"
        repo = SQLiteLearningRepository(db_file)
        repo.close()
        assert db_file.exists()


class TestAppend:
    def test_single_event(self) -> None:
        repo = SQLiteLearningRepository(":memory:")
        ev = _make_event()
        repo.append(ev)
        events = repo.events_for("doc-1")
        assert len(events) == 1
        assert events[0].field_name == "kolicina"
        repo.close()

    def test_multiple_events_ordered_by_created_at(self) -> None:
        repo = SQLiteLearningRepository(":memory:")
        now = datetime.now(timezone.utc)
        ev1 = _make_event(created_at=now - timedelta(seconds=2))
        ev2 = _make_event(created_at=now - timedelta(seconds=1))
        ev3 = _make_event(created_at=now)
        repo.append(ev3)
        repo.append(ev1)
        repo.append(ev2)
        events = repo.events_for("doc-1")
        assert len(events) == 3
        assert events[0].created_at <= events[1].created_at <= events[2].created_at
        repo.close()


class TestEventsFor:
    def test_filter_by_document(self) -> None:
        repo = SQLiteLearningRepository(":memory:")
        repo.append(_make_event(document_id="doc-1"))
        repo.append(_make_event(document_id="doc-2"))
        assert len(repo.events_for("doc-1")) == 1
        assert len(repo.events_for("doc-2")) == 1
        assert len(repo.events_for("doc-3")) == 0
        repo.close()

    def test_filter_by_field(self) -> None:
        repo = SQLiteLearningRepository(":memory:")
        repo.append(_make_event(field_name="kolicina"))
        repo.append(_make_event(field_name="cijena_jed"))
        assert len(repo.events_for("doc-1", field="kolicina")) == 1
        assert len(repo.events_for("doc-1", field="cijena_jed")) == 1
        assert len(repo.events_for("doc-1", field="unknown")) == 0
        repo.close()


class TestEventsSince:
    def test_filter_by_date(self) -> None:
        repo = SQLiteLearningRepository(":memory:")
        now = datetime.now(timezone.utc)
        repo.append(_make_event(created_at=now - timedelta(hours=2)))
        repo.append(_make_event(created_at=now - timedelta(hours=1)))
        repo.append(_make_event(created_at=now))
        events = repo.events_since(now - timedelta(minutes=30))
        assert len(events) == 1
        repo.close()

    def test_filter_by_date_and_field(self) -> None:
        repo = SQLiteLearningRepository(":memory:")
        now = datetime.now(timezone.utc)
        repo.append(_make_event(created_at=now - timedelta(hours=2), field_name="kolicina"))
        repo.append(_make_event(created_at=now, field_name="cijena_jed"))
        events = repo.events_since(now - timedelta(minutes=30), field="cijena_jed")
        assert len(events) == 1
        assert events[0].field_name == "cijena_jed"
        repo.close()


class TestRoundTrip:
    def test_locator_roundtrip(self) -> None:
        repo = SQLiteLearningRepository(":memory:")
        original_locator = Locator(
            source_path="test.xlsx",
            kind="excel",
            sheet="Faktura",
            row=3,
            col=5,
            page=None,
            bbox=None,
            char_span=None,
        )
        ev = LearningEvent(
            document_id="d",
            field_name="kolicina",
            event_type=EventType.USER_CONFIRMED,
            new_value=42,
            locator=original_locator,
            source="test",
        )
        repo.append(ev)
        events = repo.events_for("d")
        assert len(events) == 1
        assert events[0].locator == original_locator
        repo.close()

    def test_value_roundtrip(self) -> None:
        repo = SQLiteLearningRepository(":memory:")
        ev = _make_event(new_value={"nested": "dict", "list": [1, 2, 3]})
        repo.append(ev)
        events = repo.events_for("doc-1")
        assert events[0].new_value == {"nested": "dict", "list": [1, 2, 3]}
        repo.close()


class TestClose:
    def test_close_method(self) -> None:
        repo = SQLiteLearningRepository(":memory:")
        repo.close()

    def test_context_manager(self) -> None:
        with SQLiteLearningRepository(":memory:") as repo:
            repo.append(_make_event())
            assert len(repo.events_for("doc-1")) == 1

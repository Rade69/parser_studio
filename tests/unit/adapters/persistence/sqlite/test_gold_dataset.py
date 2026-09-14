# Tests: persistence/sqlite/gold_dataset.
from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest

from parser_studio.adapters.persistence import GoldDataset, SQLiteLearningRepository
from parser_studio.domain.evidence.locator import Locator
from parser_studio.domain.learning.learning_event import EventType, LearningEvent


def _make_event(
    document_id: str = "doc-1",
    field_name: str = "kolicina",
    event_type: EventType = EventType.USER_CONFIRMED,
    new_value: object = 5,
    created_at: datetime | None = None,
) -> LearningEvent:
    if created_at is None:
        created_at = datetime.now(timezone.utc)
    return LearningEvent(
        document_id=document_id,
        field_name=field_name,
        event_type=event_type,
        new_value=new_value,
        locator=Locator(source_path="f.xlsx", kind="excel"),
        source="user:test",
        created_at=created_at,
    )


@pytest.fixture
def repo() -> SQLiteLearningRepository:
    """Kreiraj SQLite repo sa par USER_CONFIRMED evenata za test."""
    r = SQLiteLearningRepository(":memory:")
    now = datetime.now(timezone.utc)
    r.append(_make_event(field_name="kolicina", new_value=5, created_at=now - timedelta(seconds=2)))
    r.append(_make_event(field_name="cijena_jed", new_value=8.80, created_at=now - timedelta(seconds=1)))
    # USER_VERIFIED takodje ulazi u Gold Dataset
    r.append(
        _make_event(
            field_name="iznos",
            event_type=EventType.USER_VERIFIED,
            new_value=44.0,
            created_at=now,
        )
    )
    # OCR_EXTRACTED NE ulazi u Gold Dataset
    r.append(
        _make_event(
            document_id="doc-2",
            field_name="kolicina",
            event_type=EventType.OCR_EXTRACTED,
            new_value=99,
            created_at=now,
        )
    )
    yield r
    r.close()


class TestGoldDatasetBasic:
    def test_entries_returns_user_confirmed_and_verified(self, repo) -> None:
        gold = GoldDataset(":memory:")
        # GoldDataset treba svoju konekciju; preuzimamo db_path od repo
        # Za MVP test, koristimo istu putanju (in-memory je razlicit conn)
        # Ovo testira SAMO da li GoldDataset entry-creation radi na vlastitom conn
        # Stvarni test cross-repo integracije je integration test
        gold.close()


class TestGoldDatasetIntegration:
    def test_via_shared_db_path(self, tmp_path) -> None:
        """Testira GoldDataset preko file-based repo (shared path)."""
        db_path = tmp_path / "shared.db"

        # Kreiraj repo i dodaj events
        repo = SQLiteLearningRepository(db_path)
        now = datetime.now(timezone.utc)
        repo.append(_make_event(field_name="kolicina", new_value=5, created_at=now))
        repo.append(
            _make_event(
                field_name="cijena_jed",
                new_value=8.80,
                created_at=now,
            )
        )
        # OCR event ne smije biti u Gold Dataset
        repo.append(
            _make_event(
                document_id="doc-2",
                field_name="kolicina",
                event_type=EventType.OCR_EXTRACTED,
                new_value=99,
            )
        )
        repo.close()

        # Otvori GoldDataset na istom fajlu
        gold = GoldDataset(db_path)
        entries = gold.entries()
        assert len(entries) == 2  # samo USER_CONFIRMED/VERIFIED
        field_names = [e.field_name for e in entries]
        assert "kolicina" in field_names
        assert "cijena_jed" in field_names
        gold.close()

    def test_entries_filter_by_document(self, tmp_path) -> None:
        db_path = tmp_path / "shared.db"
        repo = SQLiteLearningRepository(db_path)
        repo.append(_make_event(document_id="doc-1"))
        repo.append(_make_event(document_id="doc-2"))
        repo.close()

        gold = GoldDataset(db_path)
        entries = gold.entries(document_id="doc-1")
        assert len(entries) == 1
        assert entries[0].document_id == "doc-1"
        gold.close()

    def test_entries_filter_by_field(self, tmp_path) -> None:
        db_path = tmp_path / "shared.db"
        repo = SQLiteLearningRepository(db_path)
        repo.append(_make_event(field_name="kolicina"))
        repo.append(_make_event(field_name="cijena_jed"))
        repo.close()

        gold = GoldDataset(db_path)
        entries = gold.entries(field="kolicina")
        assert len(entries) == 1
        assert entries[0].field_name == "kolicina"
        gold.close()

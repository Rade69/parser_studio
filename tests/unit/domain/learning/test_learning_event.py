# Tests: learning/learning_event.
from __future__ import annotations

import pytest

from parser_studio.domain.evidence.locator import Locator
from parser_studio.domain.learning.learning_event import EventType, LearningEvent


def _make_locator() -> Locator:
    return Locator(source_path="f.xlsx", kind="excel", sheet="S1")


class TestLearningEventConstruction:
    def test_minimum(self) -> None:
        ev = LearningEvent(
            document_id="doc-1",
            field_name="kolicina",
            event_type=EventType.USER_CONFIRMED,
            new_value=10,
            locator=_make_locator(),
            source="user:radovan",
        )
        assert ev.document_id == "doc-1"
        assert ev.field_name == "kolicina"
        assert ev.event_type == EventType.USER_CONFIRMED
        assert ev.new_value == 10
        assert ev.old_value is None
        assert ev.note == ""

    def test_full(self) -> None:
        ev = LearningEvent(
            document_id="doc-2",
            field_name="iznos",
            event_type=EventType.USER_CORRECTED,
            new_value=99.50,
            locator=_make_locator(),
            source="user:jadovan",
            item_id="item-3",
            old_value=100.00,
            note="ispravka nakon ručnog pregleda",
        )
        assert ev.item_id == "item-3"
        assert ev.old_value == 100.00
        assert ev.note == "ispravka nakon ručnog pregleda"


class TestLearningEventFrozen:
    def test_mutation_raises(self) -> None:
        ev = LearningEvent(
            document_id="d",
            field_name="x",
            event_type=EventType.OCR_EXTRACTED,
            new_value=1,
            locator=_make_locator(),
            source="ocr",
        )
        with pytest.raises((AttributeError, Exception)):
            ev.field_name = "y"  # type: ignore[misc]


class TestEventType:
    def test_enum_values(self) -> None:
        assert EventType.OCR_EXTRACTED.value == "OCR_EXTRACTED"
        assert EventType.VALIDATION_FAILED.value == "VALIDATION_FAILED"
        assert EventType.USER_CORRECTED.value == "USER_CORRECTED"
        assert EventType.USER_VERIFIED.value == "USER_VERIFIED"
        assert EventType.USER_CONFIRMED.value == "USER_CONFIRMED"

    def test_is_str(self) -> None:
        assert isinstance(EventType.USER_CONFIRMED, str)
        assert EventType.USER_CONFIRMED == "USER_CONFIRMED"


class TestLearningEventValidation:
    def test_empty_document_id_raises(self) -> None:
        with pytest.raises(ValueError, match="document_id"):
            LearningEvent(
                document_id="",
                field_name="x",
                event_type=EventType.OCR_EXTRACTED,
                new_value=1,
                locator=_make_locator(),
                source="ocr",
            )

    def test_empty_field_name_raises(self) -> None:
        with pytest.raises(ValueError, match="field_name"):
            LearningEvent(
                document_id="d",
                field_name="",
                event_type=EventType.OCR_EXTRACTED,
                new_value=1,
                locator=_make_locator(),
                source="ocr",
            )

    def test_empty_source_raises(self) -> None:
        with pytest.raises(ValueError, match="source"):
            LearningEvent(
                document_id="d",
                field_name="x",
                event_type=EventType.OCR_EXTRACTED,
                new_value=1,
                locator=_make_locator(),
                source="",
            )

# Tests: Evidence.
from __future__ import annotations

import pytest

from parser_studio.domain.evidence import Evidence, Locator


def _make_locator() -> Locator:
    return Locator(source_path="f.xlsx", kind="excel", sheet="S1", row=1, col=2)


class TestEvidenceConstruction:
    def test_minimal(self) -> None:
        ev = Evidence(
            raw_value=42,
            raw_text="42",
            locator=_make_locator(),
            element_type="excel_cell",
        )
        assert ev.raw_value == 42
        assert ev.raw_text == "42"
        assert ev.element_type == "excel_cell"
        assert ev.source_id is None

    def test_with_source_id(self) -> None:
        ev = Evidence(
            raw_value="hello",
            raw_text="hello",
            locator=_make_locator(),
            element_type="text",
            source_id="src-001",
        )
        assert ev.source_id == "src-001"


class TestEvidenceFrozen:
    def test_mutation_raises(self) -> None:
        ev = Evidence(
            raw_value=42,
            raw_text="42",
            locator=_make_locator(),
            element_type="cell",
        )
        with pytest.raises((AttributeError, Exception)):
            ev.raw_value = 999  # type: ignore[misc]

    def test_no_dict(self) -> None:
        ev = Evidence(
            raw_value=42,
            raw_text="42",
            locator=_make_locator(),
            element_type="cell",
        )
        assert not hasattr(ev, "__dict__")


class TestEvidenceValidation:
    def test_invalid_locator_type_raises(self) -> None:
        with pytest.raises(TypeError, match="locator mora biti"):
            Evidence(
                raw_value=42,
                raw_text="42",
                locator="not-a-locator",  # type: ignore[arg-type]
                element_type="cell",
            )

    def test_empty_element_type_raises(self) -> None:
        with pytest.raises(ValueError, match="element_type"):
            Evidence(
                raw_value=42,
                raw_text="42",
                locator=_make_locator(),
                element_type="",
            )

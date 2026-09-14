# Tests: Locator.
from __future__ import annotations

import pytest

from parser_studio.domain.evidence import Locator


class TestLocatorConstruction:
    def test_minimal_excel_locator(self) -> None:
        loc = Locator(source_path="file.xlsx", kind="excel", sheet="Sheet1")
        assert loc.source_path == "file.xlsx"
        assert loc.kind == "excel"
        assert loc.sheet == "Sheet1"
        assert loc.page is None
        assert loc.bbox is None
        assert loc.row is None
        assert loc.col is None
        assert loc.char_span is None

    def test_full_pdf_locator(self) -> None:
        loc = Locator(
            source_path="scan.pdf",
            kind="pdf",
            page=3,
            bbox=(0.1, 0.2, 0.3, 0.4),
            char_span=(10, 20),
        )
        assert loc.page == 3
        assert loc.bbox == (0.1, 0.2, 0.3, 0.4)
        assert loc.char_span == (10, 20)


class TestLocatorFrozen:
    def test_mutation_raises(self) -> None:
        loc = Locator(source_path="f.xlsx", kind="excel")
        with pytest.raises((AttributeError, Exception)):
            loc.source_path = "other.xlsx"  # type: ignore[misc]

    def test_no_dict(self) -> None:
        loc = Locator(source_path="f.xlsx", kind="excel")
        assert not hasattr(loc, "__dict__"), "slots=True zahtijeva odsustvo __dict__"


class TestLocatorSlots:
    def test_has_slots(self) -> None:
        assert "__slots__" in Locator.__dict__ or "__slots__" in vars(Locator)


class TestLocatorDefaults:
    def test_text_kind_accepted(self) -> None:
        loc = Locator(source_path="note.txt", kind="text", char_span=(0, 100))
        assert loc.kind == "text"


class TestLocatorValidation:
    def test_invalid_kind_raises(self) -> None:
        with pytest.raises(ValueError, match="kind mora biti"):
            Locator(source_path="f.xlsx", kind="docx")  # type: ignore[arg-type]

    def test_invalid_bbox_length_raises(self) -> None:
        with pytest.raises(ValueError, match="bbox mora imati 4"):
            Locator(source_path="f.pdf", kind="pdf", bbox=(0.1, 0.2, 0.3))  # type: ignore[arg-type]

    def test_negative_page_raises(self) -> None:
        with pytest.raises(ValueError, match="page ne može"):
            Locator(source_path="f.pdf", kind="pdf", page=-1)

    def test_negative_row_raises(self) -> None:
        with pytest.raises(ValueError, match="row ne može"):
            Locator(source_path="f.xlsx", kind="excel", row=-1)

    def test_negative_col_raises(self) -> None:
        with pytest.raises(ValueError, match="col ne može"):
            Locator(source_path="f.xlsx", kind="excel", col=-1)

    def test_invalid_char_span_raises(self) -> None:
        with pytest.raises(ValueError, match="char_span"):
            Locator(source_path="f.txt", kind="text", char_span=(10, 5))

    def test_empty_char_span_raises(self) -> None:
        with pytest.raises(ValueError, match="char_span"):
            Locator(source_path="f.txt", kind="text", char_span=(5, 5))

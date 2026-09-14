# Tests: ExcelDocumentReader.
from __future__ import annotations

from pathlib import Path

import pytest

from openpyxl import Workbook

from parser_studio.adapters.documents.excel_reader import (
    EXCEL_EXTENSIONS,
    ExcelDocumentReader,
)
from parser_studio.ports.document_reader import DocumentReader


@pytest.fixture
def sample_xlsx(tmp_path: Path) -> Path:
    """Mali Excel koji imitira strukturu fakture: header podaci, pa stavke."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Faktura"
    ws.append(["SUMAPROM DOO", None, None, "Faktura br.", "059/2022"])
    ws.append([])
    ws.append(["Pos.", "Item Code", "Description", "U.M.", "Quantity", "Unit Price"])
    ws.append([1, "A-100", "STARTNO UZE 4mm", "KOM", 5, 8.80])
    ws.append([2, "B-200", "NOZ KOSILICE", "KOM", 10, 6.30])
    ws.append([3, "C-300", "LANAC", "KOM", None, 12.50])

    ws2 = wb.create_sheet("Prazan")
    ws2.append(["nista"])

    path = tmp_path / "sumaprom_uzorak.xlsx"
    wb.save(path)
    wb.close()
    return path


class TestExcelReaderConstruction:
    def test_reader_id(self) -> None:
        reader = ExcelDocumentReader()
        assert reader.reader_id == "excel"

    def test_implements_document_reader_protocol(self) -> None:
        reader = ExcelDocumentReader()
        assert isinstance(reader, DocumentReader)


class TestSupports:
    def test_supports_xlsx(self, tmp_path: Path) -> None:
        reader = ExcelDocumentReader()
        assert reader.supports(tmp_path / "a.xlsx") is True

    def test_supports_xlsm(self, tmp_path: Path) -> None:
        reader = ExcelDocumentReader()
        assert reader.supports(tmp_path / "a.xlsm") is True

    def test_supports_xls(self, tmp_path: Path) -> None:
        reader = ExcelDocumentReader()
        assert reader.supports(tmp_path / "a.xls") is True

    def test_rejects_pdf(self, tmp_path: Path) -> None:
        reader = ExcelDocumentReader()
        assert reader.supports(tmp_path / "a.pdf") is False

    def test_rejects_txt(self, tmp_path: Path) -> None:
        reader = ExcelDocumentReader()
        assert reader.supports(tmp_path / "a.txt") is False

    def test_extensions_constant(self) -> None:
        assert ".xlsx" in EXCEL_EXTENSIONS
        assert ".xlsm" in EXCEL_EXTENSIONS
        assert ".xls" in EXCEL_EXTENSIONS
        assert ".pdf" not in EXCEL_EXTENSIONS


class TestReadXlsx:
    def test_read_produces_document_evidence(self, sample_xlsx: Path) -> None:
        reader = ExcelDocumentReader()
        doc = reader.read(sample_xlsx)
        assert doc.document_id
        assert doc.source_path == str(sample_xlsx)

    def test_read_returns_all_sheets_in_pages(self, sample_xlsx: Path) -> None:
        reader = ExcelDocumentReader()
        doc = reader.read(sample_xlsx)
        assert "Faktura" in doc.pages
        assert "Prazan" in doc.pages

    def test_read_returns_cells_with_locators(self, sample_xlsx: Path) -> None:
        reader = ExcelDocumentReader()
        doc = reader.read(sample_xlsx)
        assert len(doc.cells) > 0
        cell = doc.cells[0]
        assert cell.locator.kind == "excel"
        assert cell.locator.sheet
        assert cell.locator.row is not None
        assert cell.locator.col is not None
        assert cell.element_type == "excel_cell"
        assert cell.source_id == "excel"

    def test_read_includes_known_values(self, sample_xlsx: Path) -> None:
        reader = ExcelDocumentReader()
        doc = reader.read(sample_xlsx)
        values = [c.raw_value for c in doc.cells]
        assert "SUMAPROM DOO" in values
        assert "A-100" in values
        assert "STARTNO UZE 4mm" in values
        assert 5 in values
        assert 8.80 in values

    def test_read_skips_none_cells(self, sample_xlsx: Path) -> None:
        reader = ExcelDocumentReader()
        doc = reader.read(sample_xlsx)
        for cell in doc.cells:
            assert cell.raw_value is not None
            assert cell.raw_text != ""


class TestCaching:
    def test_caching_returns_same_document(self, sample_xlsx: Path) -> None:
        reader = ExcelDocumentReader()
        doc1 = reader.read(sample_xlsx)
        doc2 = reader.read(sample_xlsx)
        assert doc1 is doc2
        assert doc1.document_id == doc2.document_id


class TestErrorHandling:
    def test_nonexistent_file_raises(self, tmp_path: Path) -> None:
        reader = ExcelDocumentReader()
        with pytest.raises(FileNotFoundError):
            reader.read(tmp_path / "nema.xlsx")

    def test_invalid_format_raises(self, tmp_path: Path) -> None:
        p = tmp_path / "a.txt"
        p.write_text("x")
        reader = ExcelDocumentReader()
        # supports() vraca False, ali ako se read() pozove direktno na .txt...
        with pytest.raises(ValueError):
            reader.read(p)

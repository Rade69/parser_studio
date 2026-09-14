# Tests: presentation/cli/test_psbuild.
from __future__ import annotations

from pathlib import Path

import pytest
from openpyxl import Workbook

from parser_studio.presentation.cli import psbuild


@pytest.fixture
def sample_xlsx(tmp_path: Path) -> Path:
    """Mali Excel fajl za CLI testiranje."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Faktura"
    ws.append(["Naziv", "Kolicina"])
    ws.append(["Proizvod A", 5])
    path = tmp_path / "cli_test.xlsx"
    wb.save(path)
    wb.close()
    return path


@pytest.fixture(autouse=True)
def temp_sqlite_db(monkeypatch, tmp_path: Path):
    """Override PARSER_STUDIO_DB za CLI test (in-memory za CLI komande)."""
    # CLI koristi ":memory:" za build_default_application;
    # ali env var moze biti postavljen od strane drugih testova.
    # Ne diramo env var; CLI koristi ":memory:" default.
    yield


class TestCLIArgs:
    def test_version_flag(self, capsys) -> None:
        with pytest.raises(SystemExit) as exc_info:
            psbuild.main(["--version"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "psbuild" in captured.out
        assert psbuild.VERSION in captured.out

    def test_help_flag(self, capsys) -> None:
        with pytest.raises(SystemExit):
            psbuild.main(["--help"])

    def test_no_args_prints_help(self, capsys) -> None:
        result = psbuild.main([])
        assert result == 1
        captured = capsys.readouterr()
        assert "usage:" in captured.out or "Parser Studio" in captured.out


class TestCLIImport:
    def test_import_command(self, sample_xlsx: Path, capsys) -> None:
        result = psbuild.main(["import", str(sample_xlsx)])
        assert result == 0
        captured = capsys.readouterr()
        assert "Cells:" in captured.out
        assert "Sheets:" in captured.out

    def test_import_nonexistent_file(self, capsys) -> None:
        # File ne postoji, CLI vraca exit code 1
        result = psbuild.main(["import", "/nonexistent/path/file.xlsx"])
        assert result == 1


class TestCLIAnalyze:
    def test_analyze_command(self, sample_xlsx: Path, capsys) -> None:
        result = psbuild.main(["analyze", str(sample_xlsx)])
        assert result == 0
        captured = capsys.readouterr()
        assert "kolicina:" in captured.out
        assert "naziv_robe:" in captured.out


class TestCLIConfirm:
    def test_confirm_command(self, sample_xlsx: Path, capsys) -> None:
        result = psbuild.main([
            "confirm", str(sample_xlsx),
            "--field", "kolicina=10",
            "--actor", "user:test",
        ])
        assert result == 0
        captured = capsys.readouterr()
        assert "Confirmed 1 field(s)" in captured.out


class TestBuildParser:
    def test_build_parser_returns_parser(self) -> None:
        parser = psbuild.build_parser()
        assert parser is not None
        assert parser.prog == "psbuild"

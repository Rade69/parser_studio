"""Unit testovi za parser_oracle port (Protocol + error hijerarhija)."""
from __future__ import annotations

from pathlib import Path

from contract.import_result import ImportResult
from parser_studio.ports.parser_oracle import (
    OracleError,
    OracleImportFailedError,
    OracleUnavailableError,
    OracleUnsupportedFormatError,
    ParserOracle,
)


class FakeOracle:
    """Minimalna implementacija ParserOracle porta za testiranje."""

    def __init__(self, name="fake", can_handle_result=True, result=None):
        self._name = name
        self._can_handle = can_handle_result
        self._result = result if result is not None else ImportResult(invoice_name="test")

    def oracle_name(self) -> str:
        return self._name

    def can_handle(self, path: Path) -> bool:
        return self._can_handle

    def import_file(self, path, progress=None):
        return self._result


class TestParserOracleProtocol:
    def test_protocol_is_runtime_checkable(self):
        """Protocol sa @runtime_checkable dozvoljava isinstance check."""
        fake = FakeOracle()
        assert isinstance(fake, ParserOracle)

    def test_protocol_methods_required(self):
        """Sve tri metode (oracle_name, can_handle, import_file) su dio interface-a."""
        fake = FakeOracle()
        assert hasattr(fake, "oracle_name")
        assert hasattr(fake, "can_handle")
        assert hasattr(fake, "import_file")
        assert callable(fake.oracle_name)
        assert callable(fake.can_handle)
        assert callable(fake.import_file)

    def test_oracle_name_returns_string(self):
        fake = FakeOracle(name="moj_oracle")
        assert fake.oracle_name() == "moj_oracle"

    def test_can_handle_returns_bool(self):
        fake = FakeOracle(can_handle_result=False)
        assert fake.can_handle(Path("x.xlsx")) is False

    def test_import_file_returns_import_result(self):
        result = ImportResult(invoice_name="faktura 1")
        fake = FakeOracle(result=result)
        assert fake.import_file(Path("x.xlsx")) is result


class TestOracleErrors:
    def test_oracle_error_is_exception(self):
        assert issubclass(OracleError, Exception)

    def test_oracle_unavailable_is_oracle_error(self):
        assert issubclass(OracleUnavailableError, OracleError)

    def test_oracle_unsupported_format_is_oracle_error(self):
        assert issubclass(OracleUnsupportedFormatError, OracleError)

    def test_oracle_import_failed_is_oracle_error(self):
        assert issubclass(OracleImportFailedError, OracleError)

    def test_oracle_error_can_be_raised(self):
        with __import__("pytest").raises(OracleError):
            raise OracleError("test")

    def test_oracle_unavailable_can_carry_path(self):
        try:
            raise OracleUnavailableError("deklarant_pro root: /foo")
        except OracleUnavailableError as exc:
            assert "deklarant_pro" in str(exc)


class TestErrorHierarchyCatching:
    """Aplikacija može uhvatiti SVE oracle greške jednim except blokom."""

    def test_catch_all_oracle_errors(self):
        errors = [
            OracleUnavailableError("a"),
            OracleUnsupportedFormatError("b"),
            OracleImportFailedError("c"),
        ]
        for err in errors:
            try:
                raise err
            except OracleError:
                pass  # sve tri su OracleError
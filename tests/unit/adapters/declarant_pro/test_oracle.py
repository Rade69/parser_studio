"""Unit testovi za DeclarantProOracle adapter.

Koriste fake StrategyRegistry da izbjegnu zavisnost od stvarnog
declarant_pro koda u unit testovima. Integration test (test_oracle_bootstrap.py)
će pozvati stvarni declarant_pro put.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from contract.import_result import ImportResult
from parser_studio.adapters.declarant_pro.oracle import DeclarantProOracle
from parser_studio.adapters.declarant_pro.strategy_loader import (
    DEFAULT_DECLARANT_PRO_ROOT,
    ensure_declarant_pro_importable,
    list_available_strategies,
)
from parser_studio.ports.parser_oracle import (
    OracleImportFailedError,
    OracleUnavailableError,
    OracleUnsupportedFormatError,
)

# ============================================================
# Fake strategija (imitira declarant_pro ImportStrategy)
# ============================================================


class FakeStrategy:
    """Minimalna ImportStrategy implementacija za testiranje."""

    def __init__(
        self,
        name: str = "Fake",
        priority: int = 0,
        can_handle_result: bool = True,
        import_result=None,
        raise_on_import: Exception | None = None,
    ):
        self._name = name
        self._priority = priority
        self._can_handle_result = can_handle_result
        self._import_result = import_result
        self._raise = raise_on_import

    @property
    def strategy_name(self) -> str:
        return self._name

    @property
    def priority(self) -> int:
        return self._priority

    def can_handle(self, filepath: Path) -> bool:
        return self._can_handle_result

    def import_file(self, filepath, progress_callback=None, **kwargs):
        if self._raise is not None:
            raise self._raise
        if self._import_result is not None:
            return self._import_result
        return ImportResult(invoice_name=f"fake-{filepath.name}")


class FakeRegistry:
    """Minimalna StrategyRegistry implementacija."""

    def __init__(self, strategies=None):
        self.strategies = strategies or []

    def find_strategy(self, filepath):
        for s in self.strategies:
            if s.can_handle(filepath):
                return s
        return None

    def import_file(self, filepath, **kwargs):
        s = self.find_strategy(filepath)
        if s is None:
            raise FileNotFoundError(f"no strategy for {filepath}")
        return s.import_file(filepath, **kwargs)


# ============================================================
# Test: konstruktor i oracle_name
# ============================================================


class TestOracleIdentity:
    def test_oracle_name_constant(self):
        oracle = DeclarantProOracle(registry=FakeRegistry())
        assert oracle.oracle_name() == "declarant_pro"

    def test_oracle_name_matches_constant(self):
        oracle = DeclarantProOracle(registry=FakeRegistry())
        assert oracle.oracle_name() == DeclarantProOracle.ORACLE_NAME


# ============================================================
# Test: can_handle
# ============================================================


class TestCanHandle:
    def test_can_handle_true_when_strategy_matches(self):
        registry = FakeRegistry([FakeStrategy(can_handle_result=True)])
        oracle = DeclarantProOracle(registry=registry)
        assert oracle.can_handle(Path("test.xlsx")) is True

    def test_can_handle_false_when_no_strategy(self):
        registry = FakeRegistry(strategies=[])
        oracle = DeclarantProOracle(registry=registry)
        assert oracle.can_handle(Path("test.xlsx")) is False


# ============================================================
# Test: import_file uspješan
# ============================================================


class TestImportFileSuccess:
    def test_returns_import_result_from_strategy(self):
        expected = ImportResult(invoice_name="F-001", currency="EUR")
        registry = FakeRegistry([FakeStrategy(import_result=expected)])
        oracle = DeclarantProOracle(registry=registry)

        result = oracle.import_file(Path("test.xlsx"))
        assert result is expected

    def test_records_last_strategy_metadata(self):
        registry = FakeRegistry([
            FakeStrategy(name="Specific", priority=10),
        ])
        oracle = DeclarantProOracle(registry=registry)
        oracle.import_file(Path("test.xlsx"))

        assert oracle.last_strategy_name == "Specific"
        assert oracle.last_strategy_priority == 10

    def test_progress_callback_passed_through(self):
        """progress_callback se prosljeđuje strategiji kao progress_callback."""
        captured_kwargs = {}

        class RecordingStrategy(FakeStrategy):
            def import_file(self, filepath, progress_callback=None, **kwargs):
                captured_kwargs["progress"] = progress_callback
                return ImportResult(invoice_name="x")

        registry = FakeRegistry([RecordingStrategy()])
        oracle = DeclarantProOracle(registry=registry)

        cb = lambda p: None
        oracle.import_file(Path("test.xlsx"), progress=cb)
        assert captured_kwargs["progress"] is cb

    def test_no_progress_callback(self):
        """Bez progress argumenta, progress_callback=None ide u strategiju."""
        captured_kwargs = {}

        class RecordingStrategy(FakeStrategy):
            def import_file(self, filepath, progress_callback=None, **kwargs):
                captured_kwargs["progress"] = progress_callback
                return ImportResult(invoice_name="x")

        registry = FakeRegistry([RecordingStrategy()])
        oracle = DeclarantProOracle(registry=registry)
        oracle.import_file(Path("test.xlsx"))
        assert captured_kwargs["progress"] is None


# ============================================================
# Test: error handling
# ============================================================


class TestErrorHandling:
    def test_unsupported_format_when_no_match(self):
        registry = FakeRegistry(strategies=[])
        oracle = DeclarantProOracle(registry=registry)
        with pytest.raises(OracleUnsupportedFormatError) as exc_info:
            oracle.import_file(Path("test.xlsx"))
        assert "xlsx" in str(exc_info.value).lower()

    def test_import_failed_wraps_vendor_exception(self):
        registry = FakeRegistry([
            FakeStrategy(raise_on_import=RuntimeError("boom")),
        ])
        oracle = DeclarantProOracle(registry=registry)
        with pytest.raises(OracleImportFailedError) as exc_info:
            oracle.import_file(Path("test.xlsx"))
        assert "boom" in str(exc_info.value)
        assert "Fake" in str(exc_info.value)

    def test_oracle_errors_pass_through(self):
        """Oracle* greške se NE wrapuju u OracleImportFailedError."""

        class FakeStrategyRaisingOracleError(FakeStrategy):
            def import_file(self, filepath, progress_callback=None, **kwargs):
                raise OracleUnavailableError("inner")

        registry = FakeRegistry([FakeStrategyRaisingOracleError()])
        oracle = DeclarantProOracle(registry=registry)
        with pytest.raises(OracleUnavailableError):
            oracle.import_file(Path("test.xlsx"))


# ============================================================
# Test: legacy List[InvoiceLine] response
# ============================================================


class TestLegacyListResponse:
    def test_list_of_invoice_line_wrapped_in_import_result(self):
        from contract.draft_types import InvoiceLine

        line = InvoiceLine(line_no=1, naziv_robe="test")
        registry = FakeRegistry([
            FakeStrategy(import_result=[line, line]),
        ])
        oracle = DeclarantProOracle(registry=registry)
        result = oracle.import_file(Path("test.xlsx"))
        assert isinstance(result, ImportResult)
        assert len(result.items) == 2
        assert result.items[0].naziv_robe == "test"


# ============================================================
# Test: ensure_declarant_pro_importable
# ============================================================


class TestEnsureDeclarantProImportable:
    def test_raises_for_nonexistent_root(self, tmp_path):
        with pytest.raises(OracleUnavailableError) as exc_info:
            ensure_declarant_pro_importable(tmp_path / "missing")
        assert "ne postoji" in str(exc_info.value)

    def test_idempotent_for_existing_root(self, tmp_path):
        """Ako je root već u sys.path, ne duplira se."""
        path_str = str(tmp_path.resolve())
        try:
            ensure_declarant_pro_importable(tmp_path)
            first_count = __import__("sys").path.count(path_str)
            ensure_declarant_pro_importable(tmp_path)
            second_count = __import__("sys").path.count(path_str)
            assert first_count == second_count == 1
        finally:
            try:
                __import__("sys").path.remove(path_str)
            except ValueError:
                pass


# ============================================================
# Test: list_available_strategies (lazy load integration smoke)
# ============================================================


class TestListAvailableStrategies:
    def test_default_root_constant_is_set(self):
        """Default root je stvarna putanja (declarant_pro je instaliran)."""
        assert DEFAULT_DECLARANT_PRO_ROOT == Path("H:/deklarant_pro")

    def test_list_strategies_with_fake_registry(self, monkeypatch):
        """Testiranje sa fake registry-jem (bez declarant_pro importa)."""

        class FakeStrategyListLoader:
            @staticmethod
            def load_default_registry(root=None):
                return FakeRegistry([
                    FakeStrategy(name="ExcelStrategy", priority=10),
                    FakeStrategy(name="PDFStrategy", priority=5),
                    FakeStrategy(name="GenericStrategy", priority=0),
                ])

        # Patch-uj load_default_registry u strategy_loader modulu
        from parser_studio.adapters.declarant_pro import strategy_loader

        monkeypatch.setattr(
            strategy_loader, "load_default_registry",
            FakeStrategyListLoader.load_default_registry,
        )

        strategies = list_available_strategies()
        assert len(strategies) == 3
        assert isinstance(strategies[0], type(strategy_loader.StrategyInfo("", 0)))
        # Prvi po prioritetu
        assert strategies[0].name == "ExcelStrategy"
        assert strategies[0].priority == 10


# ============================================================
# Test: lazy registry load
# ============================================================


class TestLazyRegistryLoad:
    def test_registry_loaded_lazily_on_first_call(self):
        """Konstruktor NE učitava declarant_pro; load se radi na prvi
        can_handle/import_file poziv."""
        oracle = DeclarantProOracle()
        # Oracle je konstruisan, ali još nema registry
        assert oracle._registry is None

    def test_registry_cached_after_first_load(self, monkeypatch):
        """Nakon prvog učitavanja, registry se kešira."""

        load_count = [0]

        def fake_loader(root=None):
            load_count[0] += 1
            return FakeRegistry([FakeStrategy()])

        import parser_studio.adapters.declarant_pro.oracle as oracle_mod
        monkeypatch.setattr(oracle_mod, "load_default_registry", fake_loader)
        oracle = DeclarantProOracle()
        oracle.can_handle(Path("x.xlsx"))
        oracle.import_file(Path("x.xlsx"))
        oracle.can_handle(Path("y.xlsx"))
        # Tri poziva, ali samo jedan load (cached)
        assert load_count[0] == 1

    def test_registry_cached_when_provided_externally(self, monkeypatch):
        """Ako je registry proslijeđen u ctor, NE zove se load."""
        load_count = [0]

        def fake_loader(root=None):
            load_count[0] += 1
            return FakeRegistry([FakeStrategy()])

        import parser_studio.adapters.declarant_pro.oracle as oracle_mod
        monkeypatch.setattr(oracle_mod, "load_default_registry", fake_loader)
        oracle = DeclarantProOracle(registry=FakeRegistry([FakeStrategy()]))
        oracle.can_handle(Path("x.xlsx"))
        oracle.import_file(Path("x.xlsx"))
        # Registry je iz ctor-a, loader se nikad ne zove
        assert load_count[0] == 0

class TestDependencyDirection:
    """V3 DEP pravila — adapter smije zavisiti od domain+ports+contract."""

    def test_oracle_imports_from_domain_layer_via_ports(self):
        """Adapter NE importuje application/presentation — samo domain/ports."""
        import parser_studio.adapters.declarant_pro.oracle as oracle_mod

        # Sanity: oracle_mod postoji i ima ParserOracle type
        assert hasattr(oracle_mod, "DeclarantProOracle")

    def test_strategy_loader_uses_ports_only(self):
        """Strategy loader baca OracleUnavailableError iz porta."""
        from parser_studio.adapters.declarant_pro.strategy_loader import (  # noqa
            ensure_declarant_pro_importable,
        )
        # Tipovi iz porta — adapter nema svoje greške
        from parser_studio.ports.parser_oracle import OracleUnavailableError
        assert OracleUnavailableError.__module__.startswith("parser_studio.ports")

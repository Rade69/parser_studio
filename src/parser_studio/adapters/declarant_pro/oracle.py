# Adapters/deklarant_pro: oracle.
# Posjeduje: DeclarantProOracle implementacija ParserOracle porta.
# Poziva: deklarant_pro StrategyRegistry.import_file() (read-only).
# Vraća: contract.ImportResult (vendorovana kopija).
"""DeclarantProOracle — implementacija ParserOracle porta preko Deklarant
Pro ImportStrategy sistema.

Read-only: NE mjenja deklarant_pro, NE piše u Parser Studio storage.
Samo load-uje strategije i prosljeđuje import_file() poziv.
"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from contract.import_result import ImportResult
from parser_studio.ports.parser_oracle import (
    OracleError,
    OracleImportFailedError,
    OracleUnsupportedFormatError,
)

from .strategy_loader import load_default_registry


class DeclarantProOracle:
    """Adapter koji prevodi ParserOracle pozive u deklarant_pro
    StrategyRegistry.import_file().

    Konstruktor NE učitava deklarant_pro odmah — load se radi lazy na
    prvi import_file() poziv. To omogućava kreiranje instance u test
    okruženjima gdje deklarant_pro nije dostupan (testira se error
    handling bez stvarnog importa).

    Za testiranje sa fake registry-jem: proslijedite `registry` direktno.
    """

    ORACLE_NAME = "declarant_pro"

    def __init__(
        self,
        root: Path | None = None,
        registry=None,
    ) -> None:
        """Init.

        Args:
            root: deklarant_pro root; None = DEFAULT_DECLARANT_PRO_ROOT
                  ili $DECLARANT_PRO_ROOT env var
            registry: opcioni pre-učitani StrategyRegistry (za testiranje);
                     ako dat, root se ignoriše
        """
        self._root = root
        self._registry = registry  # type: ignore[assignment]
        self._last_strategy: str | None = None
        self._last_priority: int | None = None

    def oracle_name(self) -> str:
        return self.ORACLE_NAME

    def can_handle(self, path: Path) -> bool:
        """Brza heuristika: registrovana strategija prihvata ovaj fajl.

        NE parsira fajl, samo can_handle() check. Može baciti
        OracleUnavailableError ako deklarant_pro nije importable.
        """
        registry = self._get_registry()
        return registry.find_strategy(path) is not None

    def import_file(
        self,
        path: Path,
        progress: Callable[[int], None] | None = None,
    ) -> ImportResult:
        """Pozovi deklarant_pro ImportStrategy.import_file().

        Args:
            path: putanja do fakture
            progress: opcioni progress callback (0-100)

        Returns:
            ImportResult (vendorovana kopija)

        Raises:
            OracleUnavailableError: deklarant_pro nije importable
            OracleUnsupportedFormatError: nema strategije za format
            OracleImportFailedError: strategija odabrana ali import pao
        """
        registry = self._get_registry()

        # can_handle provjera prije import_file (lakše poruke o grešci)
        strategy = registry.find_strategy(path)
        if strategy is None:
            raise OracleUnsupportedFormatError(
                f"Nema deklarant_pro strategije za format: "
                f"{path.suffix or '(bez ekstenzije)'}"
            )

        self._last_strategy = strategy.strategy_name
        self._last_priority = strategy.priority

        kwargs: dict = {}
        if progress is not None:
            kwargs["progress_callback"] = progress

        try:
            result = strategy.import_file(path, **kwargs)
        except OracleError:
            # Ne wrapuj — već je Oracle tip
            raise
        except Exception as exc:
            raise OracleImportFailedError(
                f"deklarant_pro import_file() failed "
                f"strategy={strategy.strategy_name}: {exc}"
            ) from exc

        # Deklarant Pro strategije mogu vratiti List[InvoiceLine] (legacy)
        # umjesto ImportResult. Ako je to slučaj, vrati minimalni ImportResult.
        if isinstance(result, ImportResult):
            return result
        if isinstance(result, list):
            # Legacy: vrati listu InvoiceLine u minimalnom ImportResult
            from contract.draft_types import InvoiceLine as IL
            from contract.import_result import ImportResult as IR

            lines = result
            if lines and isinstance(lines[0], IL):
                return IR(items=list(lines))
            # Nepoznat tip — OracleImportFailedError
            raise OracleImportFailedError(
                f"deklarant_pro strategija {strategy.strategy_name} "
                f"vratila neočekivan tip: {type(result).__name__}"
            )

        raise OracleImportFailedError(
            f"deklarant_pro strategija {strategy.strategy_name} "
            f"vratila ImportResult-kompatibilan ali nepozant tip: "
            f"{type(result).__name__}"
        )

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def last_strategy_name(self) -> str | None:
        return self._last_strategy

    @property
    def last_strategy_priority(self) -> int | None:
        return self._last_priority

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _get_registry(self):
        """Lazy load StrategyRegistry ako nije proslijeđen u ctor."""
        if self._registry is not None:
            return self._registry
        if self._root is not None:
            self._registry = load_default_registry(self._root)
        else:
            self._registry = load_default_registry()
        return self._registry
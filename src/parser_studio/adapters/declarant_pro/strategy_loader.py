# Adapters/DEKLARANT_PRO: strategy_loader.
# Helper za učitavanje Deklarant Pro StrategyRegistry i introspekciju strategija.
"""Strategy loader — izolira DEKLARANT_PRO import iza jedne funkcije.

Sva mjesta u Parser Studio kodu koja trebaju DEKLARANT_PRO import
idu kroz load_default_registry() ili list_available_strategies().
Ako DEKLARANT_PRO nije dostupan, OracleUnavailableError se baca.

Testovi mogu proslijediti fake registry umjesto da zovu
load_default_registry().
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import NamedTuple

from parser_studio.ports.parser_oracle import OracleUnavailableError

# Default lokacija DEKLARANT_PRO koda (read-only).
# Može se overridati kroz DEKLARANT_PRO_ROOT env var ili load_default_registry argument.
DEFAULT_DEKLARANT_PRO_ROOT = Path("H:/declarant_pro")


class StrategyInfo(NamedTuple):
    """Introspekcija jedne registrovane strategije."""

    name: str
    priority: int


def ensure_DEKLARANT_PRO_importable(root: Path) -> None:
    """Dodaj DEKLARANT_PRO root u sys.path ako već nije.

    Side-effect: sys.path se mijenja. Ovo je intentionalno — adapter
    JE most, application/ ne vidi DEKLARANT_PRO.

    Raises:
        OracleUnavailableError: ako root ne postoji na disku
    """
    root_str = str(root.resolve())
    if root_str in sys.path:
        return
    if not root.exists():
        raise OracleUnavailableError(
            f"DEKLARANT_PRO root ne postoji na disku: {root}"
        )
    sys.path.insert(0, root_str)


def load_default_registry(
    root: Path | None = None,
):
    """Učitaj DEKLARANT_PRO StrategyRegistry (singleton).

    Registruje default strategije (PDF, Excel, XML) na prvi poziv.
    Vraćeni registry ima import_file() metod.

    Args:
        root: opcioni override za DEKLARANT_PRO root;
              default = DEFAULT_DEKLARANT_PRO_ROOT ili $DEKLARANT_PRO_ROOT env

    Returns:
        StrategyRegistry (DEKLARANT_PRO tip)

    Raises:
        OracleUnavailableError: ako DEKLARANT_PRO nije importable
    """
    if root is None:
        env_root = __import__("os").environ.get("DEKLARANT_PRO_ROOT")
        root = Path(env_root) if env_root else DEFAULT_DEKLARANT_PRO_ROOT

    ensure_DEKLARANT_PRO_importable(root)

    try:
        from importers.strategy_registry import (
            get_registry,  # type: ignore[import-not-found]
        )
    except ImportError as exc:
        raise OracleUnavailableError(
            f"DEKLARANT_PRO moduli nisu importable sa root={root}: {exc}"
        ) from exc

    return get_registry()


def list_available_strategies(
    root: Path | None = None,
) -> list[StrategyInfo]:
    """Introspekcija: listaj sve registrovane strategije.

    Args:
        root: opcioni override za DEKLARANT_PRO root

    Returns:
        Lista StrategyInfo (name, priority), sortirano po priority desc.
    """
    registry = load_default_registry(root)
    return [
        StrategyInfo(name=s.strategy_name, priority=s.priority)
        for s in registry.strategies
    ]
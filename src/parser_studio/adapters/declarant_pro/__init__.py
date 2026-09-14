# Adapters: declarant_pro.
# Posjeduje: DeclarantProOracle adapter za ParserOracle port.
# Zavisnosti: domain/, ports/, contract/ (vendorovana kopija), declarant_pro (read-only runtime).
# Ne zna za: application/, presentation/, sqlite3, PySide6, Docling.
"""Deklarant Pro oracle adapter.

Ovaj adapter JE JEDINI MOST između Parser Studija i declarant_pro/ koda.
Deklarant Pro se tretira kao read-only vendor:

- NE mjenjamo declarant_pro kod
- NE importujemo declarant_pro u application/ (samo u adapteru)
- Ako declarant_pro nije dostupan, OracleUnavailableError

V3 pravilo poštovano: contract/ folder je vendorovana kopija Deklarant
Pro ImportResult/InvoiceLine/Party tipova. Adapter koristi contract tipove
za interface; runtime declarant_pro import je izoliran unutar adaptera.
"""
from __future__ import annotations

from .oracle import DeclarantProOracle
from .strategy_loader import (
    StrategyInfo,
    list_available_strategies,
    load_default_registry,
)

__all__ = [
    "DeclarantProOracle",
    "StrategyInfo",
    "list_available_strategies",
    "load_default_registry",
]
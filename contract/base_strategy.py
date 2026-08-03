"""
VENDOROVANA kopija ugovora iz deklarant_pro/importers/base_strategy.py.

NE UREĐIVATI RUČNO — kopija, ne original.

Docstringovi iz originala su skraćeni (primjeri upotrebe nisu potrebni alatu),
ali SIGNATURE su identične — one su ugovor koji generisani parser mora ispuniti.

Provjera odstupanja: `contract/drift_check.py`.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, List, Optional, Union

from contract.draft_types import InvoiceLine


class ImportStrategy(ABC):
    """Apstraktna baza za sve import strategije."""

    @abstractmethod
    def can_handle(self, filepath: Path) -> bool:
        """Provjeri da li ova strategija može procesirati dati fajl."""

    @abstractmethod
    def import_file(
        self,
        filepath: Path,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> Union[List[InvoiceLine], "ImportResult"]:  # noqa: F821
        """Importuj fajl i vrati normalizovane podatke."""

    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Ime strategije (za logging, debugging i UI prikaz)."""

    @property
    def priority(self) -> int:
        """Prioritet strategije (veći broj = viši prioritet). Default 0.

        Konvencija deklarant_pro: generički = 0, specijalizovani built-in = 10,
        plugin = 20-30 (mora biti VIŠI od built-in da bi pretekao PDFImportStrategy
        / ExcelImportStrategy koje hvataju sve po ekstenziji).
        """
        return 0

    def __str__(self) -> str:
        return f"{self.strategy_name} (priority: {self.priority})"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.strategy_name}>"

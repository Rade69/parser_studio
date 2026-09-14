# Ports: parser_oracle.
# Posjeduje: ParserOracle Protocol + OracleError hijerarhija.
# Ne zna za: konkretne adaptere (DeklarantPro), prezentaciju, SQLite.
"""ParserOracle port.

V3_2 §44 — Oracle bootstrap. Parser Studio pita Oracle da importuje
fakturu koristikuci POSTOJEĆE parsere (npr. Deklarant Pro ImportStrategy).

Oracle je read-only: NE piše u Parser Studio storage, NE mjenja target
dokument, NE mutira stanje. Samo vraća ImportResult (vendorovana kopija
contract tipa) nazad.

Stari parser NIJE automatski istina — D3 (ConfirmOracle) je taj koji
odlucuje da li oracle vrijednost postaje Gold.
"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Protocol, runtime_checkable

from contract.import_result import ImportResult


class OracleError(Exception):
    """Bazna greška za sve Oracle operacije."""


class OracleUnavailableError(OracleError):
    """Oracle adapter ne može da se učita (npr. deklarant_pro nije
    importable, sys.path problem, fali vendor kod)."""


class OracleUnsupportedFormatError(OracleError):
    """Nijedna registrovana strategija ne podržava dati format fajla."""


class OracleImportFailedError(OracleError):
    """Strategija je odabrana, ali import_file() bacio je grešku
    (nevalidan fajl, parserska greška, I/O)."""


@runtime_checkable
class ParserOracle(Protocol):
    """Port za oracle import — čita postojeći vendor parser read-only.

    Implementacije (npr. DeklarantProOracle) pozivaju VENDOR parser
    (npr. ImportStrategy.import_file()) i vraćaju ImportResult (vendorovana
    kopija contract tipa).
    """

    def oracle_name(self) -> str:
        """Identifikator oracle-a (npr. "deklarant_pro"). Koristi se za
        audit, log, UI prikaz."""
        ...

    def can_handle(self, path: Path) -> bool:
        """Da li oracle može da obradi dati fajl. Ne parsira fajl — samo
        provjerava suffix / heuristiku."""
        ...

    def import_file(
        self,
        path: Path,
        progress: Callable[[int], None] | None = None,
    ) -> ImportResult:
        """Pozovi vendor parser i vrati ImportResult.

        Args:
            path: putanja do fakture
            progress: opcioni callback (0-100) za progress reporting

        Returns:
            ImportResult (vendorovana kopija contract.ImportResult)

        Raises:
            OracleUnavailableError: oracle adapter nije dostupan
            OracleUnsupportedFormatError: format nije podržan
            OracleImportFailedError: strategija odabrana ali import pao
        """
        ...
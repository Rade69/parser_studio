# Ports: parser_oracle.
# Posjeduje: ParserOracle Protocol + OracleError hijerarhija.
# Ne zna za: konkretne adaptere (DeclarantPro), prezentaciju, SQLite, contract.
"""ParserOracle port.

V3_2 §44 — Oracle bootstrap. Parser Studio pita Oracle da importuje
fakturu koristeci POSTOJECE parsere (npr. Deklarant Pro ImportStrategy).

Oracle je read-only: NE pise u Parser Studio storage, NE mijenja target
dokument, NE mutira stanje. Samo vraca OraclePayload (vendor-agnosticki
tip u domain/oracle/) nazad u application.

Vendor tip ImportResult (contract/) ostaje UNUTAR adaptera — application
NE smije importovati contract (V3 DEP).

Stari parser NIJE automatski istina — D3 (ConfirmOracle) je taj koji
odlucuje da li oracle vrijednost postaje Gold.
"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from parser_studio.domain.oracle import OraclePayload


class OracleError(Exception):
    """Bazna greska za sve Oracle operacije."""


class OracleUnavailableError(OracleError):
    """Oracle adapter ne moze da se ucita (npr. declarant_pro nije
    importable, sys.path problem, fali vendor kod)."""


class OracleUnsupportedFormatError(OracleError):
    """Nijedna registrovana strategija ne podrzava dati format fajla."""


class OracleImportFailedError(OracleError):
    """Strategija je odabrana, ali import_file() bacio je gresku
    (nevalidan fajl, parserska greska, I/O)."""


@runtime_checkable
class ParserOracle(Protocol):
    """Port za oracle import — cita postojuci vendor parser read-only.

    Implementacije (npr. DeclarantProOracle) pozivaju VENDOR parser
    (npr. ImportStrategy.import_file()) i vracaju OraclePayload
    (vendor-agnosticki tip iz domain/oracle/).

    Contract ImportResult je INTERNI detalj adaptera — NE izlazi iz
    porta. Application radi iskljucivo sa OraclePayload.
    """

    def oracle_name(self) -> str:
        """Identifikator oracle-a (npr. "declarant_pro"). Koristi se za
        audit, log, UI prikaz."""
        ...

    def can_handle(self, path: Path) -> bool:
        """Da li oracle moze da obradi dati fajl. Ne parsira fajl — samo
        provjerava suffix / heuristiku."""
        ...

    def import_file(
        self,
        path: Path,
        progress: Callable[[int], None] | None = None,
    ) -> OraclePayload:
        """Pozovi vendor parser i vrati OraclePayload.

        Args:
            path: putanja do fakture
            progress: opcioni callback (0-100) za progress reporting

        Returns:
            OraclePayload (vendor-agnosticki payload iz domain/oracle/)

        Raises:
            OracleUnavailableError: oracle adapter nije dostupan
            OracleUnsupportedFormatError: format nije podrzan
            OracleImportFailedError: strategija odabrana ali import pao
        """
        ...

    def validate_import(
        self,
        path: Path,
    ) -> tuple[bool, list[str], list[str]]:
        """Validacija importovanog fajla (vendor-agnosticki output).

        Za advanced use case-ove koji trebaju parser-level provjeru
        (npr. M5 Gold corpus verifikacija). Vraća (ok, errors, warnings)
        kao tuple, BEZ vendor tipova u outputu.

        Returns:
            (ok, errors, warnings) — vendor-agnosticki

        Raises:
            OracleUnavailableError: oracle adapter nije dostupan
            OracleImportFailedError: strategija odabrana ali import pao
        """
        ...
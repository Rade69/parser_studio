# Adapters/declarant_pro: oracle.
# Posjeduje: DeclarantProOracle implementacija ParserOracle porta.
# Poziva: declarant_pro StrategyRegistry.import_file() (read-only).
# Vraća: OraclePayload (vendor-agnostički) — ImportResult je INTERNI.
"""DeclarantProOracle — implementacija ParserOracle porta preko Deklarant
Pro ImportStrategy sistema.

Read-only: NE mijenja declarant_pro, NE piše u Parser Studio storage.
Samo load-uje strategije i prosljeđuje import_file() poziv.

Vendor ImportResult (contract/) ostaje INTERNI — javni output je OraclePayload.
"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from contract.import_result import ImportResult
from parser_studio.domain.oracle import OracleItem, OraclePayload
from parser_studio.ports.parser_oracle import (
    OracleError,
    OracleImportFailedError,
    OracleUnsupportedFormatError,
)

from .strategy_loader import load_default_registry


class DeclarantProOracle:
    """Adapter koji prevodi ParserOracle pozive u declarant_pro
    StrategyRegistry.import_file().

    Konstruktor NE učitava declarant_pro odmah — load se radi lazy na
    prvi import_file() poziv. To omogućava kreiranje instance u test
    okruženjima gdje declarant_pro nije dostupan (testira se error
    handling bez stvarnog importa).

    Za testiranje sa fake registry-jem: proslijedite `registry` direktno.
    """

    ORACLE_NAME = "DEKLARANT_PRO"

    def __init__(
        self,
        root: Path | None = None,
        registry=None,
    ) -> None:
        """Init.

        Args:
            root: declarant_pro root; None = DEFAULT_DEKLARANT_PRO_ROOT
                  ili $DEKLARANT_PRO_ROOT env var
            registry: opcioni pre-učitani StrategyRegistry (za testiranje);
                     ako dat, root se ignorise
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
        OracleUnavailableError ako declarant_pro nije importable.
        """
        registry = self._get_registry()
        return registry.find_strategy(path) is not None

    def import_file(
        self,
        path: Path,
        progress: Callable[[int], None] | None = None,
    ) -> OraclePayload:
        """Pozovi declarant_pro ImportStrategy.import_file() i vrati OraclePayload.

        Args:
            path: putanja do fakture
            progress: opcioni progress callback (0-100)

        Returns:
            OraclePayload (vendor-agnostički)

        Raises:
            OracleUnavailableError: declarant_pro nije importable
            OracleUnsupportedFormatError: nema strategije za format
            OracleImportFailedError: strategija odabrana ali import pao
        """
        result = self._invoke_strategy(path, progress)
        return self._build_payload(result)

    def validate_import(
        self,
        path: Path,
    ) -> tuple[bool, list[str], list[str]]:
        """Validacija importovanog fajla (vendor-agnosticki output)."""
        result = self._invoke_strategy(path, progress=None)
        ok, errors, warnings = result.validate(allow_empty=True)
        return ok, errors, warnings

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
        """Lazy load StrategyRegistry ako nije proslijeden u ctor."""
        if self._registry is not None:
            return self._registry
        if self._root is not None:
            self._registry = load_default_registry(self._root)
        else:
            self._registry = load_default_registry()
        return self._registry

    def _invoke_strategy(
        self,
        path: Path,
        progress: Callable[[int], None] | None,
    ) -> ImportResult:
        """Interni: pozovi declarant_pro strategiju i vrati ImportResult.

        Razdvaja I/O dio (koji je exception-prone) od mapping dijela
        (_build_payload). ImportResult ostaje INTERNI.
        """
        registry = self._get_registry()

        strategy = registry.find_strategy(path)
        if strategy is None:
            raise OracleUnsupportedFormatError(
                f"Nema declarant_pro strategije za format: "
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
                f"declarant_pro import_file() failed "
                f"strategy={strategy.strategy_name}: {exc}"
            ) from exc

        # Deklarant Pro strategije mogu vratiti List[InvoiceLine] (legacy)
        # umjesto ImportResult. Normaliziraj u ImportResult.
        if isinstance(result, ImportResult):
            return result
        if isinstance(result, list):
            from contract.draft_types import InvoiceLine as IL

            lines = result
            if lines and isinstance(lines[0], IL):
                return ImportResult(items=list(lines))
            raise OracleImportFailedError(
                f"declarant_pro strategija {strategy.strategy_name} "
                f"vratila neočekivan tip: {type(result).__name__}"
            )

        raise OracleImportFailedError(
            f"declarant_pro strategija {strategy.strategy_name} "
            f"vratila ImportResult-kompatibilan ali nepoznat tip: "
            f"{type(result).__name__}"
        )

    def _build_payload(self, result: ImportResult) -> OraclePayload:
        """Interni: pretvori ImportResult u OraclePayload (vendor-agnostički).

        Ovo je JEDINO mjesto u Parser Studio kodu koje prevodi contract
        tip u domain tip. Adapter smije importovati contract (V3 DEP).
        """
        items = tuple(
            OracleItem(
                line_no=i + 1,
                description=item.naziv_robe,
                quantity=float(item.kolicina),
                unit_price=float(item.cijena_jed),
                line_amount=float(item.iznos),
                hs_code=str(item.tarifni_broj or ""),
                origin_country=item.zemlja_porijekla,
                uom=item.jm,
                gross_weight_kg=float(item.bruto_kg),
                net_weight_kg=float(item.neto_kg),
                product_code=item.product_code,
            )
            for i, item in enumerate(result.items)
        )

        supplier_name = ""
        supplier_address = ""
        supplier_country = ""
        supplier_vat = ""
        if result.exporter is not None:
            supplier_name = result.exporter.name
            supplier_address = result.exporter.address
            supplier_country = result.exporter.country
            supplier_vat = result.exporter.vat_or_id

        return OraclePayload(
            invoice_number=result.invoice_name,
            supplier_name=supplier_name,
            supplier_address=supplier_address,
            supplier_country=supplier_country,
            supplier_vat=supplier_vat,
            invoice_total=float(
                sum(item.iznos for item in result.items)
            ),
            currency=result.currency,
            bruto_kg=float(result.bruto_kg),
            neto_kg=float(result.neto_kg),
            incoterm=result.incoterm_code,
            is_combined=result.is_combined,
            has_origin_statement=result.has_origin_statement,
            items=items,
            source_strategy=self._last_strategy or "",
            source_priority=self._last_priority or 0,
        )
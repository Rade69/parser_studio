# Domain: invoice/vendor_parser_model.
# Posjeduje: VendorParserModel + supporting rule dataclasses/enums.
# Ne zna za: SQLite, PySide6, Docling, openpyxl/xlrd, contract, adapters,
#            presentation, parser_studio runtime.
"""VendorParserModel — declarative model za parsiranje jednog vendora.

V3 sekcija 32 definise VendorParserModel kao domain model u
`domain/parser_model/vendor_parser_model.py` (ciljna struktura). U M1
privremeno se nalazi u `domain/invoice/` radi FAZA B incremental delivery;
po potrebi se kasnije moze prebaciti u `domain/parser_model/`.

Sadrzi:

- vendor identity rules (kako prepoznati vendor dokument)
- layout detection rules
- invoice extraction rules (9 invoice-level polja)
- item table rules (11 item-level polja)
- column roles (heuristicki)
- normalization rules
- validation rules
- fallbacks
- required source files (logicki)
- consumed_paths behavior

Ne sadrzi (V3 sekcija 32):

- slobodan AI Python,
- hardcoded output konkretne fakture,
- Parser Studio runtime pozive.

Sva "ponašanja" su izražena kao:

- ime funkcije (string) — resolver po imenu poziva registriranu funkciju
- parametri (Mapping) — deklarativni parametri za tu funkciju

NE sadrzi inline Python tijela, izvrsavanje koda ili bilo kakav
string-sa-source-kodom mehanizam. Generator (FAZA H/H3) prevodi ove
deklarativne modele u konkretni `.py` fajl.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# Pomocni alias za citljivost; specificira da je svaka vrijednost u params
# serializable (str, int, float, bool, None, tuple, list, dict).
JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | tuple["JsonValue", ...] | list["JsonValue"] | dict[str, "JsonValue"]
ParamsDict = Mapping[str, JsonValue]


class ExtractionStrategy(str, Enum):
    """Strategija ekstrakcije jednog polja (V3 sekcija 9, lista producer-a).

    Svaka strategija je apstraktna oznaka; konkretna implementacija je u
    application/extraction/producers/.
    """

    HEADER_MATCH = "header_match"
    LABEL_RIGHT = "label_right"
    LABEL_BELOW = "label_below"
    TABLE_HEADER = "table_header"
    COLUMN_CONTENT = "column_content"
    VALUE_SHAPE = "value_shape"
    KNOWN_LAYOUT = "known_layout"
    OCR_RECOVERY = "ocr_recovery"
    AI_ADVISOR = "ai_advisor"
    PARSER_ORACLE = "parser_oracle"


class FallbackStrategy(str, Enum):
    """Kako se ponasati kad primarna ekstrakcija jednog polja ne uspije."""

    RAISE_ERROR = "raise_error"
    RETURN_NONE = "return_none"
    USE_DEFAULT = "use_default"
    USE_FALLBACK_PRODUCER = "use_fallback_producer"


class ConsumedPathsBehavior(str, Enum):
    """Kako tretirati `consumed_paths` iz input dokumenta (V3 sekcija 32).

    IGNORE:            ignorisi consumed_paths; nemoj ih ukljucivati u output.
    TRACK_FOR_AUDIT:   prati consumed_paths interno za audit, ali ih ne
                       ukljucuj u finalni output.
    APPEND_TO_OUTPUT:  ukljuci consumed_paths u finalni output (kontekst).
    """

    IGNORE = "ignore"
    TRACK_FOR_AUDIT = "track_for_audit"
    APPEND_TO_OUTPUT = "append_to_output"


def _validate_identifier(value: str, field_name: str) -> None:
    """Validira da je value ne-prazan string i da je validan Python identifier.

    Koristi se za model_id, vendor_id, version, function_name i field_name.
    """
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} mora biti str, dobijeno {type(value).__name__}"
        )
    if not value:
        raise ValueError(f"{field_name} ne moze biti prazan string")
    if not value.isidentifier():
        raise ValueError(
            f"{field_name} mora biti validan Python identifier, dobijeno {value!r}"
        )


def _validate_params(params: ParamsDict | None, owner: str) -> None:
    """Validira da je params Mapping (ili None). Sadrzaj provjerava generator."""
    if params is None:
        return
    if not isinstance(params, Mapping):
        raise TypeError(
            f"{owner}.params mora biti Mapping, dobijeno {type(params).__name__}"
        )


def _validate_rules_dict(
    params: Mapping[str, tuple[Any, ...]] | None,
    owner: str,
    element_type: type,
) -> None:
    """Validira da je params Mapping cija je vrijednost tuple zadanog tipa."""
    if params is None:
        return
    if not isinstance(params, Mapping):
        raise TypeError(
            f"{owner} mora biti Mapping, dobijeno {type(params).__name__}"
        )
    for k in params:
        if not isinstance(k, str):
            raise TypeError(
                f"{owner} kljucevi moraju biti str, dobijeno {type(k).__name__}"
            )
        items = params[k]
        if not isinstance(items, tuple):
            raise TypeError(
                f"{owner}[{k!r}] mora biti tuple {element_type.__name__}-ova, "
                f"dobijeno {type(items).__name__}"
            )
        for i, item in enumerate(items):
            if not isinstance(item, element_type):
                raise TypeError(
                    f"{owner}[{k!r}][{i}] mora biti {element_type.__name__}, "
                    f"dobijeno {type(item).__name__}"
                )


@dataclass(frozen=True, slots=True)
class LayoutRule:
    """Jedno pravilo za detekciju layout-a ili vendor identity.

    Sadrzi SAMO ime funkcije i deklarativne parametre; NE inline Python.
    """

    rule_id: str
    function_name: str
    params: ParamsDict = field(default_factory=dict)
    priority: int = 0

    def __post_init__(self) -> None:
        _validate_identifier(self.rule_id, "rule_id")
        _validate_identifier(self.function_name, "function_name")
        _validate_params(self.params, f"LayoutRule({self.rule_id})")


@dataclass(frozen=True, slots=True)
class FieldExtractionRule:
    """Pravilo za ekstrakciju jednog canonical polja.

    `field_name` je jedno od canonical_invoice_field_names() ili
    canonical_item_field_names(). `strategy` je apstraktna oznaka; konkretni
    producer bira aplikacioni sloj. `params` su deklarativni parametri.
    """

    field_name: str
    strategy: ExtractionStrategy
    function_name: str
    params: ParamsDict = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_identifier(self.field_name, "field_name")
        if not isinstance(self.strategy, ExtractionStrategy):
            raise TypeError(
                f"strategy mora biti ExtractionStrategy instanca, "
                f"dobijeno {type(self.strategy).__name__}"
            )
        _validate_identifier(self.function_name, "function_name")
        _validate_params(self.params, f"FieldExtractionRule({self.field_name})")


@dataclass(frozen=True, slots=True)
class ValidationRule:
    """Jedno validacijsko pravilo (pozvati funkciju sa parametrima).

    Sadrzi SAMO ime funkcije i parametre; NE inline kod.
    """

    function_name: str
    params: ParamsDict = field(default_factory=dict)
    error_message: str | None = None

    def __post_init__(self) -> None:
        _validate_identifier(self.function_name, "function_name")
        _validate_params(self.params, f"ValidationRule({self.function_name})")
        if self.error_message is not None and not isinstance(self.error_message, str):
            raise TypeError(
                f"error_message mora biti str | None, "
                f"dobijeno {type(self.error_message).__name__}"
            )


@dataclass(frozen=True, slots=True)
class NormalizationRule:
    """Jedno normalizacijsko pravilo (NFKC, strip, lowercase, ...).

    Sadrzi SAMO ime funkcije i parametre; NE inline kod.
    """

    function_name: str
    params: ParamsDict = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_identifier(self.function_name, "function_name")
        _validate_params(self.params, f"NormalizationRule({self.function_name})")


@dataclass(frozen=True, slots=True)
class VendorParserModel:
    """Kompletan deklarativni model parsera za jednog vendora.

    Vendor-agnostic u strukturnom smislu: ne sadrzi izvrsivi Python, ne
    hardkodira konkretne fakture, ne poziva parser_studio runtime.

    Sadrzi:
    - identity_rules, layout_rules: kako prepoznati vendor i layout
    - invoice_field_rules, item_field_rules: FieldExtractionRule po polju
    - item_table_rules: LayoutRule za item tablicu
    - column_roles: heuristicke uloge kolona (col_id -> canonical field_name)
    - normalization_rules: per-field tuple NormalizationRule-ova
    - validation_rules: per-field tuple ValidationRule-ova
    - fallback_strategies: per-field FallbackStrategy
    - required_source_files: logicki identifikatori izvornih fajlova
    - consumed_paths_behavior: kako tretirati consumed_paths iz inputa
    """

    model_id: str
    vendor_id: str
    version: int

    identity_rules: tuple[LayoutRule, ...] = field(default_factory=tuple)
    layout_rules: tuple[LayoutRule, ...] = field(default_factory=tuple)

    invoice_field_rules: tuple[FieldExtractionRule, ...] = field(default_factory=tuple)
    item_field_rules: tuple[FieldExtractionRule, ...] = field(default_factory=tuple)

    item_table_rules: tuple[LayoutRule, ...] = field(default_factory=tuple)

    column_roles: Mapping[str, str] = field(default_factory=dict)
    normalization_rules: Mapping[str, tuple[NormalizationRule, ...]] = field(
        default_factory=dict
    )
    validation_rules: Mapping[str, tuple[ValidationRule, ...]] = field(
        default_factory=dict
    )
    fallback_strategies: Mapping[str, FallbackStrategy] = field(default_factory=dict)

    required_source_files: tuple[str, ...] = field(default_factory=tuple)

    consumed_paths_behavior: ConsumedPathsBehavior = ConsumedPathsBehavior.IGNORE

    def __post_init__(self) -> None:
        _validate_identifier(self.model_id, "model_id")
        _validate_identifier(self.vendor_id, "vendor_id")
        if not isinstance(self.version, int):
            raise TypeError(
                f"version mora biti int, dobijeno {type(self.version).__name__}"
            )
        if self.version < 1:
            raise ValueError(f"version mora biti >= 1, dobijeno {self.version}")

        # Validiraj identity_rules i layout_rules
        for r in self.identity_rules:
            if not isinstance(r, LayoutRule):
                raise TypeError(
                    f"identity_rules mora sadrzavati LayoutRule instance, "
                    f"dobijeno {type(r).__name__}"
                )
        for r in self.layout_rules:
            if not isinstance(r, LayoutRule):
                raise TypeError(
                    f"layout_rules mora sadrzavati LayoutRule instance, "
                    f"dobijeno {type(r).__name__}"
                )
        for r in self.item_table_rules:
            if not isinstance(r, LayoutRule):
                raise TypeError(
                    f"item_table_rules mora sadrzavati LayoutRule instance, "
                    f"dobijeno {type(r).__name__}"
                )

        # Validiraj invoice_field_rules i item_field_rules
        for r in self.invoice_field_rules:
            if not isinstance(r, FieldExtractionRule):
                raise TypeError(
                    f"invoice_field_rules mora sadrzavati FieldExtractionRule instance, "
                    f"dobijeno {type(r).__name__}"
                )
        for r in self.item_field_rules:
            if not isinstance(r, FieldExtractionRule):
                raise TypeError(
                    f"item_field_rules mora sadrzavati FieldExtractionRule instance, "
                    f"dobijeno {type(r).__name__}"
                )

        # column_roles: kljucevi i vrijednosti moraju biti str
        if not isinstance(self.column_roles, Mapping):
            raise TypeError(
                f"column_roles mora biti Mapping, dobijeno {type(self.column_roles).__name__}"
            )
        for k, v in self.column_roles.items():
            if not isinstance(k, str):
                raise TypeError(
                    f"column_roles kljucevi moraju biti str, dobijeno {type(k).__name__}"
                )
            if not isinstance(v, str):
                raise TypeError(
                    f"column_roles vrijednosti moraju biti str, dobijeno {type(v).__name__}"
                )

        _validate_rules_dict(
            self.normalization_rules, "normalization_rules", NormalizationRule
        )
        _validate_rules_dict(
            self.validation_rules, "validation_rules", ValidationRule
        )

        # fallback_strategies: kljucevi str, vrijednosti FallbackStrategy
        if not isinstance(self.fallback_strategies, Mapping):
            raise TypeError(
                f"fallback_strategies mora biti Mapping, "
                f"dobijeno {type(self.fallback_strategies).__name__}"
            )
        for k, v in self.fallback_strategies.items():
            if not isinstance(k, str):
                raise TypeError(
                    f"fallback_strategies kljucevi moraju biti str, "
                    f"dobijeno {type(k).__name__}"
                )
            if not isinstance(v, FallbackStrategy):
                raise TypeError(
                    f"fallback_strategies vrijednosti moraju biti FallbackStrategy, "
                    f"dobijeno {type(v).__name__}"
                )

        # required_source_files: tuple str-ova
        if not isinstance(self.required_source_files, tuple):
            raise TypeError(
                f"required_source_files mora biti tuple, "
                f"dobijeno {type(self.required_source_files).__name__}"
            )
        for i, s in enumerate(self.required_source_files):
            if not isinstance(s, str):
                raise TypeError(
                    f"required_source_files[{i}] mora biti str, "
                    f"dobijeno {type(s).__name__}"
                )

        # consumed_paths_behavior
        if not isinstance(self.consumed_paths_behavior, ConsumedPathsBehavior):
            raise TypeError(
                f"consumed_paths_behavior mora biti ConsumedPathsBehavior, "
                f"dobijeno {type(self.consumed_paths_behavior).__name__}"
            )


def rule_count_summary(model: VendorParserModel) -> dict[str, int]:
    """Pomocni pregled broja pravila po kategoriji (za dijagnostiku)."""
    return {
        "identity_rules": len(model.identity_rules),
        "layout_rules": len(model.layout_rules),
        "invoice_field_rules": len(model.invoice_field_rules),
        "item_field_rules": len(model.item_field_rules),
        "item_table_rules": len(model.item_table_rules),
        "column_roles": len(model.column_roles),
        "normalization_fields": len(model.normalization_rules),
        "validation_fields": len(model.validation_rules),
        "fallback_fields": len(model.fallback_strategies),
        "required_source_files": len(model.required_source_files),
    }
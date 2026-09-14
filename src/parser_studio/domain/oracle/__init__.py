# Domain: oracle.
# Posjeduje: OraclePayload (vendor-agnostički payload), OracleFieldMap.
# Ne zna za: contract, SQLite, prezentaciju, adaptere.
"""Oracle domain.

V3_2 §44 — Oracle bootstrap. Vendor-agnostički payload koji
aplikacija koristi bez direktnog importa contract/ tipova.

Adapteri prevode vendor ImportResult u OraclePayload.
"""
from __future__ import annotations

from .oracle_mapping import (
    INVOICE_LEVEL_MAP,
    ITEM_LEVEL_MAP,
    all_supported_fields,
    get_oracle_attr_for,
    is_invoice_field,
    is_item_field,
    is_known_field,
)
from .oracle_payload import OracleItem, OraclePayload

__all__ = [
    "INVOICE_LEVEL_MAP",
    "ITEM_LEVEL_MAP",
    "OracleItem",
    "OraclePayload",
    "all_supported_fields",
    "get_oracle_attr_for",
    "is_invoice_field",
    "is_item_field",
    "is_known_field",
]
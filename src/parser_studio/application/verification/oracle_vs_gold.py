# Application: verification/oracle_vs_gold.
# Posjeduje: OracleVsGoldComparison use case.
# Smije zavisiti samo od: domain, ports.
# NE smije: pisati u storage, mutirati stanje.
"""OracleVsGoldComparison — compare Oracle kandidate sa Gold entries.

V3_2 §44 D3 — Verifikacija FAZA D outputa. Read-only: NE piše u storage,
NE mutira stanje. Samo vraća ComparisonReport.

Use case input:
- oracle_candidates: dict[field, list[Candidate]] — šta Oracle tvrdi
- gold_entries: dict[field, GoldEntry] — šta Gold Dataset čuva (USER_CONFIRMED)

Output:
- ComparisonReport sa aggregate accuracy, per-field accuracy, failed fields.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Any


class ComparisonStatus(str, enum.Enum):
    """Status pojedinog polja u poređenju."""

    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    MISSING_ORACLE = "MISSING_ORACLE"  # Gold ima, Oracle nema
    MISSING_GOLD = "MISSING_GOLD"  # Oracle ima, Gold nema


@dataclass(frozen=True, slots=True)
class FieldComparison:
    """Rezultat poređenja za jedno polje."""

    field: str
    status: ComparisonStatus
    oracle_value: Any
    gold_value: Any

    @property
    def is_correct(self) -> bool:
        return self.status == ComparisonStatus.MATCH


@dataclass(frozen=True, slots=True)
class GoldEntry:
    """Minimal Gold entry za poređenje (USER_CONFIRMED vrijednost)."""

    field: str
    value: Any
    item_id: str | None = None


@dataclass(frozen=True, slots=True)
class ComparisonReport:
    """Aggregate rezultat poređenja Oracle vs Gold."""

    comparisons: tuple[FieldComparison, ...]
    total_fields: int = 0
    matched: int = 0
    mismatched: int = 0
    missing_oracle: int = 0
    missing_gold: int = 0

    @property
    def accuracy(self) -> float:
        if self.total_fields == 0:
            return 0.0
        return self.matched / self.total_fields

    def per_field_accuracy(self) -> dict[str, float]:
        """Vraća accuracy po polju (1.0 za MATCH, 0.0 za sve ostalo)."""
        return {
            c.field: 1.0 if c.is_correct else 0.0
            for c in self.comparisons
        }

    def failed_fields(self) -> tuple[str, ...]:
        """Lista polja koja NISU MATCH."""
        return tuple(
            c.field for c in self.comparisons if not c.is_correct
        )


class OracleVsGoldComparison:
    """Use case: read-only poređenje Oracle outputa sa Gold entries.

    NE piše u storage, NE mutira stanje.
    """

    def compare(
        self,
        oracle_candidates: dict[str, Any],
        gold_entries: dict[str, GoldEntry],
    ) -> ComparisonReport:
        """Poredi Oracle candidate vrijednosti sa Gold entries.

        Args:
            oracle_candidates: dict[field, raw_value] — šta Oracle tvrdi
            gold_entries: dict[field, GoldEntry] — šta Gold čuva

        Returns:
            ComparisonReport sa aggregate i per-field statistikama
        """
        all_fields = set(oracle_candidates.keys()) | set(gold_entries.keys())
        comparisons: list[FieldComparison] = []

        matched = 0
        mismatched = 0
        missing_oracle = 0
        missing_gold = 0

        for fname in sorted(all_fields):
            oracle_val = oracle_candidates.get(fname)
            gold_entry = gold_entries.get(fname)
            gold_val = gold_entry.value if gold_entry else None

            if oracle_val is None and (gold_entry is None or gold_val is None):
                # Oba None (ili oba nemaju vrijednost) — preskoci
                continue
            elif oracle_val is None:
                status = ComparisonStatus.MISSING_ORACLE
                missing_oracle += 1
            elif gold_entry is None or gold_val is None:
                status = ComparisonStatus.MISSING_GOLD
                missing_gold += 1
            elif self._values_equal(oracle_val, gold_val):
                status = ComparisonStatus.MATCH
                matched += 1
            else:
                status = ComparisonStatus.MISMATCH
                mismatched += 1

            comparisons.append(
                FieldComparison(
                    field=fname,
                    status=status,
                    oracle_value=oracle_val,
                    gold_value=gold_val,
                )
            )

        return ComparisonReport(
            comparisons=tuple(comparisons),
            total_fields=len(comparisons),
            matched=matched,
            mismatched=mismatched,
            missing_oracle=missing_oracle,
            missing_gold=missing_gold,
        )

    def _values_equal(self, oracle_val: Any, gold_val: Any) -> bool:
        """Jednostavna equality provjera sa type coercion.

        Oracle i Gold mogu imati različite numeričke tipove (int vs float,
        Decimal vs float). Poredimo sa tolerancijom za brojeve.
        """
        if oracle_val == gold_val:
            return True
        # Numerička tolerancija (0.02 za aritmetiku)
        if isinstance(oracle_val, (int, float)) and isinstance(
            gold_val, (int, float)
        ):
            try:
                return abs(float(oracle_val) - float(gold_val)) < 0.02
            except (TypeError, ValueError):
                return False
        return False
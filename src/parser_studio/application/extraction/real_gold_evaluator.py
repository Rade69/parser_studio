# Application: extraction/real_gold_evaluator.
# Posjeduje: RealGoldEvaluator + EvaluationReport + DocumentEvaluation.
# Zna za: domain.evidence, domain.extraction.
# Ne zna za: SQLite, PySide6, Docling, contract.
"""RealGoldEvaluator (V3_2 §43.5 C5) — mjeri accuracy nad Gold corpusom.

V3_2 C5: "Mjeriti stvarnu accuracy nad Gold corpusom.
         Ne koristiti F10 ili sampled rows kao zamjenu za full extraction accuracy."

Za M3 (FAZA C/C5), evaluator radi SAMO sa compare(expected, resolved) funkcijom.
Pipeline evaluacija (import + analyze + resolve) ostaje za FAZA D/E.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DocumentEvaluation:
    """Evaluacija jednog dokumenta."""

    document_id: str
    field_accuracy: dict[str, float]  # "invoice_number": 1.0, "currency": 0.5, ...
    per_field_matches: dict[str, bool]  # "invoice_number": True, ...
    overall_accuracy: float  # 0.0 - 1.0
    correct_count: int
    total_count: int


@dataclass(frozen=True, slots=True)
class EvaluationReport:
    """Aggregate evaluation report za vise dokumenata."""

    per_document: dict[str, DocumentEvaluation]  # document_id -> result
    aggregate_accuracy: float  # mean(per_document.overall_accuracy)
    field_accuracy: dict[str, float]  # aggregate "field": mean accuracy
    total_correct: int
    total_fields: int
    threshold_pass: bool  # True ako aggregate >= threshold

    @property
    def passed(self) -> bool:
        return self.threshold_pass


class RealGoldEvaluator:
    """Evaluator: compare(expected, resolved) -> EvaluationReport.

    Args:
        threshold: Minimalni aggregate accuracy za PASS (default 0.70 za GATE-3).
        field_weights: Opcionalna dict {field: weight} za weighted accuracy.
    """

    def __init__(
        self,
        threshold: float = 0.70,
        field_weights: dict[str, float] | None = None,
    ) -> None:
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(
                f"threshold mora biti u [0.0, 1.0], dobijeno {threshold}"
            )
        self._threshold = threshold
        self._field_weights = field_weights or {}

    def evaluate_documents(
        self,
        documents: dict[str, tuple[dict[str, str], dict[str, str]]],
    ) -> EvaluationReport:
        """Evaluacija vise dokumenata.

        Args:
            documents: {document_id: (expected_dict, resolved_dict)}.
                expected_dict: {field: gold_value}
                resolved_dict: {field: pipeline_value}

        Returns:
            EvaluationReport sa aggregate + per_document + per_field accuracy.
        """
        per_doc: dict[str, DocumentEvaluation] = {}
        field_correct: dict[str, int] = {}
        field_total: dict[str, int] = {}
        total_correct = 0
        total_fields = 0

        for doc_id, (expected, resolved) in documents.items():
            doc_eval = self._evaluate_one_document(doc_id, expected, resolved)
            per_doc[doc_id] = doc_eval
            total_correct += doc_eval.correct_count
            total_fields += doc_eval.total_count

            for field, matched in doc_eval.per_field_matches.items():
                field_correct[field] = field_correct.get(field, 0) + int(matched)
                field_total[field] = field_total.get(field, 0) + 1

        # Aggregate: prosjecni overall_accuracy
        if per_doc:
            aggregate = sum(d.overall_accuracy for d in per_doc.values()) / len(per_doc)
        else:
            aggregate = 0.0

        # Per-field aggregate
        field_accuracy = {
            field: field_correct[field] / field_total[field]
            for field in field_total
            if field_total[field] > 0
        }

        return EvaluationReport(
            per_document=per_doc,
            aggregate_accuracy=aggregate,
            field_accuracy=field_accuracy,
            total_correct=total_correct,
            total_fields=total_fields,
            threshold_pass=aggregate >= self._threshold,
        )

    def _evaluate_one_document(
        self,
        document_id: str,
        expected: dict[str, str],
        resolved: dict[str, str],
    ) -> DocumentEvaluation:
        """Evaluacija jednog dokumenta."""
        per_field_matches: dict[str, bool] = {}
        correct = 0
        total = len(expected)

        for field, gold_value in expected.items():
            pipeline_value = resolved.get(field)
            # Whitespace-trim i case-insensitive poredjenje
            matched = (
                pipeline_value is not None
                and str(pipeline_value).strip().lower() == str(gold_value).strip().lower()
            )
            per_field_matches[field] = matched
            if matched:
                correct += 1

        field_accuracy = {
            field: (1.0 if matched else 0.0)
            for field, matched in per_field_matches.items()
        }

        overall = correct / total if total > 0 else 0.0

        return DocumentEvaluation(
            document_id=document_id,
            field_accuracy=field_accuracy,
            per_field_matches=per_field_matches,
            overall_accuracy=overall,
            correct_count=correct,
            total_count=total,
        )

    def passes_threshold(self, report: EvaluationReport) -> bool:
        """Da li report prosao threshold."""
        return report.aggregate_accuracy >= self._threshold


__all__ = [
    "DocumentEvaluation",
    "EvaluationReport",
    "RealGoldEvaluator",
]

# Application: oracle_bootstrap/bootstrap.
# Posjeduje: BootstrapOracle use case — orkestrira Oracle + Producer.
# Smije zavisiti samo od: domain, ports.
"""BootstrapOracle — pokreni oracle na fajlu, dohvati OraclePayload, generisi
oracle kandidate kroz OracleCandidateProducer.

Tok:
1. ParserOracle.import_file(path) -> OraclePayload
2. Za svaki poznati field (invoice + item), pozovi OracleCandidateProducer
3. Vrati ExtractionDraft sa oracle kandidatima + OraclePayload + metadata

V3_2 §44 D3 — Python API samo (bez Qt widgeta, FAZA UI paralelno).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from parser_studio.domain.evidence import DocumentEvidence
from parser_studio.domain.extraction.extraction_draft import ExtractionDraft
from parser_studio.domain.oracle import (
    OraclePayload,
    all_supported_fields,
    is_item_field,
)
from parser_studio.ports.candidate_producer import FieldContext
from parser_studio.ports.parser_oracle import ParserOracle


@dataclass(frozen=True, slots=True)
class BootstrapRequest:
    """Input za BootstrapOracle."""

    document_id: str
    document: DocumentEvidence
    path: Path
    language: str = "bs"

    def __post_init__(self) -> None:
        if not self.document_id:
            raise ValueError("document_id ne može biti prazan string")
        if self.path is None:
            raise ValueError("path ne može biti None")


@dataclass(frozen=True, slots=True)
class BootstrapResult:
    """Output iz BootstrapOracle — draft + payload + metadata."""

    draft: ExtractionDraft
    oracle_payload: OraclePayload
    strategy_name: str
    strategy_priority: int
    candidates_by_field: dict[str, int] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()


class BootstrapOracle:
    """Use case: orkestrira ParserOracle + OracleCandidateProducer.

    Args:
        oracle: ParserOracle port (adapter se ubrizgava u composition root)
    """

    def __init__(
        self,
        oracle: ParserOracle,
        producer_factory: Any = None,
    ) -> None:
        """Init.

        Args:
            oracle: ParserOracle port
            producer_factory: opcioni factory za OracleCandidateProducer
                (default: kreira novu instancu svaki put)
        """
        self._oracle = oracle
        if producer_factory is None:
            from parser_studio.application.extraction.producers.oracle import (
                OracleCandidateProducer,
            )
            producer_factory = OracleCandidateProducer
        self._producer_factory = producer_factory

    def execute(self, request: BootstrapRequest) -> BootstrapResult:
        """Bootstrap oracle extraction za dati dokument.

        Args:
            request: BootstrapRequest sa document_id, document, path

        Returns:
            BootstrapResult sa ExtractionDraft + OraclePayload + metadata

        Raises:
            OracleError: ako oracle.import_file() baci (propagira se)
        """
        # 1. Oracle import — vendor-agnosticki OraclePayload
        oracle_payload = self._oracle.import_file(request.path)

        # 2. Kreiraj producer sa oracle_payload u context
        producer = self._producer_factory()

        # 3. Za svaki poznati field, dohvati oracle kandidate
        candidates_by_field: dict[str, tuple] = {}
        counts: dict[str, int] = {}
        warnings: list[str] = []

        for field_name in all_supported_fields():
            # Za item-level, probaj za svaku stavku u payload-u
            if is_item_field(field_name):
                if not oracle_payload.items:
                    continue
                for item in oracle_payload.items:
                    ctx = FieldContext(
                        document_id=request.document_id,
                        field=field_name,
                        language=request.language,
                        line_no=item.line_no,
                        oracle_payload=oracle_payload,
                    )
                    candidates = producer.propose(request.document, ctx)
                    if candidates:
                        candidates_by_field.setdefault(
                            f"{field_name}.line_{item.line_no}", ()
                        )
                        candidates_by_field[f"{field_name}.line_{item.line_no}"] += tuple(
                            candidates
                        )
                        counts[f"{field_name}.line_{item.line_no}"] = len(candidates)
            else:
                # Invoice-level
                ctx = FieldContext(
                    document_id=request.document_id,
                    field=field_name,
                    language=request.language,
                    oracle_payload=oracle_payload,
                )
                candidates = producer.propose(request.document, ctx)
                if candidates:
                    candidates_by_field[field_name] = tuple(candidates)
                    counts[field_name] = len(candidates)

        if oracle_payload.is_empty():
            warnings.append("oracle_payload je prazan — nema vrijednosti za potvrdu")

        # 4. Kreiraj ExtractionDraft
        draft = ExtractionDraft(
            document_id=request.document_id,
            document=request.document,
            candidates_by_field=candidates_by_field,
            unresolved=tuple(
                f for f in all_supported_fields() if f not in candidates_by_field
            ),
            warnings=tuple(warnings),
        )

        # 5. Introspekcija
        strategy_name = oracle_payload.source_strategy or self._oracle.oracle_name()
        strategy_priority = oracle_payload.source_priority

        return BootstrapResult(
            draft=draft,
            oracle_payload=oracle_payload,
            strategy_name=strategy_name,
            strategy_priority=strategy_priority,
            candidates_by_field=counts,
            warnings=tuple(warnings),
        )
# Application: OracleCandidateProducer.
# Posjeduje: implementacija CandidateProducer porta za Oracle output.
# Smije zavisiti samo od: domain, ports.
# NE smije zavisiti od: adapters, presentation, contract.
"""OracleCandidateProducer — pretvara OraclePayload vrijednosti u Candidate.

V3_2 §44 — Oracle bootstrap (D2). Za svaki target field, oracle producer
predlaže 1 Candidate sa:
- raw_value: oracle vrijednost
- normalized_value: ista vrijednost (Oracle već normalizuje)
- producer_id: "oracle"
- confidence: 0.95 (visok — Oracle je "stari parser koji zna")
- evidence: strategija koja je proizvela vrijednost

D3 (ConfirmOracle) je taj koji odlučuje da li oracle vrijednost postaje
Gold — Oracle NIJE automatski istina (V3 §23).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from parser_studio.domain.evidence import Candidate, Locator
from parser_studio.domain.oracle import (
    get_oracle_attr_for,
    is_item_field,
)
from parser_studio.ports.candidate_producer import (
    FieldContext,
)

if TYPE_CHECKING:
    from parser_studio.domain.evidence import DocumentEvidence


class OracleCandidateProducer:
    """Producer koji mapira OraclePayload vrijednosti na Candidate.

    Za invoice-level polja (invoice_number, currency, supplier_*...):
    čita iz OraclePayload.<field> direktno.

    Za item-level polja (quantity, line_amount...): čita iz
    OraclePayload.items[line_no].<field> ako je line_no dat u context.

    Ako oracle_payload NIJE dat u context, producer NE predlaže
    kandidate (supports() vraća False).
    """

    producer_id: str = "oracle"

    def supports(self, context: FieldContext) -> bool:
        """Producer je aktivan samo ako je oracle_payload prisutan
        i field je poznat u oracle mapi."""
        if context.oracle_payload is None:
            return False
        if context.oracle_payload.is_empty():
            return False
        return get_oracle_attr_for(context.field) is not None

    def propose(
        self,
        document: DocumentEvidence,
        context: FieldContext,
    ) -> list[Candidate]:
        """Propose 1 oracle kandidat za traženo polje.

        Returns:
            Lista sa 0 ili 1 kandidatom. Ako oracle_payload nema
            vrijednost za traženo polje, vraća [].
        """
        if not self.supports(context):
            return []

        oracle_attr = get_oracle_attr_for(context.field)
        if oracle_attr is None:
            return []

        # Invoice-level polje
        if not is_item_field(context.field):
            raw_value = getattr(context.oracle_payload, oracle_attr, None)
        else:
            # Item-level — trebamo line_no
            if context.line_no is None:
                return []
            raw_value = context.oracle_payload.get_item_field(
                context.line_no, oracle_attr
            )

        if raw_value is None or raw_value == "" or raw_value == 0.0:
            return []

        locator = self._build_locator(document, context)
        evidence_str = self._build_evidence(context)

        candidate = Candidate(
            field=context.field,
            raw_value=raw_value,
            normalized_value=raw_value,  # Oracle već normalizuje
            locator=locator,
            evidence=evidence_str,
            producer_id=self.producer_id,
            ai_assisted=False,
            issues=(),
        )
        return [candidate]

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _build_locator(
        self,
        document: DocumentEvidence,
        context: FieldContext,
    ) -> Locator:
        """Konstruiši Locator za oracle kandidata.

        Oracle NE daje preciznu lokaciju (za razliku od C2 producer-a koji
        čita ćelije). Koristimo source_path + kind bez koordinata.
        D3 confirm/reject može dodati precizniju lokaciju ako korisnik
        specificira.
        """
        return Locator(
            source_path=document.source_path if document else "oracle",
            kind="text",  # Oracle je tekst-based, ne excel/pdf layout
        )

    def _build_evidence(self, context: FieldContext) -> str:
        """Konstruiši evidence string za audit."""
        oracle = context.oracle_payload
        if oracle is None:
            return f"oracle(producer={self.producer_id})"
        return (
            f"oracle(strategy={oracle.source_strategy}, "
            f"priority={oracle.source_priority})"
        )
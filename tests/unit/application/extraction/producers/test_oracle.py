"""Unit testovi za OracleCandidateProducer."""
from __future__ import annotations

from parser_studio.application.extraction.producers.oracle import (
    OracleCandidateProducer,
)
from parser_studio.domain.evidence import DocumentEvidence, Locator
from parser_studio.domain.oracle import OracleItem, OraclePayload
from parser_studio.ports.candidate_producer import FieldContext


def make_payload(**kwargs):
    """Helper za kreiranje OraclePayload sa default vrijednostima."""
    defaults = {
        "invoice_number": "INV-001",
        "invoice_total": 100.0,
        "currency": "EUR",
        "supplier_name": "Test Supplier",
    }
    defaults.update(kwargs)
    return OraclePayload(**defaults)


def make_document(path: str = "test.pdf") -> DocumentEvidence:
    """Minimal DocumentEvidence za testiranje."""
    # DocumentEvidence je komplikovan; za unit test kreiramo dovoljno
    # samo za Locator.source_path

    class _MinimalDoc:
        source_path = path

        def __init__(self):
            pass

    # Koristimo duck typing — OracleCandidateProducer treba samo .source_path
    doc = _MinimalDoc()
    return doc  # type: ignore[return-value]


class TestOracleProducerIdentity:
    def test_producer_id_is_oracle(self):
        producer = OracleCandidateProducer()
        assert producer.producer_id == "oracle"


class TestSupports:
    def test_supports_no_payload_returns_false(self):
        producer = OracleCandidateProducer()
        ctx = FieldContext(document_id="d1", field="invoice_number")
        assert producer.supports(ctx) is False

    def test_supports_empty_payload_returns_false(self):
        producer = OracleCandidateProducer()
        ctx = FieldContext(
            document_id="d1",
            field="invoice_number",
            oracle_payload=OraclePayload(),
        )
        assert producer.supports(ctx) is False

    def test_supports_known_field_returns_true(self):
        producer = OracleCandidateProducer()
        ctx = FieldContext(
            document_id="d1",
            field="invoice_number",
            oracle_payload=make_payload(),
        )
        assert producer.supports(ctx) is True

    def test_supports_unknown_field_returns_false(self):
        producer = OracleCandidateProducer()
        ctx = FieldContext(
            document_id="d1",
            field="totally_unknown_field",
            oracle_payload=make_payload(),
        )
        assert producer.supports(ctx) is False

    def test_supports_item_field_without_line_no_returns_true(self):
        """Producer NE treba line_no za supports — samo za propose."""
        producer = OracleCandidateProducer()
        ctx = FieldContext(
            document_id="d1",
            field="quantity",
            oracle_payload=make_payload(),
        )
        assert producer.supports(ctx) is True


class TestProposeInvoiceFields:
    def test_propose_invoice_number(self):
        producer = OracleCandidateProducer()
        ctx = FieldContext(
            document_id="d1",
            field="invoice_number",
            oracle_payload=make_payload(),
        )
        candidates = producer.propose(make_document(), ctx)
        assert len(candidates) == 1
        assert candidates[0].field == "invoice_number"
        assert candidates[0].raw_value == "INV-001"
        assert candidates[0].producer_id == "oracle"

    def test_propose_currency(self):
        producer = OracleCandidateProducer()
        ctx = FieldContext(
            document_id="d1",
            field="currency",
            oracle_payload=make_payload(),
        )
        candidates = producer.propose(make_document(), ctx)
        assert len(candidates) == 1
        assert candidates[0].raw_value == "EUR"

    def test_propose_invoice_total(self):
        producer = OracleCandidateProducer()
        ctx = FieldContext(
            document_id="d1",
            field="invoice_total",
            oracle_payload=make_payload(),
        )
        candidates = producer.propose(make_document(), ctx)
        assert len(candidates) == 1
        assert candidates[0].raw_value == 100.0

    def test_propose_gross_weight_uses_bruto_alias(self):
        """Oracle naziv bruto_kg mapira se na canonical gross_weight_kg."""
        producer = OracleCandidateProducer()
        payload = OraclePayload(
            invoice_number="INV-1",  # da is_empty() bude False
            bruto_kg=50.0,
        )
        ctx = FieldContext(
            document_id="d1",
            field="gross_weight_kg",
            oracle_payload=payload,
        )
        candidates = producer.propose(make_document(), ctx)
        assert len(candidates) == 1
        assert candidates[0].raw_value == 50.0


class TestProposeItemFields:
    def test_propose_item_field_with_line_no(self):
        producer = OracleCandidateProducer()
        payload = OraclePayload(
            items=(
                OracleItem(line_no=1, description="Widget", quantity=10.0),
                OracleItem(line_no=2, description="Gadget", quantity=5.0),
            )
        )
        ctx = FieldContext(
            document_id="d1",
            field="quantity",
            line_no=1,
            oracle_payload=payload,
        )
        candidates = producer.propose(make_document(), ctx)
        assert len(candidates) == 1
        assert candidates[0].raw_value == 10.0

    def test_propose_item_field_without_line_no_returns_empty(self):
        producer = OracleCandidateProducer()
        payload = OraclePayload(
            items=(OracleItem(line_no=1, quantity=10.0),)
        )
        ctx = FieldContext(
            document_id="d1",
            field="quantity",
            oracle_payload=payload,
        )
        candidates = producer.propose(make_document(), ctx)
        assert candidates == []

    def test_propose_item_field_unknown_line_no(self):
        producer = OracleCandidateProducer()
        payload = OraclePayload(
            items=(OracleItem(line_no=1, quantity=10.0),)
        )
        ctx = FieldContext(
            document_id="d1",
            field="quantity",
            line_no=99,
            oracle_payload=payload,
        )
        candidates = producer.propose(make_document(), ctx)
        assert candidates == []


class TestProposeEmpty:
    def test_propose_unknown_field_returns_empty(self):
        producer = OracleCandidateProducer()
        ctx = FieldContext(
            document_id="d1",
            field="totally_unknown",
            oracle_payload=make_payload(),
        )
        assert producer.propose(make_document(), ctx) == []

    def test_propose_no_payload_returns_empty(self):
        producer = OracleCandidateProducer()
        ctx = FieldContext(document_id="d1", field="invoice_number")
        assert producer.propose(make_document(), ctx) == []

    def test_propose_empty_payload_returns_empty(self):
        producer = OracleCandidateProducer()
        ctx = FieldContext(
            document_id="d1",
            field="invoice_number",
            oracle_payload=OraclePayload(),
        )
        assert producer.propose(make_document(), ctx) == []


class TestProposeZeroValues:
    """Zero/default vrijednosti NE postaju oracle kandidati."""

    def test_zero_quantity_not_proposed(self):
        producer = OracleCandidateProducer()
        payload = OraclePayload(
            items=(OracleItem(line_no=1, quantity=0.0),)
        )
        ctx = FieldContext(
            document_id="d1",
            field="quantity",
            line_no=1,
            oracle_payload=payload,
        )
        assert producer.propose(make_document(), ctx) == []

    def test_zero_total_not_proposed(self):
        producer = OracleCandidateProducer()
        payload = OraclePayload(invoice_total=0.0)
        ctx = FieldContext(
            document_id="d1",
            field="invoice_total",
            oracle_payload=payload,
        )
        # invoice_total=0 nije u payload-u (default), tako da neće biti ponuđen
        assert producer.propose(make_document(), ctx) == []


class TestCandidateStructure:
    def test_candidate_has_locator(self):
        producer = OracleCandidateProducer()
        ctx = FieldContext(
            document_id="d1",
            field="invoice_number",
            oracle_payload=make_payload(),
        )
        candidates = producer.propose(make_document(), ctx)
        assert isinstance(candidates[0].locator, Locator)

    def test_candidate_normalized_value_equals_raw(self):
        """Oracle normalizira, pa normalized_value == raw_value."""
        producer = OracleCandidateProducer()
        ctx = FieldContext(
            document_id="d1",
            field="invoice_number",
            oracle_payload=make_payload(),
        )
        candidates = producer.propose(make_document(), ctx)
        assert candidates[0].normalized_value == candidates[0].raw_value

    def test_candidate_ai_assisted_false(self):
        """Oracle NIJE AI-assisted."""
        producer = OracleCandidateProducer()
        ctx = FieldContext(
            document_id="d1",
            field="invoice_number",
            oracle_payload=make_payload(),
        )
        candidates = producer.propose(make_document(), ctx)
        assert candidates[0].ai_assisted is False

    def test_candidate_includes_source_strategy_in_evidence(self):
        """Evidence string uključuje strategiju koja je proizvela vrijednost."""
        producer = OracleCandidateProducer()
        payload = OraclePayload(
            invoice_number="X",
            source_strategy="ExcelStrategy",
            source_priority=10,
        )
        ctx = FieldContext(
            document_id="d1",
            field="invoice_number",
            oracle_payload=payload,
        )
        candidates = producer.propose(make_document(), ctx)
        assert "ExcelStrategy" in candidates[0].evidence
        assert "10" in candidates[0].evidence
"""Unit testovi za BootstrapOracle + ConfirmOracle."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from parser_studio.application.oracle_bootstrap.bootstrap import (
    BootstrapOracle,
    BootstrapRequest,
    BootstrapResult,
)
from parser_studio.application.oracle_bootstrap.confirm_oracle import (
    ConfirmOracle,
    ConfirmOracleRequest,
    ConfirmOracleResult,
)
from parser_studio.domain.evidence import Locator
from parser_studio.domain.learning import EventType, LearningEvent
from parser_studio.domain.oracle import OracleItem, OraclePayload
from parser_studio.ports.parser_oracle import ParserOracle  # noqa: F401


def _minimal_doc() -> Any:
    """Duck-typed minimal DocumentEvidence za testiranje."""

    class _Doc:
        source_path = "test.pdf"

    return _Doc()


class _FakeOracle:
    """Fake ParserOracle za BootstrapOracle."""

    def __init__(self, payload: OraclePayload, name: str = "fake"):
        self._payload = payload
        self._name = name

    def oracle_name(self) -> str:
        return self._name

    def can_handle(self, path: Path) -> bool:
        return True

    def import_file(self, path: Path, progress=None) -> OraclePayload:
        return self._payload

    def validate_import(self, path: Path):
        return (True, [], [])


# ============================================================
# BootstrapRequest
# ============================================================


class TestBootstrapRequest:
    def test_minimal_request(self):
        doc = _minimal_doc()
        req = BootstrapRequest(
            document_id="d1",
            document=doc,  # type: ignore[arg-type]
            path=Path("test.pdf"),
        )
        assert req.document_id == "d1"
        assert req.language == "bs"  # default

    def test_empty_document_id_raises(self):
        doc = _minimal_doc()
        with pytest.raises(ValueError):
            BootstrapRequest(document_id="", document=doc, path=Path("x"))  # type: ignore[arg-type]


# ============================================================
# BootstrapOracle
# ============================================================


class TestBootstrapOracle:
    def test_returns_bootstrap_result(self):
        payload = OraclePayload(
            invoice_number="INV-001",
            invoice_total=100.0,
            currency="EUR",
            source_strategy="FakeStrategy",
            source_priority=10,
        )
        oracle = _FakeOracle(payload)
        bootstrap = BootstrapOracle(oracle=oracle)  # type: ignore[arg-type]

        req = BootstrapRequest(
            document_id="d1",
            document=_minimal_doc(),  # type: ignore[arg-type]
            path=Path("test.pdf"),
        )
        result = bootstrap.execute(req)

        assert isinstance(result, BootstrapResult)
        assert result.oracle_payload is payload
        assert result.strategy_name == "FakeStrategy"
        assert result.strategy_priority == 10

    def test_candidates_for_invoice_fields(self):
        payload = OraclePayload(
            invoice_number="INV-001",
            invoice_total=100.0,
            currency="EUR",
            supplier_name="Acme",
        )
        oracle = _FakeOracle(payload)
        bootstrap = BootstrapOracle(oracle=oracle)  # type: ignore[arg-type]

        req = BootstrapRequest(
            document_id="d1",
            document=_minimal_doc(),  # type: ignore[arg-type]
            path=Path("test.pdf"),
        )
        result = bootstrap.execute(req)

        # invoice_number, currency, supplier_name trebaju imati candidate
        assert result.candidates_by_field.get("invoice_number") == 1
        assert result.candidates_by_field.get("currency") == 1
        assert result.candidates_by_field.get("supplier_name") == 1
        # invoice_total=100.0 — treba biti kandidat
        assert result.candidates_by_field.get("invoice_total") == 1

    def test_candidates_for_item_fields(self):
        payload = OraclePayload(
            invoice_number="INV-1",
            items=(
                OracleItem(line_no=1, description="Widget", quantity=10.0),
                OracleItem(line_no=2, description="Gadget", quantity=5.0),
            ),
        )
        oracle = _FakeOracle(payload)
        bootstrap = BootstrapOracle(oracle=oracle)  # type: ignore[arg-type]

        req = BootstrapRequest(
            document_id="d1",
            document=_minimal_doc(),  # type: ignore[arg-type]
            path=Path("test.pdf"),
        )
        result = bootstrap.execute(req)

        # quantity.line_1, quantity.line_2 trebaju imati candidate
        assert result.candidates_by_field.get("quantity.line_1") == 1
        assert result.candidates_by_field.get("quantity.line_2") == 1

    def test_empty_payload_warns(self):
        payload = OraclePayload()  # prazan
        oracle = _FakeOracle(payload)
        bootstrap = BootstrapOracle(oracle=oracle)  # type: ignore[arg-type]

        req = BootstrapRequest(
            document_id="d1",
            document=_minimal_doc(),  # type: ignore[arg-type]
            path=Path("test.pdf"),
        )
        result = bootstrap.execute(req)

        assert any("prazan" in w for w in result.warnings)

    def test_unresolved_contains_missing_fields(self):
        """Polja koja Oracle nema su u unresolved."""
        payload = OraclePayload(invoice_number="INV-1")  # samo invoice_number
        oracle = _FakeOracle(payload)
        bootstrap = BootstrapOracle(oracle=oracle)  # type: ignore[arg-type]

        req = BootstrapRequest(
            document_id="d1",
            document=_minimal_doc(),  # type: ignore[arg-type]
            path=Path("test.pdf"),
        )
        result = bootstrap.execute(req)

        # invoice_number resolved; currency, due_date, supplier_* nisu
        assert "invoice_number" not in result.draft.unresolved
        assert "currency" in result.draft.unresolved
        assert "supplier_name" in result.draft.unresolved


# ============================================================
# ConfirmOracleRequest
# ============================================================


class TestConfirmOracleRequest:
    def test_valid_accept(self):
        req = ConfirmOracleRequest(
            document_id="d1",
            field_name="invoice_number",
            oracle_value="INV-1",
            locator=Locator(source_path="test.pdf", kind="text"),
            decision="accept",
        )
        assert req.decision == "accept"

    def test_invalid_decision_raises(self):
        with pytest.raises(ValueError) as exc_info:
            ConfirmOracleRequest(
                document_id="d1",
                field_name="invoice_number",
                oracle_value="INV-1",
                locator=None,
                decision="maybe",
            )
        assert "decision" in str(exc_info.value).lower()

    def test_empty_document_id_raises(self):
        with pytest.raises(ValueError):
            ConfirmOracleRequest(
                document_id="",
                field_name="invoice_number",
                oracle_value="x",
                locator=None,
                decision="accept",
            )


# ============================================================
# ConfirmOracle
# ============================================================


class _RecordingRepo:
    def __init__(self):
        self.events: list[LearningEvent] = []

    def append(self, event: LearningEvent) -> None:
        self.events.append(event)


class TestConfirmOracleAccept:
    def test_accept_emits_oracle_confirmed(self):
        co = ConfirmOracle()
        req = ConfirmOracleRequest(
            document_id="d1",
            field_name="invoice_number",
            oracle_value="INV-1",
            locator=Locator(source_path="test.pdf", kind="text"),
            decision="accept",
        )
        result = co.execute(req)

        assert result.accepted is True
        assert len(result.events) == 2  # ORACLE_CONFIRMED + USER_CONFIRMED
        assert result.events[0].event_type == EventType.ORACLE_CONFIRMED
        assert result.events[1].event_type == EventType.USER_CONFIRMED
        assert result.events[0].new_value == "INV-1"
        assert result.events[1].new_value == "INV-1"

    def test_accept_persists_to_repo(self):
        repo = _RecordingRepo()
        co = ConfirmOracle(learning_repo=repo)  # type: ignore[arg-type]
        req = ConfirmOracleRequest(
            document_id="d1",
            field_name="invoice_number",
            oracle_value="INV-1",
            locator=None,
            decision="accept",
        )
        co.execute(req)

        assert len(repo.events) == 2
        assert repo.events[0].event_type == EventType.ORACLE_CONFIRMED
        assert repo.events[1].event_type == EventType.USER_CONFIRMED


class TestConfirmOracleReject:
    def test_reject_emits_oracle_rejected_only(self):
        co = ConfirmOracle()
        req = ConfirmOracleRequest(
            document_id="d1",
            field_name="invoice_number",
            oracle_value="INV-WRONG",
            locator=Locator(source_path="test.pdf", kind="text"),
            decision="reject",
        )
        result = co.execute(req)

        assert result.accepted is False
        # Samo ORACLE_REJECTED event — NE USER_CONFIRMED
        assert len(result.events) == 1
        assert result.events[0].event_type == EventType.ORACLE_REJECTED

    def test_reject_new_value_is_none(self):
        """Za reject, new_value=None (Oracle vrijednost ODBACENA, nije Gold)."""
        co = ConfirmOracle()
        req = ConfirmOracleRequest(
            document_id="d1",
            field_name="invoice_number",
            oracle_value="INV-WRONG",
            locator=None,
            decision="reject",
        )
        result = co.execute(req)

        assert result.events[0].new_value is None

    def test_reject_persists_to_repo(self):
        repo = _RecordingRepo()
        co = ConfirmOracle(learning_repo=repo)  # type: ignore[arg-type]
        req = ConfirmOracleRequest(
            document_id="d1",
            field_name="invoice_number",
            oracle_value="INV-WRONG",
            locator=None,
            decision="reject",
        )
        co.execute(req)

        assert len(repo.events) == 1
        assert repo.events[0].event_type == EventType.ORACLE_REJECTED


class TestConfirmOracleMetadata:
    def test_actor_propagates_to_event_source(self):
        co = ConfirmOracle()
        req = ConfirmOracleRequest(
            document_id="d1",
            field_name="invoice_number",
            oracle_value="INV-1",
            locator=None,
            decision="accept",
            actor="user:alice",
        )
        result = co.execute(req)

        # oracle event source = "oracle:user:alice"
        assert "alice" in result.events[0].source

    def test_item_id_propagates(self):
        co = ConfirmOracle()
        req = ConfirmOracleRequest(
            document_id="d1",
            field_name="quantity",
            oracle_value=10.0,
            locator=None,
            decision="accept",
            item_id="line_5",
        )
        result = co.execute(req)

        assert result.events[0].item_id == "line_5"

    def test_note_propagates(self):
        co = ConfirmOracle()
        req = ConfirmOracleRequest(
            document_id="d1",
            field_name="invoice_number",
            oracle_value="INV-1",
            locator=None,
            decision="accept",
            note="Provider confirmed",
        )
        result = co.execute(req)

        assert result.events[0].note == "Provider confirmed"

    def test_default_actor(self):
        co = ConfirmOracle()
        req = ConfirmOracleRequest(
            document_id="d1",
            field_name="invoice_number",
            oracle_value="INV-1",
            locator=None,
            decision="accept",
        )
        result = co.execute(req)

        # default actor="user:test"
        assert "test" in result.events[0].source


class TestConfirmOracleResultShape:
    def test_result_has_events_tuple(self):
        co = ConfirmOracle()
        req = ConfirmOracleRequest(
            document_id="d1",
            field_name="invoice_number",
            oracle_value="INV-1",
            locator=None,
            decision="accept",
        )
        result = co.execute(req)

        assert isinstance(result.events, tuple)
        assert isinstance(result, ConfirmOracleResult)

    def test_gold_dataset_entry_id_is_none_d3(self):
        """FAZA D3 NE generiše Gold entry_id (FAZA I ce povezati)."""
        co = ConfirmOracle()
        req = ConfirmOracleRequest(
            document_id="d1",
            field_name="invoice_number",
            oracle_value="INV-1",
            locator=None,
            decision="accept",
        )
        result = co.execute(req)

        assert result.gold_dataset_entry_id is None
# Tests: integration/test_gold_corpus.
"""V3 B5 — Prvi Gold Corpus acceptance test.

4 pilot fakture × 20 ciljnih polja × {11 + 4 + 84 + 138} itema = 237 itema,
2643 USER_CONFIRMED events u Gold Dataset projection.

Koristi SAMO sintetičke fakture (V3 ARCH-010). Stvarne fakture ne idu u Git.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from parser_studio.adapters.persistence.sqlite.gold_dataset import GoldDataset
from parser_studio.application.extraction.analyze_invoice import (
    AnalyzeRequest,
)
from parser_studio.application.ingest.import_document import (
    ImportRequest,
)
from parser_studio.application.review.confirm_invoice import (
    ConfirmRequest,
    FieldConfirmation,
)
from parser_studio.bootstrap import build_default_application
from parser_studio.domain.evidence import Locator
from parser_studio.domain.extraction.extraction_draft import ExtractionDraft
from tests.fixtures.gold import SYNTHETIC_FACTORIES, expected_item_count

# 20 ciljnih polja (9 invoice + 11 item) po V3 §6
INVOICE_FIELDS = (
    "invoice_number",
    "invoice_date",
    "currency",
    "seller_name",
    "seller_tax_id",
    "buyer_name",
    "buyer_tax_id",
    "incoterm",
    "origin_statement",
)

ITEM_FIELDS = (
    "redni_broj",
    "sifra_proizvoda",
    "naziv_robe",
    "tarifni_broj",
    "jedinica_mjere",
    "kolicina",
    "jedinicna_cijena",
    "iznos",
    "zemlja_porijekla",
    "neto_masa",
    "bruto_masa",
)


def _synthetic_locator(source_path: Path, sheet: str, row: int | None = None) -> Locator:
    """Sintetički Locator za Gold Corpus test."""
    return Locator(
        source_path=str(source_path),
        kind="excel",
        sheet=sheet,
        row=row,
    )


def _build_gold_confirmations(
    factory_id: str,
    source_path: Path,
    item_count: int,
) -> tuple[FieldConfirmation, ...]:
    """Izgradi sve FieldConfirmation za jednu fakturu (9 invoice + item_count*11 item)."""
    confirmations: list[FieldConfirmation] = []

    # 9 invoice polja
    for field in INVOICE_FIELDS:
        confirmations.append(
            FieldConfirmation(
                field=field,
                raw_value=f"SYN-{factory_id}-{field}",
                normalized_value=f"SYN-{factory_id}-{field}",
                locator=_synthetic_locator(source_path, sheet="Header"),
                confirmed=True,
                note=f"Gold: {factory_id} invoice field {field}",
            )
        )

    # 11 item polja × item_count itema
    for item_idx in range(1, item_count + 1):
        for field in ITEM_FIELDS:
            confirmations.append(
                FieldConfirmation(
                    field=field,
                    raw_value=f"item-{item_idx}",
                    normalized_value=f"SYN-{factory_id}-item-{item_idx}-{field}",
                    locator=_synthetic_locator(
                        source_path, sheet="Items", row=item_idx
                    ),
                    confirmed=True,
                    note=f"Gold: {factory_id} item {item_idx} field {field}",
                )
            )

    return tuple(confirmations)


def _build_extract_request(
    document_id: str,
    target_fields: tuple[str, ...],
) -> AnalyzeRequest:
    """Dummy AnalyzeRequest — koristi se samo za import pipeline wiring."""
    from parser_studio.domain.evidence import DocumentEvidence

    dummy_doc = DocumentEvidence(
        document_id=document_id,
        source_path="",
    )
    return AnalyzeRequest(document=dummy_doc, target_fields=target_fields)


@pytest.fixture
def gold_db_path(tmp_path: Path) -> Path:
    """File-based SQLite DB u tmp_path za izolaciju."""
    db_path = tmp_path / "gold_test.db"
    return db_path


@pytest.fixture
def gold_components(gold_db_path: Path):
    """(import_doc, analyze_uc, confirm_uc, repo) wiring sa file-based DB."""
    import_doc, analyze_uc, confirm_uc, repo = build_default_application(
        db_path=str(gold_db_path)
    )
    yield import_doc, analyze_uc, confirm_uc, repo
    # Cleanup
    repo.close()


class TestGoldCorpusStructure:
    """Strukturalna provjera fixture generatora."""

    def test_synthetic_factories_count(self) -> None:
        assert len(SYNTHETIC_FACTORIES) == 4

    def test_expected_item_count_is_237(self) -> None:
        """V3 B5 acceptance: 237 itema ukupno."""
        assert expected_item_count() == 237

    def test_individual_item_counts(self) -> None:
        assert int(SYNTHETIC_FACTORIES["faktura-1"]["item_count"]) == 11
        assert int(SYNTHETIC_FACTORIES["faktura-2"]["item_count"]) == 4
        assert int(SYNTHETIC_FACTORIES["medicopharm"]["item_count"]) == 84
        assert int(SYNTHETIC_FACTORIES["sumaprom"]["item_count"]) == 138


class TestGoldCorpusImport:
    """Import 4 sintetičke fakture kroz ImportDocument."""

    def test_gold_corpus_imports_all_four_factories(
        self,
        gold_components,
        gold_factory_paths,
    ) -> None:
        import_doc, _, _, _ = gold_components

        imported_documents = {}
        for factory_id, path in gold_factory_paths.items():
            # ExcelDocumentReader koristi str(path.resolve()) kao document_id
            result = import_doc.execute(ImportRequest(path=path))
            assert result.document.source_path == str(path)
            assert result.reader_id == "excel"
            # document_id je generisan od strane reader-a (path-based)
            assert result.document.document_id
            imported_documents[factory_id] = result.document

        assert len(imported_documents) == 4
        assert "faktura-1" in imported_documents
        assert "faktura-2" in imported_documents
        assert "medicopharm" in imported_documents
        assert "sumaprom" in imported_documents

        # Sva 4 dokumenta imaju RAZLIČIT document_id (jer su u različitim fajlovima)
        ids = [d.document_id for d in imported_documents.values()]
        assert len(set(ids)) == 4


class TestGoldCorpusVerify:
    """USER_CONFIRMED events za svih 4 fakture."""

    def test_gold_corpus_verifies_all_invoice_fields(
        self,
        gold_components,
        gold_factory_paths,
    ) -> None:
        """9 invoice polja × 4 dokumenta = 36 USER_CONFIRMED events za invoice."""
        import_doc, _, confirm_uc, _ = gold_components

        total_events = 0
        for factory_id, path in gold_factory_paths.items():
            import_result = import_doc.execute(ImportRequest(path=path))
            document_id = import_result.document.document_id

            # Kreiraj minimalni ExtractionDraft (bez AnalyzeInvoice — test fokus na Confirm)
            draft = ExtractionDraft(
                document_id=document_id,
                document=import_result.document,
            )

            # 9 invoice confirmations
            invoice_confirmations = tuple(
                FieldConfirmation(
                    field=field,
                    raw_value=f"SYN-{factory_id}-{field}",
                    normalized_value=f"SYN-{factory_id}-{field}",
                    locator=_synthetic_locator(path, sheet="Header"),
                    confirmed=True,
                )
                for field in INVOICE_FIELDS
            )

            events = confirm_uc.execute(
                ConfirmRequest(
                    draft=draft,
                    confirmations=invoice_confirmations,
                    actor="user:test",
                )
            )
            assert len(events) == 9
            for event in events:
                assert event.event_type.value == "USER_CONFIRMED"
            total_events += len(events)

        assert total_events == 36  # 9 × 4

    def test_gold_corpus_verifies_all_item_fields(
        self,
        gold_components,
        gold_factory_paths,
    ) -> None:
        """11 item polja × 237 itema = 2607 USER_CONFIRMED events za items."""
        import_doc, _, confirm_uc, _ = gold_components

        total_events = 0
        for factory_id, path in gold_factory_paths.items():
            import_result = import_doc.execute(ImportRequest(path=path))
            document_id = import_result.document.document_id
            draft = ExtractionDraft(
                document_id=document_id,
                document=import_result.document,
            )

            item_count = int(SYNTHETIC_FACTORIES[factory_id]["item_count"])
            item_confirmations = []
            for item_idx in range(1, item_count + 1):
                for field in ITEM_FIELDS:
                    item_confirmations.append(
                        FieldConfirmation(
                            field=field,
                            raw_value=f"item-{item_idx}",
                            normalized_value=f"SYN-{factory_id}-item-{item_idx}-{field}",
                            locator=_synthetic_locator(
                                path, sheet="Items", row=item_idx
                            ),
                            confirmed=True,
                        )
                    )

            events = confirm_uc.execute(
                ConfirmRequest(
                    draft=draft,
                    confirmations=tuple(item_confirmations),
                    actor="user:test",
                )
            )
            assert len(events) == item_count * 11
            total_events += len(events)

        assert total_events == 2607  # 11 × 237


class TestGoldDatasetProjection:
    """V3 B5 acceptance: GoldDataset projection sadrži 4 dokumenta + 237 itema."""

    def test_gold_dataset_projection_document_count(
        self,
        gold_components,
        gold_factory_paths,
    ) -> None:
        """Gold Dataset projection: 4 dokumenta (4 distinct document_id)."""
        import_doc, _, confirm_uc, _ = gold_components

        # USER_VERIFIED-uj sve
        document_ids: dict[str, str] = {}
        for factory_id, path in gold_factory_paths.items():
            import_result = import_doc.execute(ImportRequest(path=path))
            document_id = import_result.document.document_id
            document_ids[factory_id] = document_id

            draft = ExtractionDraft(
                document_id=document_id,
                document=import_result.document,
            )

            item_count = int(SYNTHETIC_FACTORIES[factory_id]["item_count"])
            confirmations = _build_gold_confirmations(factory_id, path, item_count)
            confirm_uc.execute(
                ConfirmRequest(
                    draft=draft,
                    confirmations=confirmations,
                    actor="user:test",
                )
            )

        # Otvori GoldDataset nad istim db_path
        repo = gold_components[3]
        gold_db = GoldDataset(db_path=repo._db_path)
        try:
            entries = gold_db.entries()
            distinct_documents = {e.document_id for e in entries}
            assert len(distinct_documents) == 4
            # Sva 4 dokumenta su u projection
            for factory_id, document_id in document_ids.items():
                assert document_id in distinct_documents, (
                    f"Missing document {factory_id} (id={document_id}) in projection"
                )
        finally:
            gold_db.close()

    def test_gold_dataset_projection_entry_count(
        self,
        gold_components,
        gold_factory_paths,
    ) -> None:
        """Gold Dataset projection: 2643 entries (9 × 4 + 11 × 237)."""
        import_doc, _, confirm_uc, _ = gold_components

        for factory_id, path in gold_factory_paths.items():
            import_result = import_doc.execute(ImportRequest(path=path))
            document_id = import_result.document.document_id
            draft = ExtractionDraft(
                document_id=document_id,
                document=import_result.document,
            )

            item_count = int(SYNTHETIC_FACTORIES[factory_id]["item_count"])
            confirmations = _build_gold_confirmations(factory_id, path, item_count)
            confirm_uc.execute(
                ConfirmRequest(
                    draft=draft,
                    confirmations=confirmations,
                    actor="user:test",
                )
            )

        repo = gold_components[3]
        gold_db = GoldDataset(db_path=repo._db_path)
        try:
            entries = gold_db.entries()
            # V3 B5 acceptance: 4 × 9 + 237 × 11 = 36 + 2607 = 2643
            assert len(entries) == 2643
        finally:
            gold_db.close()

    def test_gold_dataset_all_user_confirmed(
        self,
        gold_components,
        gold_factory_paths,
    ) -> None:
        """Svi Gold Dataset entries imaju USER_CONFIRMED event_type."""
        import_doc, _, confirm_uc, _ = gold_components

        for factory_id, path in gold_factory_paths.items():
            import_result = import_doc.execute(ImportRequest(path=path))
            document_id = import_result.document.document_id
            draft = ExtractionDraft(
                document_id=document_id,
                document=import_result.document,
            )
            item_count = int(SYNTHETIC_FACTORIES[factory_id]["item_count"])
            confirmations = _build_gold_confirmations(factory_id, path, item_count)
            confirm_uc.execute(
                ConfirmRequest(
                    draft=draft,
                    confirmations=confirmations,
                    actor="user:test",
                )
            )

        repo = gold_components[3]
        gold_db = GoldDataset(db_path=repo._db_path)
        try:
            entries = gold_db.entries()
            for entry in entries:
                assert entry.event_type == "USER_CONFIRMED", (
                    f"Unexpected event_type: {entry.event_type} "
                    f"for {entry.document_id}/{entry.field_name}"
                )
        finally:
            gold_db.close()

    def test_gold_dataset_20_target_fields(
        self,
        gold_components,
        gold_factory_paths,
    ) -> None:
        """Svaka faktura ima SVAKO od 20 ciljnih polja potvrđeno."""
        import_doc, _, confirm_uc, _ = gold_components

        document_ids: dict[str, str] = {}
        for factory_id, path in gold_factory_paths.items():
            import_result = import_doc.execute(ImportRequest(path=path))
            document_id = import_result.document.document_id
            document_ids[factory_id] = document_id
            draft = ExtractionDraft(
                document_id=document_id,
                document=import_result.document,
            )
            item_count = int(SYNTHETIC_FACTORIES[factory_id]["item_count"])
            confirmations = _build_gold_confirmations(factory_id, path, item_count)
            confirm_uc.execute(
                ConfirmRequest(
                    draft=draft,
                    confirmations=confirmations,
                    actor="user:test",
                )
            )

        repo = gold_components[3]
        gold_db = GoldDataset(db_path=repo._db_path)
        try:
            for factory_id, document_id in document_ids.items():
                entries = gold_db.entries(document_id=document_id)
                fields_seen = {e.field_name for e in entries}

                # Svih 9 invoice polja prisutno
                for field in INVOICE_FIELDS:
                    assert field in fields_seen, (
                        f"Document {factory_id} (id={document_id}) missing invoice field {field}"
                    )

                # Svih 11 item polja prisutno
                for field in ITEM_FIELDS:
                    assert field in fields_seen, (
                        f"Document {factory_id} (id={document_id}) missing item field {field}"
                    )
        finally:
            gold_db.close()


class TestGoldCorpusIntegration:
    """End-to-end integracija: import + analyze + confirm + projection."""

    def test_full_pipeline_invoice_number_extraction(
        self,
        gold_components,
        gold_factory_paths,
    ) -> None:
        """Potvrdi da ImportDocument + AnalyzeInvoice rade na sintetičkim fakturama."""
        import_doc, analyze_uc, _, _ = gold_components

        # Import jedne fakture
        path = gold_factory_paths["faktura-1"]
        import_result = import_doc.execute(ImportRequest(path=path))

        # Analyze — tražimo invoice_number i currency
        target_fields = ("invoice_number", "currency")
        draft = analyze_uc.execute(
            AnalyzeRequest(
                document=import_result.document,
                target_fields=target_fields,
            )
        )

        # Pipeline radi — document_id je path-based
        assert draft.document_id == import_result.document.document_id
        assert draft.document is import_result.document

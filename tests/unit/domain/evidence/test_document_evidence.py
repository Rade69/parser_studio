# Tests: DocumentEvidence.
from __future__ import annotations

import pytest

from parser_studio.domain.evidence import DocumentEvidence, Evidence, Locator


def _make_evidence(text: str = "x") -> Evidence:
    return Evidence(
        raw_value=text,
        raw_text=text,
        locator=Locator(source_path="f.pdf", kind="pdf"),
        element_type="text",
    )


class TestDocumentEvidenceConstruction:
    def test_minimum_v3_fields(self) -> None:
        doc = DocumentEvidence(
            document_id="doc-001",
            source_path="file.pdf",
        )
        assert doc.document_id == "doc-001"
        assert doc.source_path == "file.pdf"
        assert doc.pages == []
        assert doc.text_elements == []
        assert doc.tables == []
        assert doc.cells == []
        assert doc.page_dimensions is None
        assert doc.metadata is None

    def test_with_collections(self) -> None:
        ev1 = _make_evidence("a")
        ev2 = _make_evidence("b")
        doc = DocumentEvidence(
            document_id="doc-002",
            source_path="file.xlsx",
            pages=["page1", "page2"],
            text_elements=[ev1, ev2],
            cells=[ev1, ev2],
            page_dimensions={1: (800.0, 600.0)},
            metadata={"author": "test"},
        )
        assert len(doc.text_elements) == 2
        assert len(doc.cells) == 2
        assert doc.page_dimensions == {1: (800.0, 600.0)}
        assert doc.metadata == {"author": "test"}


class TestDocumentEvidenceFrozen:
    def test_mutation_raises(self) -> None:
        doc = DocumentEvidence(document_id="d", source_path="f.pdf")
        with pytest.raises((AttributeError, Exception)):
            doc.document_id = "other"  # type: ignore[misc]


class TestDocumentEvidenceValidation:
    def test_empty_document_id_raises(self) -> None:
        with pytest.raises(ValueError, match="document_id"):
            DocumentEvidence(document_id="", source_path="f.pdf")

    def test_empty_source_path_raises(self) -> None:
        with pytest.raises(ValueError, match="source_path"):
            DocumentEvidence(document_id="d", source_path="")

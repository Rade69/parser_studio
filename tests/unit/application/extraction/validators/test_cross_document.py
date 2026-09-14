# Tests: application/extraction/validators/test_cross_document.
"""Testovi za CrossDocumentValidator (V3_2 C4 cross-document — PLACEHOLDER za FAZA D)."""
from __future__ import annotations

from parser_studio.application.extraction.validators import (
    CrossDocumentValidator,
    IssueSeverity,
)
from parser_studio.domain.evidence import DocumentEvidence
from parser_studio.domain.extraction.extraction_draft import ExtractionDraft


class TestCrossDocumentValidator:
    def test_placeholder_info_issue(self) -> None:
        """Vraća INFO Issue o FAZA D-u (placeholder)."""
        draft = ExtractionDraft(
            document_id="doc-1",
            document=DocumentEvidence(document_id="doc-1", source_path="/test.xlsx"),
        )
        issues = CrossDocumentValidator().validate(draft)
        assert len(issues) == 1
        assert issues[0].severity == IssueSeverity.INFO
        assert issues[0].code == "CD001"
        assert "FAZA D" in issues[0].message

    def test_validator_name(self) -> None:
        assert CrossDocumentValidator().name == "cross_document"

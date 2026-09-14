# Tests: ExtractionContext.
from __future__ import annotations

import pytest

from parser_studio.domain.evidence import ExtractionContext


class TestExtractionContextConstruction:
    def test_minimum(self) -> None:
        ctx = ExtractionContext(document_id="doc-1")
        assert ctx.document_id == "doc-1"
        assert ctx.language == "bs"
        assert ctx.target_fields == ()
        assert ctx.profile_version is None
        assert ctx.producer_id is None

    def test_full(self) -> None:
        ctx = ExtractionContext(
            document_id="doc-1",
            language="en",
            target_fields=("quantity", "unit_price", "line_amount"),
            profile_version=2,
            producer_id="analyzer_v2",
        )
        assert ctx.language == "en"
        assert ctx.target_fields == ("quantity", "unit_price", "line_amount")
        assert ctx.profile_version == 2
        assert ctx.producer_id == "analyzer_v2"


class TestExtractionContextFrozen:
    def test_mutation_raises(self) -> None:
        ctx = ExtractionContext(document_id="d")
        with pytest.raises((AttributeError, Exception)):
            ctx.language = "en"  # type: ignore[misc]


class TestExtractionContextValidation:
    def test_empty_document_id_raises(self) -> None:
        with pytest.raises(ValueError, match="document_id"):
            ExtractionContext(document_id="")

    def test_empty_language_raises(self) -> None:
        with pytest.raises(ValueError, match="language"):
            ExtractionContext(document_id="d", language="")

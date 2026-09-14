# Tests: integration/conftest.
"""Shared pytest fixtures za integration testove."""
from __future__ import annotations

from pathlib import Path

import pytest

from parser_studio.bootstrap import build_default_application
from tests.fixtures.gold import generate_all_synthetic_factories


@pytest.fixture
def gold_factory_dir(tmp_path: Path) -> Path:
    """Generiši 4 sintetičke fakture u tmp_path."""
    output_dir = tmp_path / "gold"
    output_dir.mkdir()
    paths = generate_all_synthetic_factories(output_dir)
    assert len(paths) == 4
    for path in paths.values():
        assert path.exists()
        assert path.stat().st_size > 0
    return output_dir


@pytest.fixture
def gold_factory_paths(gold_factory_dir: Path) -> dict[str, Path]:
    """Vrati dict {factory_id: path} za 4 sintetičke fakture."""
    return {
        factory_id: gold_factory_dir / f"{factory_id}.xlsx"
        for factory_id in ["faktura-1", "faktura-2", "medicopharm", "sumaprom"]
    }


@pytest.fixture
def gold_app_components():
    """Vrati (import_doc, analyze_uc, confirm_uc, repo) wiring."""
    import_doc, analyze_uc, confirm_uc, repo = build_default_application(
        db_path=":memory:"
    )
    return import_doc, analyze_uc, confirm_uc, repo

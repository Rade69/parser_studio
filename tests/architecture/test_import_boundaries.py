# Tests: architecture/test_import_boundaries.
# Provjera V3 DEP-001..DEP-005 import granica preko AST analize.
"""Architecture tests — provjera import granica prema V3 DEP-001..DEP-005.

Koristi AST za analizu import statements u Python fajlovima.
Pravila:
- domain/ NE SMIJE importovati adapters, presentation, sqlite3, openpyxl, xlrd, docling, contract
- application/ NE SMIJE importovati adapters, presentation, sqlite3, openpyxl, xlrd, docling, contract
- ports/ NE SMIJE importovati adapters, presentation, sqlite3, openpyxl, xlrd, docling
- presentation/ NE SMIJE importovati sqlite3, openpyxl, xlrd, docling, adapters.persistence.sqlite
"""
from __future__ import annotations

import ast
from pathlib import Path

FORBIDDEN_IMPORTS_BY_LAYER: dict[str, set[str]] = {
    "domain": {
        "parser_studio.adapters",
        "parser_studio.presentation",
        "sqlite3",
        "openpyxl",
        "xlrd",
        "docling",
        "contract",
    },
    "application": {
        "parser_studio.adapters",
        "parser_studio.presentation",
        "sqlite3",
        "openpyxl",
        "xlrd",
        "docling",
        "contract",
    },
    "ports": {
        "parser_studio.adapters",
        "parser_studio.presentation",
        "sqlite3",
        "openpyxl",
        "xlrd",
        "docling",
    },
    "presentation": {
        "sqlite3",
        "openpyxl",
        "xlrd",
        "docling",
        "parser_studio.adapters.persistence.sqlite",
    },
}


def _get_top_level_modules_from_file(file_path: Path) -> set[str]:
    """Vrati top-level module imena iz Python fajla."""
    source = file_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                # Top-level ime (prvi dio do .)
                top = alias.name.split(".")[0]
                modules.add(top)
                # Takodjer dodaj puni prefiks za dublje provjere
                if alias.name.startswith("parser_studio."):
                    modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            top = node.module.split(".")[0]
            modules.add(top)
            if node.module.startswith("parser_studio."):
                modules.add(node.module)
    return modules


def _get_layer(file_path: Path) -> str | None:
    """Vrati layer (domain/application/ports/presentation) za fajl."""
    path_str = str(file_path).replace("\\", "/")
    if "/src/parser_studio/domain/" in path_str:
        return "domain"
    if "/src/parser_studio/application/" in path_str:
        return "application"
    if "/src/parser_studio/ports/" in path_str:
        return "ports"
    if "/src/parser_studio/presentation/" in path_str:
        return "presentation"
    return None


def _collect_violations(layer: str, forbidden: set[str]) -> list[tuple[str, set[str]]]:
    """Sakuplja violations za dati layer."""
    root = Path(f"src/parser_studio/{layer}")
    if not root.exists():
        return []
    violations: list[tuple[str, set[str]]] = []
    for py_file in root.rglob("*.py"):
        imports = _get_top_level_modules_from_file(py_file)
        bad = imports & forbidden
        if bad:
            violations.append((str(py_file), bad))
    return violations


def test_domain_layer_clean() -> None:
    """domain/ NE SMIJE importovati forbidden module (V3 DEP-001)."""
    forbidden = FORBIDDEN_IMPORTS_BY_LAYER["domain"]
    violations = _collect_violations("domain", forbidden)
    assert violations == [], f"domain violations: {violations}"


def test_application_layer_clean() -> None:
    """application/ NE SMIJE importovati forbidden module (V3 DEP-002)."""
    forbidden = FORBIDDEN_IMPORTS_BY_LAYER["application"]
    violations = _collect_violations("application", forbidden)
    assert violations == [], f"application violations: {violations}"


def test_ports_layer_clean() -> None:
    """ports/ NE SMIJE importovati forbidden module (V3 DEP-003)."""
    forbidden = FORBIDDEN_IMPORTS_BY_LAYER["ports"]
    violations = _collect_violations("ports", forbidden)
    assert violations == [], f"ports violations: {violations}"


def test_presentation_layer_clean() -> None:
    """presentation/ NE SMIJE importovati sqlite3/openpyxl/xlrd/docling (V3 DEP-004)."""
    forbidden = FORBIDDEN_IMPORTS_BY_LAYER["presentation"]
    violations = _collect_violations("presentation", forbidden)
    assert violations == [], f"presentation violations: {violations}"

---
task_id: A7
title: "Presentation migracija + cleanup legacy strukture + architecture tests + pyproject.toml cleanup"
status: ACTIVE
risk: MEDIUM-HIGH
date: 2026-09-14
branch: dev (base)
worktree: TBD
---

# A7 — Presentation migracija + cleanup

> Migrirati `cli/`, `services/`, `viewmodels/`, `views/` u `src/parser_studio/presentation/` (Qt/CLI). Obriši legacy direktorijume poslije migracije. Dodati architecture tests + cleanup `pyproject.toml`.

---

## Roles

```text
Human Owner:    <tvoj unos>
Coordinator:    Claude Code
Implementer:    <tvoj unos>
Reviewer:       <tvoj unos — nezavisni>
```

---

## Canonical references

```text
docs/PLAN.md                                  (V3, sekcija 18: presentation/qt/; sekcija 18: presentation/cli/; sekcija 41: A7; sekcija 56: "sta se trenutno NE radi")
.agent/PROJECT_MAP.md                         (sekcija C: MIGRATION MAP; sekcija D: BOUNDARIES)
.agent/TASK_ROUTING.md                        (sekcija "Review / PySide6")
core/documents/, core/engines/                (legacy, NETAKNUT u A7 — vidi napomenu ispod)
cli/psbuild.py                                (legacy CLI entry point — MIGRIRATI)
views/, viewmodels/, services/                (legacy prazni — MIGRIRATI ili BRISATI)
src/parser_studio/bootstrap.py                (A5: composition root)
src/parser_studio/application/                (A5: use case-ovi)
src/parser_studio/ports/                      (A3, A4: DocumentReader, CandidateProducer)
agent_reports/2026-09-14-graft-evaluation.md  (Graft SECONDARY pravila)
```

---

## Current-state preconditions

```text
[ ] branch: dev na a86cc59 (A6 docs)
[ ] A6 acceptance DONE — LearningRepository + SQLite adapter
[ ] A5 acceptance DONE — Application use case-ovi
[ ] A4 acceptance DONE — CandidateProducer Protocol
[ ] A3 acceptance DONE — DocumentReader port
[ ] A2 acceptance DONE — Evidence domain
[ ] A1 acceptance DONE — src/parser_studio/ skelet
[ ] Graft status: SECONDARY (probacioni period)
[ ] baseline testovi: 330 PASS + 1 FAIL (test_f9 pre-existing)
[ ] ruff: 192 errors
[ ] contract drift: PASS
[ ] DEKLARANT_PRO_ROOT: H:/deklarant_pro
```

A7 može krenuti.

---

## Problem

V3 sekcija 41 A7:
- "Presentation migration + cleanup"
- Zadaci: migrirati services/views/viewmodels/cli u presentation/
- Acceptance: Postojeći CLI radi, Qt entry point se kreira

Trenutno stanje:

**Legacy prazni/placeholder:**
- `cli/psbuild.py` — minimalan CLI entry point (legacy)
- `views/` — prazno + `views/wizard/` (zastario)
- `viewmodels/` — prazno
- `services/` — prazno

**A6 arhitektura:**
- `src/parser_studio/presentation/` — PRAZAN (samo `__init__.py`)
- `src/parser_studio/presentation/qt/` — PRAZAN
- `src/parser_studio/presentation/cli/` — PRAZAN

**pyproject.toml:**
- Entry point: `psbuild = "cli.psbuild:main"` (legacy)
- Description: "Learning-first alat za izradu i verifikaciju parsera faktura za Deklarant Pro" (vec A1)
- `cryptography>=41.0` u dependencies — V3 kaže "ukloniti ili u optional[signing]"

**Architecture tests:**
- NEMA `tests/architecture/` — V3 kaže "Architecture testovi su autoritet za granice"

---

## Goal

1. Migrirati `cli/psbuild.py` → `src/parser_studio/presentation/cli/psbuild.py`
2. Migrirati `views/wizard/` (prazno) → `src/parser_studio/presentation/qt/wizard/` (prazno, sa deprecation notice)
3. Migrirati `viewmodels/` → `src/parser_studio/presentation/qt/viewmodels/` (prazno, placeholder za Qt modele)
4. Migrirati `services/` → `src/parser_studio/application/` (vec tamo, samo obrisati legacy `services/`)
5. Ažurirati `pyproject.toml` entry point na `parser_studio.presentation.cli.psbuild:main`
6. Obriši legacy `cli/`, `services/`, `viewmodels/`, `views/` (ili ostavi prazne + deprecation notice)
7. Dodati `tests/architecture/test_import_boundaries.py`
8. pyproject.toml cleanup: `cryptography` van (ili u optional[signing]), description update

Acceptance:
- CLI entry point radi (psbuild komanda dostupna)
- `src/parser_studio/presentation/` ima `qt/` i `cli/` sa novim fajlovima
- Legacy `cli/`, `services/`, `viewmodels/`, `views/` obrisani (ili deprecation notice)
- Architecture tests PASS za sve import granice
- pytest ista ili bolja statistika
- ruff ne značajno gore
- contract drift PASS
- 8+ unit testova (CLI + architecture)

---

## In scope

### Novi fajlovi

```text
src/parser_studio/presentation/cli/
    __init__.py
    psbuild.py          # CLI entry point (migriran iz cli/psbuild.py)

src/parser_studio/presentation/qt/
    __init__.py
    viewmodels/
        __init__.py
        review_invoice_viewmodel.py    # placeholder, MVVM pattern
    widgets/
        __init__.py
    wizard/
        __init__.py

tests/unit/presentation/
    __init__.py
    cli/
        __init__.py
        test_psbuild.py
    qt/
        __init__.py
        test_viewmodels.py

tests/architecture/
    __init__.py
    test_import_boundaries.py    # AST provjera import granica
```

### Izmjene

```text
pyproject.toml:
- Entry point: psbuild = "parser_studio.presentation.cli.psbuild:main"
- Description: "Learning-first alat za izradu i verifikaciju parsera faktura za Deklarant Pro" (vec OK)
- cryptography: premjestiti u [project.optional-dependencies] signing, ILI ukloniti
```

### Brisanje (cleanup)

```text
cli/psbuild.py                  # legacy CLI; premješten u presentation/cli/psbuild.py
cli/__init__.py                 # prazan
services/__init__.py            # prazan
viewmodels/__init__.py          # prazan
views/__init__.py               # prazan
views/widgets/__init__.py       # prazan
views/wizard/__init__.py        # prazan
```

ALI — brisanje je destruktivno. Za MVP, koristim **deprecation strategy**:
- Legacy `cli/psbuild.py` ostaje ali baca `DeprecationWarning` i importuje iz nove putanje
- Legacy `services/`, `viewmodels/`, `views/` ostaju prazni
- Ili: obrisati legacy jer su prazni (neće biti regression)

**Odlučujem**: potpuno brisanje legacy praznih direktorija; legacy `cli/psbuild.py` zamijenjen novim fajlom na istoj putanji (commit overwrite).

### CLI specifikacija

```python
# src/parser_studio/presentation/cli/psbuild.py
"""CLI entry point za Parser Studio.

Komande (za MVP):
- psbuild import <path>     : ucitaj .xlsx, prikazi DocumentEvidence sazetak
- psbuild analyze <path>   : import + analyze + prikazi ExtractionDraft sazetak
- psbuild confirm <path> --field kolicina=5 --actor user:radovan
                           : import + analyze + confirm sa manualnim vrijednostima
- psbuild --version         : ispisi verziju
- psbuild --help            : ispisi help

Migriran iz cli/psbuild.py (legacy). Ostaje backward-compatible
import putanja preko compat layer-a za 1 release.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from parser_studio.bootstrap import build_default_application


VERSION = "0.2.0"


def cmd_import(args, app) -> int:
    from parser_studio.application.ingest.import_document import ImportRequest
    result = app[0].execute(ImportRequest(path=Path(args.path)))
    print(f"Document: {result.document.source_path}")
    print(f"Cells: {len(result.document.cells)}")
    print(f"Sheets: {len(result.document.pages)}")
    return 0


def cmd_analyze(args, app) -> int:
    from parser_studio.application.extraction.analyze_invoice import AnalyzeRequest
    from parser_studio.application.ingest.import_document import ImportRequest
    import_result = app[0].execute(ImportRequest(path=Path(args.path)))
    target_fields = ("kolicina", "cijena_jed", "iznos", "naziv_robe", "tarifni_broj", "zemlja_porijekla")
    draft = app[1].execute(AnalyzeRequest(
        document=import_result.document,
        target_fields=target_fields,
    ))
    for field in target_fields:
        candidates = draft.candidates_for(field)
        print(f"{field}: {len(candidates)} candidate(s)")
    return 0


def cmd_confirm(args, app) -> int:
    from parser_studio.application.extraction.analyze_invoice import AnalyzeRequest
    from parser_studio.application.ingest.import_document import ImportRequest
    from parser_studio.application.review.confirm_invoice import (
        ConfirmRequest, FieldConfirmation,
    )
    from parser_studio.domain.evidence.locator import Locator
    import_result = app[0].execute(ImportRequest(path=Path(args.path)))
    target_fields = tuple(args.field.split("=")[0] for args.field in args.field)
    draft = app[1].execute(AnalyzeRequest(
        document=import_result.document,
        target_fields=target_fields,
    ))
    confirmations = []
    for field_value in args.field:
        field, value = field_value.split("=", 1)
        confirmations.append(FieldConfirmation(
            field=field,
            raw_value=None,
            normalized_value=value,
            locator=Locator(source_path=str(import_result.document.source_path), kind="excel"),
            confirmed=True,
        ))
    events = app[2].execute(ConfirmRequest(
        draft=draft,
        confirmations=tuple(confirmations),
        actor=args.actor,
    ))
    print(f"Confirmed {len(events)} field(s)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="psbuild", description="Parser Studio CLI")
    parser.add_argument("--version", action="store_true")
    subparsers = parser.add_subparsers(dest="command")
    p_import = subparsers.add_parser("import", help="Import dokument")
    p_import.add_argument("path", help="Putanja do .xlsx/.xls")
    p_analyze = subparsers.add_parser("analyze", help="Import + analyze")
    p_analyze.add_argument("path")
    p_confirm = subparsers.add_parser("confirm", help="Import + analyze + confirm")
    p_confirm.add_argument("path")
    p_confirm.add_argument("--field", action="append", required=True, help="field=value")
    p_confirm.add_argument("--actor", default="user:cli", help="user id za learning event")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.version:
        print(f"psbuild {VERSION}")
        return 0
    app = build_default_application(db_path=":memory:")
    try:
        if args.command == "import":
            return cmd_import(args, app)
        elif args.command == "analyze":
            return cmd_analyze(args, app)
        elif args.command == "confirm":
            return cmd_confirm(args, app)
        else:
            parser.print_help()
            return 1
    finally:
        # SQLite repo close (cetvrti element tuple-a)
        app[3].close()


if __name__ == "__main__":
    sys.exit(main())
```

### Architecture tests

```python
# tests/architecture/test_import_boundaries.py
"""Architecture tests — provjera import granica prema V3 DEP-001..DEP-005.

Koristi AST za analizu import statements u source fajlovima.

Pravila:
- domain/ NE SMIJE importovati adapters, presentation, sqlite3, openpyxl, xlrd, docling, contract
- application/ NE SMIJE importovati adapters, presentation, sqlite3, openpyxl, xlrd, docling, contract
- ports/ NE SMIJE importovati adapters, presentation, sqlite3, openpyxl, xlrd
- presentation/ NE SMIJE importovati sqlite3, openpyxl, xlrd, docling
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest


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


def _get_imports_from_file(file_path: Path) -> set[str]:
    """Vrati sve top-level module imports iz Python fajla."""
    source = file_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])
    return imports


def _layer_of(file_path: Path) -> str | None:
    """Vrati layer (domain/application/ports/presentation/adapters) za fajl."""
    parts = file_path.parts
    if "src/parser_studio/domain" in str(file_path):
        return "domain"
    if "src/parser_studio/application" in str(file_path):
        return "application"
    if "src/parser_studio/ports" in str(file_path):
        return "ports"
    if "src/parser_studio/presentation" in str(file_path):
        return "presentation"
    return None


def test_domain_layer_clean():
    """domain/ NE SMIJE importovati forbidden module."""
    root = Path("src/parser_studio/domain")
    forbidden = FORBIDDEN_IMPORTS_BY_LAYER["domain"]
    violations = []
    for py_file in root.rglob("*.py"):
        imports = _get_imports_from_file(py_file)
        bad = imports & forbidden
        if bad:
            violations.append((str(py_file), bad))
    assert violations == [], f"domain violations: {violations}"


def test_application_layer_clean():
    root = Path("src/parser_studio/application")
    forbidden = FORBIDDEN_IMPORTS_BY_LAYER["application"]
    violations = []
    for py_file in root.rglob("*.py"):
        imports = _get_imports_from_file(py_file)
        bad = imports & forbidden
        if bad:
            violations.append((str(py_file), bad))
    assert violations == [], f"application violations: {violations}"


def test_ports_layer_clean():
    root = Path("src/parser_studio/ports")
    forbidden = FORBIDDEN_IMPORTS_BY_LAYER["ports"]
    violations = []
    for py_file in root.rglob("*.py"):
        imports = _get_imports_from_file(py_file)
        bad = imports & forbidden
        if bad:
            violations.append((str(py_file), bad))
    assert violations == [], f"ports violations: {violations}"


def test_presentation_layer_clean():
    root = Path("src/parser_studio/presentation")
    forbidden = FORBIDDEN_IMPORTS_BY_LAYER["presentation"]
    violations = []
    for py_file in root.rglob("*.py"):
        imports = _get_imports_from_file(py_file)
        bad = imports & forbidden
        if bad:
            violations.append((str(py_file), bad))
    assert violations == [], f"presentation violations: {violations}"
```

### Unit testovi za CLI

```python
# tests/unit/presentation/cli/test_psbuild.py
import pytest
from parser_studio.presentation.cli import psbuild


class TestCLI:
    def test_version_flag(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            psbuild.main(["--version"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "psbuild" in captured.out

    def test_help_flag(self, capsys):
        with pytest.raises(SystemExit):
            psbuild.main(["--help"])

    def test_import_command(self, tmp_path, capsys):
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.append(["a", "b"])
        xlsx = tmp_path / "test.xlsx"
        wb.save(xlsx)
        wb.close()

        # Note: build_default_application kreira SQLite repo na disk
        # Za CLI test koristimo temp dir
        import os
        os.environ["PARSER_STUDIO_DB"] = str(tmp_path / "test.db")

        result = psbuild.main(["import", str(xlsx)])
        assert result == 0
        captured = capsys.readouterr()
        assert "Cells:" in captured.out
```

### Unit test za ViewModel

```python
# tests/unit/presentation/qt/test_viewmodels.py
from parser_studio.presentation.qt.viewmodels.review_invoice_viewmodel import (
    ReviewInvoiceViewModel,
)


class TestReviewInvoiceViewModel:
    def test_construction(self):
        vm = ReviewInvoiceViewModel()
        assert vm is not None
```

### cryptography opcije

**Opcija A: Ukloniti `cryptography` iz dependencies (preporuka V3):**
```toml
# pyproject.toml
dependencies = [
    "PySide6>=6.6",
    "pdfplumber>=0.10",
    "openpyxl>=3.1",
    "xlrd>=2.0",
    "rapidfuzz>=3.0",
    # "cryptography>=41.0",   # UKLONJENO — V3 sekcija 16
    "pydantic>=2.0",
    "jinja2>=3.1",
]

[project.optional-dependencies]
signing = ["cryptography>=41.0"]
```

**Opcija B: Ostaviti za MVP, ukloniti u zasebnom tasku.**

Preporuka: Opcija A (V3 compliance).

---

## Out of scope

```text
- Prava Qt GUI implementacija (samo placeholder struktura za FAZA B / M4)
- Wizard workflow (FAZA B / M4)
- Migration legacy core/ u novu strukturu (A0-A6 vec zavrseni; core ostaje za benchmark/test reference)
- Review GUI (FAZA B)
- AI Advisor (FAZA G)
- Codegen (FAZA H)
- Verifier (FAZA I)
- CLI export (FAZA J)
- Architecture test za FAZA B+ module (FAZA B posao)
- Fix test_f9_no_broken_rows regression (benchmark cleanup)
- Cleanup 192+ ruff gresaka
```

---

## Expected files

```text
Novi:
- src/parser_studio/presentation/cli/__init__.py
- src/parser_studio/presentation/cli/psbuild.py
- src/parser_studio/presentation/qt/__init__.py (vec postoji)
- src/parser_studio/presentation/qt/viewmodels/__init__.py
- src/parser_studio/presentation/qt/viewmodels/review_invoice_viewmodel.py
- src/parser_studio/presentation/qt/widgets/__init__.py
- src/parser_studio/presentation/qt/wizard/__init__.py
- tests/unit/presentation/__init__.py
- tests/unit/presentation/cli/__init__.py
- tests/unit/presentation/cli/test_psbuild.py
- tests/unit/presentation/qt/__init__.py
- tests/unit/presentation/qt/test_viewmodels.py
- tests/architecture/__init__.py
- tests/architecture/test_import_boundaries.py

Izmijenjeni:
- pyproject.toml
  (entry point: parser_studio.presentation.cli.psbuild:main;
   cryptography u optional[signing] ILI ukloniti)

Obrisani (cleanup):
- cli/psbuild.py (legacy)
- cli/__init__.py (legacy, prazan)
- services/__init__.py (prazan)
- viewmodels/__init__.py (prazan)
- views/__init__.py (prazan)
- views/widgets/__init__.py (prazan)
- views/wizard/__init__.py (zastario)

Premješteni:    nijedan
```

---

## Architecture boundaries

A7 NE SMIJE probiti (architecture testovi to provjeravaju):

```text
[ ] domain/ → adapters, presentation, sqlite3, openpyxl, xlrd, docling, contract
[ ] application/ → adapters, presentation, sqlite3, openpyxl, xlrd, docling, contract
[ ] ports/ → adapters, presentation, sqlite3, openpyxl, xlrd, docling
[ ] presentation/ → sqlite3, openpyxl, xlrd, docling, adapters.persistence.sqlite
```

**Dozvoljeno:**
- `presentation/cli/psbuild.py` importuje `parser_studio.application.*`, `parser_studio.bootstrap` (CLI entry point za application)
- `presentation/qt/viewmodels/*` importuje `parser_studio.application.*`, `parser_studio.domain.*` (MVVM binding)
- `adapters/persistence/sqlite/*` importuje `sqlite3` (konkretna tehnologija, dozvoljeno)

---

## Compatibility requirements

```text
[ ] Svi postojeći testovi i dalje rade (330 PASS + 1 FAIL = test_f9 pre-existing)
[ ] Svi legacy importi iz core/ i dalje rade (core/ NETAKNUT)
[ ] legacy cli/psbuild.py MOZE biti obrisan (sadrzi samo entry point; svi testovi importuju iz cli/psbuild.py)
[ ] NEMA promjene core/, contract/, cli/legacy testova
[ ] CLI radi sa psbuild --help, --version, import, analyze, confirm
[ ] NEMA parallel "core/" + "src/" business koda (cli/services/views su prazni ili obrisani)
```

---

## Acceptance criteria

```text
[ ] src/parser_studio/presentation/cli/psbuild.py sa import, analyze, confirm komandama
[ ] src/parser_studio/presentation/qt/ sa viewmodels/, widgets/, wizard/ (placeholders)
[ ] Legacy cli/, services/, viewmodels/, views/ obrisani (ili deprecation notice)
[ ] pyproject.toml entry point: parser_studio.presentation.cli.psbuild:main
[ ] cryptography premjesten u optional[signing] ILI uklonjen
[ ] Architecture tests u tests/architecture/test_import_boundaries.py (PASS)
[ ] 4+ unit testova (CLI, ViewModel, 4 architecture test layer-a)
[ ] pytest ista ili bolja statistika (max 1 FAIL = test_f9 pre-existing)
[ ] ruff ne značajno gore od baseline (192)
[ ] contract drift PASS
[ ] python -c "from parser_studio.presentation.cli.psbuild import main" OK
[ ] python -m pytest tests/architecture/ -v PASS (4 testova)
[ ] python -m parser_studio.presentation.cli.psbuild --help OK
[ ] python -m parser_studio.presentation.cli.psbuild --version OK
[ ] Graft blast: nema false "impacted dependents"
[ ] CURRENT_STATE A7 status DONE
[ ] Commit + push na dev
```

---

## Required tests

```text
Unit (novi):
- tests/unit/presentation/cli/test_psbuild.py
  - --version flag
  - --help flag
  - import komanda
  - analyze komanda
  - confirm komanda sa --field --actor
  - build_parser() radi
  - main() bez argumenata printa help i vraca 1

- tests/unit/presentation/qt/test_viewmodels.py
  - ReviewInvoiceViewModel konstrukcija

Architecture:
- tests/architecture/test_import_boundaries.py
  - test_domain_layer_clean
  - test_application_layer_clean
  - test_ports_layer_clean
  - test_presentation_layer_clean

Unit (postojeći):
- svi ostali testovi i dalje PASS

Integration:    nijedan u A7
```

---

## Impact analysis required (Graft SECONDARY period)

```text
[Da] MEDIUM risk (CLI entry point change, legacy cleanup)

Simboli za praćenje (NOVI):
- parser_studio.presentation.cli.psbuild.main
- parser_studio.presentation.cli.psbuild.build_parser
- parser_studio.presentation.qt.viewmodels.review_invoice_viewmodel.ReviewInvoiceViewModel

Simboli za PROŠIRENJE (IZMJENA):
- pyproject.toml entry point

Simboli za BRISANJE:
- cli.psbuild (legacy)
- services (prazno)
- viewmodels (prazno)
- views (prazno)

Alati:
- graft build                 # reindeksiranje
- graft grep "psbuild"        # CLI entry point
- graft grep "presentation"   # novi sloj
- graft blast                 # diff working tree vs HEAD (ukljucuje deletions)
- ručni grep fallback za .toml i legacy brisanja
```

**"Zero callers" NIJE dovoljno.**

---

## Risks

```text
1. Brisanje legacy cli/psbuild.py MOZE slomiti eksterne korisnike.
   Mitigacija: samo CLI testovi koriste interni CLI; eksterni "psbuild" entry point
               se mijenja iz cli.psbuild:main u parser_studio.presentation.cli.psbuild:main
               (isto ime, nova putanja — Python entry point lookup).

2. Architecture tests koriste AST; mogu propustiti neke import patterns.
   Mitigacija: 4 layer-a testirana (domain, application, ports, presentation);
               testovi dovoljno granularni da uhvate većinu gresaka.

3. cryptography premjestan u optional[signing] MOZE slomiti ako neko importuje.
   Mitigacija: provjeriti import grafik (grep); trenutno nema import u src/parser_studio/.

4. CLI testovi mogu ostaviti SQLite fajlove.
   Mitigacija: tmp_path fixture + env PARSER_STUDIO_DB override.

5. Wizard migration samo je placeholder; GUI ne radi.
   Mitigacija: placeholder struktura sa docstring-om "FAZA B / M4"; Qt instalacija
               nije potrebna za MVP.

6. legacy cli/services/views su prazni ali tracking; brisanje mijenja git
   history.
   Mitigacija: brisanje u istom commit-u sa novim fajlovima (atomic).

7. psbuild CLI poziva build_default_application(db_path=":memory:")
   za testiranje; u produkciji je file-based.
   Mitigacija: env var PARSER_STUDIO_DB za override.
```

---

## Execution evidence required

```text
[ ] git diff --stat base..HEAD (samo novi fajlovi + pyproject.toml + deletions)
[ ] python -m pytest -q stvarni izlaz
[ ] python -m pytest tests/architecture/ -v stvarni izlaz
[ ] python -m ruff check . stvarni izlaz
[ ] python -m contract.drift_check "$DEKLARANT_PRO_ROOT" stvarni izlaz
[ ] python -c "from parser_studio.presentation.cli.psbuild import main" OK
[ ] python -c "from parser_studio.presentation.cli.psbuild import build_parser; p = build_parser(); print(p)" OK
[ ] python -m parser_studio.presentation.cli.psbuild --version OK
[ ] python -m parser_studio.presentation.cli.psbuild --help OK
[ ] python -m pytest tests/architecture/ -v OK (4 testova PASS)
[ ] graft build output
[ ] graft blast output
[ ] File:line dokaz za legacy netaknutost (git diff --stat core/)
```

---

## Reviewer evidence

```text
[ ] vlastiti git diff review
[ ] vlastiti pytest -q reprodukcija
[ ] vlastiti architecture test reprodukcija
[ ] vlastiti ruff reprodukcija
[ ] vlastiti import sanity provjera (CLI + ViewModel)
[ ] provjera da legacy core/ NIJE DIRAN
[ ] provjera da CLI radi sa stvarnim .xlsx fajlom (ne samo mock)
[ ] provjera da architecture testovi uhvacaju stvarno kršenje (ručno probati)
[ ] R-001 ... nalazi
```

---

## Integration gate

```text
[ ] Implementer != Reviewer
[ ] Svi acceptance criteria zadovoljeni
[ ] CURRENT_STATE.md A7 status DONE
[ ] nema stvarnih faktura / poslovnih podataka u Git diffu
[ ] nema secret / token podataka u Git diffu
[ ] Post-merge integration gate: ponoviti pytest + architecture + ruff + drift
```

---

## Definition of Done — A7

```text
[ ] presentation/cli/psbuild.py sa CLI komandama
[ ] presentation/qt/ struktura (placeholders)
[ ] Legacy cli/services/views/viewmodels obrisani
[ ] pyproject.toml entry point update + cryptography cleanup
[ ] Architecture tests u tests/architecture/ (4 layer-a)
[ ] 4+ unit testova
[ ] pytest ista ili bolja statistika
[ ] architecture tests PASS
[ ] ruff ne značajno gore
[ ] contract drift PASS
[ ] Graft blast čist
[ ] CURRENT_STATE A7: DONE
[ ] commit + push
[ ] Sva FAZA A (A0-A7) ZAVRŠENA
```

---

## Notes

- A7 je **ZADNJI A MILESTONE** — poslije njega slijedi FAZA B (M3 Docling, M4 Review GUI) i kasnije.
- Migracija legacy `cli/` NE SMIJE promijeniti ponašanje CLI-ja — samo entry point lokaciju.
- Architecture tests su AUTHORITATIVNI za dependency granice (po V3); uvesti u CI poslije A7.
- Wizard je placeholder; Qt instalacija NIJE potrebna za MVP (PySide6 vec u dependencies).

---

## Final status

```text
[ ] DRAFT
[ ] ACTIVE
[ ] REVIEW
[ ] DONE
[ ] CANCELLED]
```

---

## OUT_OF_SCOPE_FINDING (popunjava implementer)

```text
(navesti ako postoji)
```

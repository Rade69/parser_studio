# M4 Briefing Prompt — za Pi agenta

**Copy-paste ovaj tekst u Pi kontekst. NE MIJENJAJ.**

---

You are implementing **Task M4** for Parser Studio.

## Objective

Implement Qt widgets for the Invoice Review GUI (V3 B4): `InvoiceReviewView` (main view) + `CellTableView` (read-only table) bound to `ReviewInvoiceViewModel` (A7 placeholder).

## Repository

- Path: `H:/parser_studio-m4` (git worktree, branch `task/m4-review-gui`)
- Base: `dev @ cc61f56`
- Full task contract: `H:/parser_studio-m4/agent_reports/M4-task-contract.md` — READ IT FIRST

## Context

- Hexagonal architecture (FAZA A complete, M1+M3 merged)
- Domain: `parser_studio.domain.evidence` (Locator, Evidence, DocumentEvidence, Candidate, ExtractionContext, ExtractionDraft)
- A7 already created: `parser_studio/presentation/qt/viewmodels/review_invoice_viewmodel.py` — ReviewInvoiceViewModel with `load_draft()`, `candidates_for()`, `confirm_field()`
- Asset for design input: `asset/parser_studio_gui_mockup.png` (UNTRACKED) — review it for layout inspiration
- PySide6 6.11 + pytest-qt 4.5 available in dev dependencies

## Scope (IN)

Create these files:

```
src/parser_studio/presentation/qt/widgets/invoice_review_view.py     # InvoiceReviewView(QWidget)
src/parser_studio/presentation/qt/widgets/cell_table_view.py         # CellTableView(QTableWidget)
src/parser_studio/presentation/qt/widgets/__init__.py                # Extend exports
tests/unit/presentation/qt/widgets/__init__.py                       # empty
tests/unit/presentation/qt/widgets/test_invoice_review_view.py       # 5-8 tests
tests/unit/presentation/qt/widgets/test_cell_table_view.py           # 5-7 tests
agent_reports/2026-09-14-M4-evidence.md                              # final evidence
```

## Scope (OUT — DO NOT TOUCH)

- ❌ `bootstrap.py`
- ❌ Anything in `src/parser_studio/domain/profiles/*` (M2 ownership)
- ❌ Anything in `src/parser_studio/ports/profile_repository.py` (M2)
- ❌ Anything in `src/parser_studio/application/profiles/*` (M2)
- ❌ Anything in `src/parser_studio/adapters/profiles/*` (M2)
- ❌ Anything in `src/parser_studio/ports/advisor.py` (M3)
- ❌ Anything in `src/parser_studio/adapters/ai/*` (M3)
- ❌ Anything in `src/parser_studio/application/learning/*` (M3)
- ❌ Anything in `src/parser_studio/domain/invoice/*` (M1)
- ❌ Anything in `src/parser_studio/presentation/cli/*` (A7)
- ❌ Anything in `src/parser_studio/presentation/qt/wizard/*` (A7)

You MAY additively extend `src/parser_studio/presentation/qt/viewmodels/review_invoice_viewmodel.py` if needed for Qt binding helpers — but do NOT change the existing public interface (`load_draft`, `candidates_for`, `confirm_field`).

## Acceptance criteria (MUST all pass)

```text
[ ] src/parser_studio/presentation/qt/widgets/invoice_review_view.py — InvoiceReviewView(QWidget)
[ ] src/parser_studio/presentation/qt/widgets/cell_table_view.py — CellTableView(QTableWidget)
[ ] InvoiceReviewView emits `confirmed(str, object)` signal when user confirms
[ ] CellTableView is read-only (NoEditTriggers)
[ ] CellTableView.load_document(document: DocumentEvidence) populates table
[ ] pytest tests/unit/presentation/qt/widgets/ — ALL PASS (10-15 tests)
[ ] pytest full suite — no new regressions
[ ] ruff check src/parser_studio/presentation/qt/widgets/ tests/unit/presentation/qt/widgets/ — All checks passed
[ ] architecture tests still PASS (presentation must NOT import sqlite3/openpyxl/xlrd/docling/adapters.persistence.sqlite)
[ ] PySide6 import works
[ ] import parser_studio.presentation.qt.widgets.invoice_review_view — OK
[ ] import parser_studio.presentation.qt.widgets.cell_table_view — OK
[ ] Commit on task/m4-review-gui branch with selective git add (NEVER git add --all)
[ ] Push to origin/task/m4-review-gui
[ ] Evidence file with REAL pytest output and git diff --stat
```

## Patterns

- Use PySide6 6.x widgets (`QWidget`, `QVBoxLayout`, `QTableWidget`, `QTableWidgetItem`, `Signal`)
- `pytest-qt` `qtbot` fixture for widget tests
- Read-only enforcement via `setEditTriggers(QTableWidget.NoEditTriggers)`
- Signal-slot binding for viewmodel ↔ view (use Qt's signal mechanism)
- Frozen dataclasses for value objects (already in A2 evidence domain pattern)

## Validation commands

```powershell
cd H:/parser_studio-m4
python -m pytest tests/unit/presentation/qt/widgets/ -v
python -m pytest -q --ignore=tests/integration
python -m ruff check src/parser_studio/presentation/qt/widgets/ tests/unit/presentation/qt/widgets/
python -m pytest tests/architecture/ -v
```

## Final deliverable

1. All files written and tests passing
2. Commit + push to `origin/task/m4-review-gui`
3. Evidence file: `agent_reports/2026-09-14-M4-evidence.md` containing:
   - `git log --oneline -5`
   - `git diff --stat dev..HEAD`
   - Full pytest output (copy-paste)
   - ruff output
   - Architecture test output
4. Return summary:
   ```
   RESULT: PASS | FAIL | PARTIAL
   Changes: <file paths>
   Tests added: <count>
   Tests passing: <count>
   Architecture tests: PASS
   Ruff: <error count>
   Assumptions: <list>
   Blockers: <list or "none">
   ```

If you hit a blocker (PySide6 import fails, pytest-qt infra broken, architecture test fails), report immediately. Do NOT workaround V3 architecture rules.

Begin.

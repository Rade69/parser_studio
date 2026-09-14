---
task_id: M4
title: "InvoiceReviewView + CellTableView Qt widgets (FAZA B / V3 B4)"
status: ACTIVE
risk: MEDIUM
date: 2026-09-14
branch: task/m4-review-gui
worktree: H:/parser_studio-m4
base: dev @ cc61f56 (HEAD nakon M1+M3 merge-a)
implementer: Pi agent (korisnik dispatchuje)
---

# M4 — Review Invoice GUI (V3 B4)

> Uvesti `InvoiceReviewView` (glavni Qt widget) + `CellTableView` (tabela ćelija dokumenta) + binding na `ReviewInvoiceViewModel` iz A7. Koristi `asset/parser_studio_gui_mockup.png` kao dizajn input.

**Pi agent implementira u `H:/parser_studio-m4` (worktree), grana `task/m4-review-gui`.**
**Mavis (root sesija) NE pokreće Pi — korisnik prosljeđuje briefing prompt iz `agent_reports/2026-09-14-M4-briefing-prompt.md`.**

---

## Canonical references

```text
docs/PLAN.md              V3 sekcija 1893 (B4 — Review workspace)
.asset/parser_studio_gui_mockup.png     GUI mockup (UNTRACKED) — dizajn input
src/parser_studio/presentation/qt/viewmodels/review_invoice_viewmodel.py  (A7 — MVVM placeholder)
.agent/CURRENT_STATE.md   Snapshot nakon M1+M3 (commit cc61f56)
.agent/PROJECT_MAP.md     Sekcija C
V3 milestone:             B4 (Review workspace)
```

---

## Scope (IN)

### 1. InvoiceReviewView (Qt widget)

```text
src/parser_studio/presentation/qt/widgets/invoice_review_view.py
src/parser_studio/presentation/qt/widgets/__init__.py  (extend, dodaj export)
```

`InvoiceReviewView(QWidget)` — glavni widget za review jedne fakture:

- Layout: `QVBoxLayout`
- Gornji dio: `CellTableView` (read-only prikaz ćelija)
- Srednji dio: lista kandidata po polju (selector)
- Donji dio: confirmation panel (text input za vrijednost, "Confirm" dugme)
- Side panel (opcionalno): preview of source cell location

```python
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Signal

class InvoiceReviewView(QWidget):
    """Glavni view za Review Invoice GUI."""
    confirmed = Signal(str, object)  # field, value

    def __init__(self, viewmodel: ReviewInvoiceViewModel, parent: QWidget | None = None):
        super().__init__(parent)
        self._viewmodel = viewmodel
        self._init_ui()
        self._bind_viewmodel()

    def _init_ui(self) -> None:
        # Kreiraj layout sa CellTableView + candidate selector + confirm panel
        ...
```

### 2. CellTableView (Qt widget)

```text
src/parser_studio/presentation/qt/widgets/cell_table_view.py
```

`CellTableView(QTableWidget)` — read-only prikaz ćelija dokumenta:

- Učitava `DocumentEvidence` iz viewmodel-a
- Prikazuje sheet/row/col strukturu
- Boja ćelije ovisno o `Locator` highlighted statusa
- NE SMIJE biti editable (review-only)

```python
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem

class CellTableView(QTableWidget):
    """Read-only prikaz DocumentEvidence ćelija."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setEditTriggers(QTableWidget.NoEditTriggers)  # read-only

    def load_document(self, document: DocumentEvidence) -> None:
        """Popuni tabelu iz DocumentEvidence (sheets, rows, cells)."""
        ...
```

### 3. Binding na ReviewInvoiceViewModel (A7)

M4 MOŽE extendati `review_invoice_viewmodel.py` SAMO ako treba dodati:
- Qt signal binding helper
- Property za highlighted cells

**NE SMIJE** mijenjati interface `ReviewInvoiceViewModel` (load_draft, candidates_for, confirm_field).

Ako M4 treba dodati `set_highlighted_locator(locator)`, smije. Ali to mora biti additive (nova metoda, ne mijenja postojeće).

### 4. Testovi

```text
tests/unit/presentation/qt/widgets/__init__.py
tests/unit/presentation/qt/widgets/test_invoice_review_view.py   (5-8 testova: layout, signal emit, viewmodel binding)
tests/unit/presentation/qt/widgets/test_cell_table_view.py       (5-7 testova: read-only, load_document, populate)
```

Testovi koriste `pytest-qt` (već u dev dependencies).

---

## Scope (OUT — ne radi u M4)

- ❌ Profile Builder UI (M2 scope)
- ❌ AI Advisor UI (ConsultAdvisor binding — FAZA kasnije)
- ❌ Backend logika (samo binding na postojeće viewmodel)
- ❌ Profile Wizard (placeholder u A7 — ostaje placeholder)
- ❌ AI advice display
- ❌ Migracija postojećih faktura u Qt
- ❌ Drag & drop, file dialog (CLI radi to)
- ❌ Settings/preferences dialog
- ❌ Internationalization (i18n)

---

## Disjunktni ownership (paralelan rad sa M2)

```text
M4 SMIJE kreirati/mijenjati:
  src/parser_studio/presentation/qt/widgets/invoice_review_view.py
  src/parser_studio/presentation/qt/widgets/cell_table_view.py
  src/parser_studio/presentation/qt/widgets/__init__.py            (extend za export)
  src/parser_studio/presentation/qt/viewmodels/review_invoice_viewmodel.py  (OPREZ: samo additive izmjene)
  tests/unit/presentation/qt/widgets/__init__.py
  tests/unit/presentation/qt/widgets/test_invoice_review_view.py
  tests/unit/presentation/qt/widgets/test_cell_table_view.py
  agent_reports/M4-task-contract.md
  agent_reports/2026-09-14-M4-evidence.md

M4 NE SMIJE dodirivati (M2 ownership):
  src/parser_studio/domain/profiles/*
  src/parser_studio/ports/profile_repository.py
  src/parser_studio/adapters/profiles/*
  src/parser_studio/application/profiles/*
  tests/unit/domain/profiles/*
  tests/unit/adapters/profiles/*
  tests/unit/application/profiles/*

M4 NE SMIJE dodirivati (M3 ownership):
  src/parser_studio/ports/advisor.py
  src/parser_studio/adapters/ai/*
  src/parser_studio/application/learning/*

M4 NE SMIJE dodirivati (M1 ownership):
  src/parser_studio/domain/invoice/*

M4 NE SMIJE dodirivati (A7 ownership):
  src/parser_studio/presentation/cli/*
  src/parser_studio/presentation/qt/wizard/*
```

**Merge procedura:** M4 je append-only u `presentation/qt/widgets/`. M2 je append-only u `domain/profiles/` + `application/profiles/` + `adapters/profiles/`. Trivijalan rebase + merge.

Ako M4 extend-uje `review_invoice_viewmodel.py` sa novim metodama — additive merge. Ako M2 ili M3 istovremeno diraju isti fajl — konflikt; koordinator rješava.

---

## Acceptance criteria

```text
[ ] src/parser_studio/presentation/qt/widgets/invoice_review_view.py — InvoiceReviewView(QWidget)
[ ] src/parser_studio/presentation/qt/widgets/cell_table_view.py — CellTableView(QTableWidget)
[ ] InvoiceReviewView emituje `confirmed` signal(field, value) kad korisnik potvrdi
[ ] CellTableView je read-only (NoEditTriggers)
[ ] CellTableView.load_document(document: DocumentEvidence) — populate from DocumentEvidence
[ ] pytest tests/unit/presentation/qt/widgets/ — svi PASS (10-15 testova)
[ ] pytest cijeli suite — NEMA novih regression-a
[ ] ruff check src/parser_studio/presentation/qt/widgets/ tests/unit/presentation/qt/widgets/ — All checks passed
[ ] architecture testovi i dalje PASS (presentation NE importuje sqlite3/openpyxl/xlrd/docling/adapters.persistence.sqlite)
[ ] PySide6 import radi (PySide6 6.x dostupan)
[ ] import parser_studio.presentation.qt.widgets.invoice_review_view — OK
[ ] import parser_studio.presentation.qt.widgets.cell_table_view — OK
[ ] Commit na task/m4-review-gui grani sa selektivnim git add
[ ] Push na origin/task/m4-review-gui
[ ] Evidence fajl sa stvarnim pytest izlazom i git diff --stat
```

---

## V3 architecture compliance

```text
presentation/qt/widgets/invoice_review_view.py:
  - PySide6 import dozvoljen u presentation sloju
  - NE importuje sqlite3, openpyxl, xlrd, docling
  - NE importuje adapters.persistence.sqlite direktno (kroz application layer)
  - Binding preko ReviewInvoiceViewModel (NE direktan adapter import)

presentation/qt/widgets/cell_table_view.py:
  - PySide6 import dozvoljen
  - DocumentEvidence input (domain.evidence) — dozvoljeno (presentation cita domain)
  - CellTableView NEMA write funkcije
```

---

## Testiranje

```powershell
cd H:/parser_studio-m4

# 1. M4 testovi
python -m pytest tests/unit/presentation/qt/widgets/ -v

# 2. Regression
python -m pytest -q --ignore=tests/integration

# 3. Ruff
python -m ruff check src/parser_studio/presentation/qt/widgets/ tests/unit/presentation/qt/widgets/

# 4. Architecture
python -m pytest tests/architecture/ -v
```

---

## Risk

**MEDIUM** — PySide6 testovi su kompleksni (Qt event loop, widget lifecycle). Ako test infra pukne, M4 se blokira.

Mitigacija:
- `pytest-qt` već u dev deps (od A7)
- Koristiti `qtbot` fixture za widget testove
- NE praviti custom event loop (koristiti `qtbot.waitSignal`)
- Ako PySide6 import fail-uje, prijaviti blocker — ne zaobilaziti

Ako M4 utvrdi da PySide6 testovi previše kompleksni za task scope:
- Minimum: klasa definirana + tipovi, BEZ punog Qt binding testiranja
- Dodati `pytest.importorskip("PySide6")` u test fajlove da se graceful skip-aju u okruženju bez PySide6
- Fallback M4-minimum: definicija widget klasa + ručni test konstruktora

---

## Definition of Done

```text
[ ] Kod u gore navedenim fajlovima napisan po acceptance kriterijima
[ ] Svi test PASS (acceptance + regression + architecture)
[ ] ruff clean za M4 fajlove
[ ] Commit na task/m4-review-gui sa selektivnim git add
[ ] Commit message: arch(M4): InvoiceReviewView + CellTableView Qt widgets (V3 B4)
[ ] Push na origin/task/m4-review-gui
[ ] Evidence fajl: agent_reports/2026-09-14-M4-evidence.md sa stvarnim pytest izlazom + git diff --stat
[ ] NE SMIJE dirati M2/M3/M1 fajlove
```

---

## Briefing prompt za Pi agenta

Briefing prompt se nalazi u zasebnom fajlu: `agent_reports/2026-09-14-M4-briefing-prompt.md`.

**Korisnik pokreće Pi agenta:**
1. Otvori `H:/parser_studio-m4` worktree (već kreiran od strane Mavis koordinatora)
2. Copy-paste briefing prompt u Pi kontekst
3. Pošalji Pi-u
4. Čekaj rezultat
5. Javi Mavis-u evidence report + commit hash

**Mavis NE pokreće Pi.** Korisnik to radi lično.

---

**Status:** ACTIVE — Pi agent implementira na `task/m4-review-gui` u `H:/parser_studio-m4` (kad korisnik pokrene).
**Parallel partner:** Mavis (root sesija) na `task/m2-profile-builder` u `H:/parser_studio-m2`.

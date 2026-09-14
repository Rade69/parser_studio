---
task_id: A2
title: "Evidence domain — Locator, Evidence, DocumentEvidence, Candidate, ExtractionContext"
status: ACTIVE
risk: MEDIUM-HIGH
date: 2026-09-14
branch: dev (base)
worktree: TBD
---

# A2 — Evidence domain (value objects)

> Uvesti immutable domain value objects prema V3 sekcija 8: `Locator`, `Evidence`, `DocumentEvidence`, `Candidate`, `ExtractionContext`. Bez migracije legacy koda; samo dodavanje novog domenskog sloja sa kompatibilnim adapterom.

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
docs/PLAN.md                                  (V3, sekcija 8: Centralni domain modeli; sekcija 41: A2)
.agent/PROJECT_MAP.md                         (sekcija B: domain posjeduje Invoice/Evidence/Locator/Candidate)
.agent/TASK_ROUTING.md                        (sekcija "Domain / Evidence")
core/documents/base.py                        (Cell, ExtractionTable, Document — kompatibilnost)
core/documents/excel_document.py              (ExcelDocument — koristi Cell, treba adapter)
agent_reports/2026-09-14-graft-evaluation.md  (Graft SECONDARY pravila)
```

---

## Current-state preconditions

```text
[ ] branch: dev na b1671f6 (A1 commit)
[ ] A1 acceptance DONE — src/parser_studio/ skelet postoji
[ ] Graft status: SECONDARY (probacioni period)
[ ] baseline testovi: 180 PASS, 1 FAIL (test_f9), 1 SKIPPED
[ ] ruff: 157 errors (benchmark/test; nije pogoršano od A1)
[ ] contract drift: PASS
[ ] DEKLARANT_PRO_ROOT: H:/deklarant_pro
```

A2 može krenuti.

---

## Problem

V3 sekcija 8 zahtijeva immutable value objects za domain:

```python
@dataclass(frozen=True, slots=True)
class Locator:
    source_path: str
    kind: Literal["pdf", "excel", "text"]
    page: int | None = None
    bbox: tuple[float, float, float, float] | None = None
    sheet: str | None = None
    row: int | None = None
    col: int | None = None
    char_span: tuple[int, int] | None = None

@dataclass(frozen=True, slots=True)
class Evidence:
    raw_value: Any
    raw_text: str
    locator: Locator
    element_type: str
    source_id: str | None = None

@dataclass(frozen=True, slots=True)
class Candidate:
    field: str
    raw_value: Any
    normalized_value: Any
    locator: Locator
    evidence: str
    producer_id: str
    ai_assisted: bool = False
    issues: tuple[str, ...] = ()
```

Plus V3 implicitno: `DocumentEvidence` (standardizovan document model) i `ExtractionContext` (rezolver state).

Trenutno stanje:
- `src/parser_studio/domain/evidence/` je PRAZAN
- Legacy `core/documents/base.py` ima `Cell` (mješovit value object + provenance), `ExtractionTable` (sirovi rezultat), `Document` (Protocol)
- Novi modeli su potrebni da:
  1. Domain bude čist (bez infrastrukture)
  2. Budući resolvers/producers/validators imaju stabilan contract
  3. Postojeća Excel provenance može biti predstavljena novim modelom

---

## Goal

Kreirati `src/parser_studio/domain/evidence/` sa 5 value object fajlova + kompatibilni adapter + unit testovi, BEZ migracije legacy koda.

Acceptance:
- 5 novih fajlova sa ispravnim dataclass-ovima
- Compatibility adapter: `Cell` iz `core.documents.base` može se pretvoriti u `Evidence` iz novog modula bez gubitka informacije
- Unit testovi PASS
- pytest ukupno: NE SMIJE imati više od 1 FAIL (test_f9_no_broken_rows benchmark regression)
- ruff: NE SMIJE imati značajno više grešaka
- Domain NE importuje `sqlite3`, `openpyxl`, `xlrd`, `docling`, `PySide6`, `requests`, `httpx`, `contract`
- Graft blast: nema false "impacted dependents"

---

## In scope

### Novi fajlovi

```text
src/parser_studio/domain/evidence/
    __init__.py              # eksportuje Locator, Evidence, DocumentEvidence, Candidate, ExtractionContext, cell_to_evidence
    locator.py               # Locator dataclass (frozen, slots)
    evidence.py              # Evidence dataclass (frozen, slots)
    document_evidence.py     # DocumentEvidence model (dataclass ili dict-like)
    candidate.py             # Candidate dataclass (frozen, slots)
    extraction_context.py    # ExtractionContext dataclass
    cell_compat.py           # compatibility adapter: cell_to_evidence(Cell) -> Evidence
```

### Locator specifikacija

```python
from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True, slots=True)
class Locator:
    """Gdje u izvornom dokumentu se nalazi vrijednost."""
    source_path: str
    kind: Literal["pdf", "excel", "text"]

    page: int | None = None
    bbox: tuple[float, float, float, float] | None = None
    # bbox: x0, y0, x1, y1, normalizovano na [0,1] ako adapter ima razlog

    sheet: str | None = None
    row: int | None = None
    col: int | None = None

    char_span: tuple[int, int] | None = None
```

V3 pravilo: "Koordinate se u canonical evidence sloju normalizuju na `[0,1]`, origin top-left, osim ako adapter ima razlog da privremeno čuva native koordinate."

### Evidence specifikacija

```python
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True, slots=True)
class Evidence:
    """Nesto sto je stvarno vidjeno u dokumentu."""
    raw_value: Any
    raw_text: str
    locator: Locator
    element_type: str
    source_id: str | None = None
```

### DocumentEvidence specifikacija

```python
@dataclass(frozen=True, slots=True)
class DocumentEvidence:
    """Standardizovan document model nezavisan od Doclinga/Excela."""
    document_id: str
    source_path: str
    pages: list[Any]                  # ostavi Any za sada (kasnije Page model)
    text_elements: list[Evidence]
    tables: list[Evidence]             # ili specific Table model
    cells: list[Evidence]
    page_dimensions: dict[int, tuple[float, float]] | None = None
    metadata: dict[str, Any] | None = None
```

ALI — V3 kaže "Minimalno može sadržati: document_id, source files, pages, text elements, tables, cells, page dimensions, metadata". To je minimum, ne maksimum. A2 treba pokriti minimum + biti proširiv.

### Candidate specifikacija

```python
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True, slots=True)
class Candidate:
    """Prijedlog vrijednosti od strane extractora ili AI advisor.
    Nije istina.
    """
    field: str
    raw_value: Any
    normalized_value: Any
    locator: Locator
    evidence: str
    producer_id: str
    ai_assisted: bool = False
    issues: tuple[str, ...] = ()
```

### ExtractionContext specifikacija

```python
@dataclass(frozen=True, slots=True)
class ExtractionContext:
    """State za resolver/producer tokom extraction."""
    document_id: str
    language: str = "bs"             # default BHS latinica
    target_fields: tuple[str, ...] = ()
    profile_version: int | None = None
    producer_id: str | None = None
```

### Compatibility adapter specifikacija

```python
# src/parser_studio/domain/evidence/cell_compat.py
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.documents.base import Cell  # type: ignore

from .evidence import Evidence
from .locator import Locator


def cell_to_evidence(cell: "Cell", source_id: str | None = None) -> Evidence:
    """Pretvori legacy Cell u novi Evidence.

    Cell: value, row, col, page (PDF), x0, x1, top, sheet
    Evidence: raw_value, raw_text, locator, element_type, source_id

    Mapping:
        Cell.value           -> Evidence.raw_value
        Cell.text            -> Evidence.raw_text (computed property)
        Cell.sheet, row, col -> Locator(sheet, row, col)
        Cell.page, x0..top   -> Locator(page, bbox)
    """
    ...
```

VAŽNO: Adapter koristi TYPE_CHECKING import da NE kreira runtime cikličnu zavisnost između `src/parser_studio/domain/evidence/` i `core/`. TYPE_CHECKING import radi samo za type hints, ne za stvarni import.

ILI: adapter se može nalaziti u legacy `core/documents/` (npr. `core/documents/base.py` doda helper). Ali to miješa novi i stari kod.

**Preporuka:** adapter u novom modulu (`cell_compat.py`), sa TYPE_CHECKING importom.

### Unit testovi

```text
tests/unit/domain/
    __init__.py
    evidence/
        __init__.py
        test_locator.py
        test_evidence.py
        test_document_evidence.py
        test_candidate.py
        test_extraction_context.py
        test_cell_compat.py
```

Testovi trebaju pokrivati:
- Konstrukcija svakog dataclass-a sa svim poljima
- `frozen=True` provjera (mutacija baca `FrozenInstanceError`)
- `slots=True` provjera (klasa nema `__dict__`)
- Default vrijednosti
- TYPE_CHECKING import (bez ciklične zavisnosti)
- `cell_to_evidence` round-trip bez gubitka informacije

### Agent-friendly file headers

Svaki novi fajl počinje kratkim headerom (2-5 linija):

```python
# Domain: Locator.
# Posjeduje: source_path, kind, page, bbox, sheet, row, col, char_span.
# Ne zna za: SQLite, PySide6, Docling, openpyxl, contract.
```

---

## Out of scope

Sljedeće je EKSPLICITNO van A2:

```text
- Migracija core/documents/base.py Cell → novi Evidence (legacy ostaje)
- Migracija core/documents/excel_document.py da koristi novi Evidence (legacy ostaje)
- Migracija core/engines/excel_headers.py (A4: CandidateProducer)
- Bilo kakva promjena production logike
- Application use case-ovi (A5)
- LearningRepository / events (A6)
- Docling adapter (M3 / FAZA B)
- Review GUI (M4 / FAZA B)
- AI Advisor (FAZA G)
- Codegen (FAZA H)
- Verifier (FAZA I)
- Architecture tests (uvodi se u A2 acceptance ili A3, zavisno od dogovora)
- Fix test_f9_no_broken_rows regression (benchmark cleanup)
- Cleanup 157 ruff grešaka
- Uklanjanje cryptography iz pyproject.toml
```

Ako implementer pronađe nešto izvan scope-a:

```text
OUT_OF_SCOPE_FINDING:
<opis>
<zašto je izvan scope-a>
<prijedlog kako riješiti (ne implementirati samovoljno)>
```

---

## Expected files

```text
Novi:
- src/parser_studio/domain/evidence/__init__.py
- src/parser_studio/domain/evidence/locator.py
- src/parser_studio/domain/evidence/evidence.py
- src/parser_studio/domain/evidence/document_evidence.py
- src/parser_studio/domain/evidence/candidate.py
- src/parser_studio/domain/evidence/extraction_context.py
- src/parser_studio/domain/evidence/cell_compat.py
- tests/unit/domain/__init__.py
- tests/unit/domain/evidence/__init__.py
- tests/unit/domain/evidence/test_locator.py
- tests/unit/domain/evidence/test_evidence.py
- tests/unit/domain/evidence/test_document_evidence.py
- tests/unit/domain/evidence/test_candidate.py
- tests/unit/domain/evidence/test_extraction_context.py
- tests/unit/domain/evidence/test_cell_compat.py

Izmijenjeni:    nijedan
Obrisani:        nijedan
Premješteni:    nijedan
```

---

## Architecture boundaries

A2 NE SMIJE probiti:

```text
[ ] domain/evidence/ → sqlite3, openpyxl, xlrd, docling, PySide6, requests, httpx, contract
[ ] domain/evidence/ → adapters, presentation
[ ] domain/evidence/ → relative import iz core/ (samo TYPE_CHECKING za cell_compat)
[ ] cell_compat.py → runtime import iz core/ (TYPE_CHECKING samo)
```

Ako treba probiti bilo koju granicu, **prijaviti koordinatoru** prije početka.

---

## Compatibility requirements

```text
[ ] Svi postojeći testovi i dalje rade (ista PASS/SKIP statistika)
[ ] Svi legacy importi i dalje rade (core/, cli/, services/, views/)
[ ] NEMA promjene legacy koda (core/, cli/, services/, views/, viewmodels/)
[ ] NEMA parallel "core/" + "src/" business koda osim kompatibilnog adaptera
[ ] Kompatibilni adapter je READ-ONLY u odnosu na Cell (ne mijenja Cell)
```

---

## Acceptance criteria

```text
[ ] 5 novih fajlova u src/parser_studio/domain/evidence/ kreirana
[ ] cell_compat.py kreira
[ ] 6 test fajlova u tests/unit/domain/evidence/ kreirana
[ ] Sve klase su frozen=True, slots=True
[ ] Domain NE importuje zabranjene module (testirati sa architecture testom ili ručno)
[ ] pytest -q ista ili bolja statistika (max 1 FAIL = test_f9 pre-existing)
[ ] ruff ne više od baseline + tolerance (~+10 novih fajlova može dodati import greške)
[ ] contract drift PASS
[ ] python -c "from parser_studio.domain.evidence import Locator, Evidence, DocumentEvidence, Candidate, ExtractionContext, cell_to_evidence" OK
[ ] graft blast: nema false "impacted dependents" izvan ova 12 fajlova
[ ] CURRENT_STATE A2 status DONE
[ ] Commit + push na dev
[ ] Architecture test fajl (opcioni): tests/architecture/test_import_boundaries.py osigurava domain ne importuje sqlite3/openpyxl/xlrd/PySide6/docling/contract
```

---

## Required tests

```text
Unit (novi):
- tests/unit/domain/evidence/test_locator.py
  - construction (sa svim poljima)
  - frozen provjera (mutacija failuje)
  - slots provjera
  - default vrijednosti
  - kind literal provjera

- tests/unit/domain/evidence/test_evidence.py
  - construction
  - frozen
  - slots

- tests/unit/domain/evidence/test_document_evidence.py
  - construction (minimum V3 fields)
  - ekstendiranje (opciona polja)

- tests/unit/domain/evidence/test_candidate.py
  - construction
  - frozen
  - slots
  - default za ai_assisted i issues

- tests/unit/domain/evidence/test_extraction_context.py
  - construction
  - default za language, target_fields

- tests/unit/domain/evidence/test_cell_compat.py
  - Cell sa svim poljima → Evidence round-trip
  - Cell sa None page → Evidence bez page
  - Cell sa sheet, row, col → Locator sa sheet, row, col
  - TYPE_CHECKING import (test da cell_compat radi bez runtime import-a core/)

Unit (postojeći):
- tests/unit/test_contract.py — ostaje
- tests/unit/test_excel_document.py — ostaje (koristi legacy Cell)
- tests/unit/test_excel_headers_engine.py — ostaje
- ... svi ostali

Integration:    nijedan u A2
Architecture:   opcioni (tests/architecture/test_import_boundaries.py)
```

---

## Impact analysis required (Graft SECONDARY period)

```text
[Da] MEDIUM/HIGH risk

Simboli za praćenje:
- parser_studio.domain.evidence (top-level module)
- parser_studio.domain.evidence.locator.Locator
- parser_studio.domain.evidence.evidence.Evidence
- parser_studio.domain.evidence.document_evidence.DocumentEvidence
- parser_studio.domain.evidence.candidate.Candidate
- parser_studio.domain.evidence.extraction_context.ExtractionContext
- parser_studio.domain.evidence.cell_compat.cell_to_evidence

Legacy simboli za provjeru (TYPE_CHECKING import mora biti vidljiv):
- core.documents.base.Cell
- core.documents.base.ExtractionTable
- core.documents.base.Document

Alati:
- graft build                 # reindeksiranje
- graft grep "Cell"           # Cell korisnici (vidi legacy impact)
- graft grep "Evidence"       # novi Evidence korisnici
- graft blast                 # diff working tree vs HEAD
- ručni grep fallback za .md i neindeksirane
```

**"Zero callers" NIJE dovoljno** (potvrđeno na `Cell`). Graft `callers` + `grep` zajedno.

---

## Risks

```text
1. TYPE_CHECKING import u cell_compat.py mora biti pažljivo dizajniran
   da NE kreira runtime cikličnu zavisnost.
   Mitigacija: TYPE_CHECKING import je isključivo za type hints;
               stvarni `Cell` parametar prolazi kroz duck typing.

2. `slots=True` na dataclass može biti problem ako neka klasa treba
   nasljeđivanje ili `__dict__` iz drugog razloga.
   Mitigacija: sve klase u A2 su leaf klase (bez nasljeđivanja).

3. `bbox: tuple[float, float, float, float] | None` zahtijeva
   striktno 4 vrijednosti; testirati edge cases.

4. Pytest može prijaviti "module not found" ako pythonpath nije
   podešen za tests/unit/domain/.
   Mitigacija: pythonpath = ["src", "."] već konfigurisan u A1.

5. `from core.documents.base import Cell` kao TYPE_CHECKING može
   linterima (mypy, ruff) prijaviti kao "unused import" ili
   "import-outside-top-level" warning.
   Mitigacija: koristiti `as_completed` pattern ili
               `# noqa: TC001` za TYPE_CHECKING block.

6. Domain import test (`from parser_studio.domain.evidence import ...`)
   može fail-ovati ako `parser_studio` paket nije instaliran
   (`pip install -e .`).
   Mitigacija: A1 je već dodao [tool.setuptools.packages.find] where = ["src"];
               package bi trebao biti vidljiv nakon `pip install -e .`
               ILI kroz pythonpath u pytest.
```

---

## Execution evidence required

Implementer mora dostaviti:

```text
[ ] git diff --stat base..HEAD (samo novi fajlovi u src/ i tests/)
[ ] python -m pytest -q stvarni izlaz
[ ] python -m ruff check . stvarni izlaz
[ ] python -m contract.drift_check "$DEKLARANT_PRO_ROOT" stvarni izlaz
[ ] python -c "from parser_studio.domain.evidence import Locator, Evidence, DocumentEvidence, Candidate, ExtractionContext, cell_to_evidence" stvarni izlaz
[ ] graft build output
[ ] graft blast output
[ ] File:line dokaz za svaku tvrdnju o izolaciji domain-a od infrastrukture
```

**Self-reported "PASS" bez stvarnog izlaza nije prihvatljiv.**

---

## Reviewer evidence

Reviewer:

```text
[ ] vlastiti git diff review
[ ] vlastiti pytest -q reprodukcija
[ ] vlastiti ruff reprodukcija
[ ] vlastiti import sanity provjera
[ ] provjera architecture granica (grep za sqlite3/openpyxl/xlrd/PySide6/docling/contract u domain/)
[ ] provjera frozen + slots (pokušaj mutacije u REPL)
[ ] R-001 ... nalazi
[ ] konačni verdict
```

---

## Integration gate

```text
[ ] Implementer != Reviewer
[ ] Svi acceptance criteria zadovoljeni
[ ] CURRENT_STATE.md A2 status DONE
[ ] nema stvarnih faktura / poslovnih podataka u Git diffu
[ ] nema secret / token podataka u Git diffu
[ ] Post-merge integration gate: ponoviti pytest + ruff
```

---

## Definition of Done — A2

```text
[ ] src/parser_studio/domain/evidence/ sa 7 fajlova (6 modela + cell_compat)
[ ] tests/unit/domain/evidence/ sa 6 test fajlova
[ ] Sve klase frozen=True, slots=True
[ ] cell_to_evidence round-trip bez gubitka
[ ] Domain NE importuje zabranjene module
[ ] pytest ista ili bolja statistika
[ ] ruff ne gore od baseline
[ ] contract drift PASS
[ ] Graft blast čist
[ ] CURRENT_STATE A2: DONE
[ ] commit + push
```

---

## Notes

- A2 je **value object sloj**, NE business logika.
- Legacy `core/` ostaje netaknut. Migracija ide u A3 (Excel adapter) i A4 (ukloniti Engine).
- Ako se tokom A2 otkrije da treba dirati `core/documents/base.py`, zaustaviti i prijaviti kao `OUT_OF_SCOPE_FINDING`.

---

## Final status

```text
[ ] DRAFT
[ ] ACTIVE
[ ] REVIEW
[ ] DONE
[ ] CANCELLED
```

---

## OUT_OF_SCOPE_FINDING (popunjava implementer)

```text
(navesti ako postoji)
```

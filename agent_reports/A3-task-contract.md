---
task_id: A3
title: "Excel document adapter — DocumentReader port + ExcelDocumentReader implementacija"
status: ACTIVE
risk: MEDIUM-HIGH
date: 2026-09-14
branch: dev (base)
worktree: TBD
---

# A3 — Excel document adapter (port + implementacija)

> Premjestiti postojeći Excel I/O iz `core/documents/excel_document.py` u novi adapter iza `DocumentReader` porta. Legacy `core/` ostaje netaknut (migracija u A7). Svi postojeći testovi i dalje rade.

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
docs/PLAN.md                                  (V3, sekcija 6: package struktura; sekcija 16.1: Excel; sekcija 41: A3; sekcija 9: Document adapteri)
.agent/PROJECT_MAP.md                         (sekcija B: adapters; sekcija C: MIGRATION MAP)
.agent/TASK_ROUTING.md                        (sekcija "Excel")
core/documents/excel_document.py              (ExcelDocument — IZVORNI KOD ZA MIGRACIJU)
core/documents/base.py                        (Cell, ExtractionTable — koristi se u ExcelDocument)
src/parser_studio/domain/evidence/             (A2: Evidence modeli — output adaptera)
agent_reports/2026-09-14-graft-evaluation.md  (Graft SECONDARY pravila)
```

---

## Current-state preconditions

```text
[ ] branch: dev na c1a07d6 (A2 commit)
[ ] A2 acceptance DONE — Evidence modeli u src/parser_studio/domain/evidence/
[ ] A1 acceptance DONE — src/parser_studio/ skelet
[ ] Graft status: SECONDARY (probacioni period)
[ ] baseline testovi: 180 PASS + 41 novi = 221 PASS, 1 FAIL (test_f9)
[ ] ruff: 158 errors
[ ] contract drift: PASS
[ ] DEKLARANT_PRO_ROOT: H:/deklarant_pro
```

A3 može krenuti.

---

## Problem

V3 sekcija 9 zahtijeva `DocumentReader` port:

```python
class DocumentReader(Protocol):
    reader_id: str

    def supports(self, path: Path) -> bool:
        ...

    def read(self, path: Path) -> DocumentEvidence:
        ...
```

A3 iz V3 sekcija 41:
- "Premjestiti postojeći Excel I/O u adapter"
- Target: `adapters/documents/excel_reader.py`
- Zadaci: zadržati `.xlsx/.xls`, keširanje, sve sheetove; implementirati DocumentReader; prilagoditi testove
- Acceptance: Svi postojeći ExcelDocument testovi PASS

Trenutno stanje:
- `core/documents/excel_document.py` ima `ExcelDocument` klasu (dobar adapter prema V3 sekcija 2.2)
- Ali `ExcelDocument` JE ADAPTER koji živi u `core/documents/` — krši V3 sekcija 7 (adapters zavise prema unutra)
- Testovi u `tests/unit/test_excel_document.py` koriste `ExcelDocument` iz `core/`
- Novi `DocumentReader` port NE POSTOJI

---

## Goal

Kreirati `DocumentReader` Protocol + `ExcelDocumentReader` adapter koji čita `.xlsx/.xls` i proizvodi `DocumentEvidence` (A2 model).

Legacy `core/documents/excel_document.py` OSTAJE netaknut (koristi se u legacy testovima, legacy `Engine` ekstrakcija u `core/engines/`). Migracija legacy koda u novi adapter je u A7 (cleanup).

Acceptance:
- Novi `DocumentReader` port sa 2 metode (supports, read)
- Novi `ExcelDocumentReader` adapter (.xlsx/.xls podrška, keširanje, svi sheetovi, DocumentEvidence output)
- 5+ unit testova za novi adapter
- pytest: NE SMIJE imati više od 1 FAIL (test_f9 pre-existing)
- ruff: NE SMIJE imati značajno više grešaka
- contract drift: PASS
- Legacy `tests/unit/test_excel_document.py` i dalje PASS (core/ nije diran)

---

## In scope

### Novi fajlovi

```text
src/parser_studio/ports/
    document_reader.py          # DocumentReader Protocol + (opciono) DocumentReaderRegistry

src/parser_studio/adapters/
    documents/
        __init__.py
        excel_reader.py         # ExcelDocumentReader implementacija
        excel_cache.py          # (opciono) Cache helper ako je kompleksan

tests/unit/adapters/
    __init__.py
    documents/
        __init__.py
        test_excel_reader.py    # unit testovi za ExcelDocumentReader
```

### DocumentReader Protocol specifikacija

```python
# src/parser_studio/ports/document_reader.py
from __future__ import annotations
from pathlib import Path
from typing import Protocol

from parser_studio.domain.evidence import DocumentEvidence


class DocumentReader(Protocol):
    """Cita izvorni dokument i proizvodi DocumentEvidence."""

    reader_id: str

    def supports(self, path: Path) -> bool:
        """Da li ovaj reader moze citati dati fajl?"""
        ...

    def read(self, path: Path) -> DocumentEvidence:
        """Procitaj fajl i vrati DocumentEvidence sa cell/text/page evidence."""
        ...
```

### ExcelDocumentReader specifikacija

```python
# src/parser_studio/adapters/documents/excel_reader.py
from __future__ import annotations
from pathlib import Path

from openpyxl import load_workbook  # type: ignore[import-not-found]
import xlrd  # type: ignore[import-not-found]

from parser_studio.domain.evidence import DocumentEvidence, Evidence, Locator
from parser_studio.ports.document_reader import DocumentReader


class ExcelDocumentReader:
    """Cita .xlsx/.xls i proizvodi DocumentEvidence."""

    reader_id: str = "excel"

    def __init__(self) -> None:
        self._cache: dict[str, DocumentEvidence] = {}

    def supports(self, path: Path) -> bool:
        suffix = path.suffix.lower()
        return suffix in (".xlsx", ".xls")

    def read(self, path: Path) -> DocumentEvidence:
        if str(path) in self._cache:
            return self._cache[str(path)]
        suffix = path.suffix.lower()
        if suffix == ".xlsx":
            doc = self._read_xlsx(path)
        elif suffix == ".xls":
            doc = self._read_xls(path)
        else:
            raise ValueError(f"Nepodržani format: {suffix}")
        self._cache[str(path)] = doc
        return doc

    def _read_xlsx(self, path: Path) -> DocumentEvidence:
        wb = load_workbook(str(path), data_only=True, read_only=True)
        cells: list[Evidence] = []
        page_dimensions: dict[int, tuple[float, float]] = {}
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            for row in ws.iter_rows():
                for cell in row:
                    if cell.value is None:
                        continue
                    locator = Locator(
                        source_path=str(path),
                        kind="excel",
                        sheet=sheet_name,
                        row=cell.row,
                        col=cell.column,
                    )
                    raw_text = str(cell.value).strip()
                    evidence = Evidence(
                        raw_value=cell.value,
                        raw_text=raw_text,
                        locator=locator,
                        element_type="excel_cell",
                        source_id=self.reader_id,
                    )
                    cells.append(evidence)
            page_dimensions[hash(sheet_name) % 1000] = (1024.0, 768.0)  # placeholder
        return DocumentEvidence(
            document_id=str(path),
            source_path=str(path),
            pages=list(wb.sheetnames),
            cells=cells,
            page_dimensions=page_dimensions if page_dimensions else None,
        )

    def _read_xls(self, path: Path) -> DocumentEvidence:
        # Slicna logika sa xlrd; format detection za starije .xls
        ...
```

### Agent-friendly headers

Novi fajlovi počinju kratkim headerom (2-5 linija):

```python
# Adapter: ExcelDocumentReader.
# Posjeduje: cita .xlsx/.xls, kesiranje, DocumentEvidence output.
# Ne zna za: SQLite, PySide6, Docling, contract.
```

### Unit testovi

```text
tests/unit/adapters/documents/test_excel_reader.py
```

Testovi trebaju pokrivati:
- Konstrukcija (reader_id="excel")
- `supports()` za .xlsx, .xls, .csv, .pdf, nepostojeci fajl
- `read()` za .xlsx sa više sheetova, više redova, praznim celijama
- Keširanje (isti path vraca isti DocumentEvidence)
- Različiti formati ne miješaju
- Error handling za nepostojeci fajl, nevalidan format
- DocumentEvidence sadrzi sve celije sa ispravnim Locator (sheet, row, col)

---

## Out of scope

Sljedeće je EKSPLICITNO van A3:

```text
- Migracija legacy ExcelDocument iz core/documents/excel_document.py da koristi novi adapter
- Migracija legacy core/engines/excel_headers.py (A4: CandidateProducer)
- Ukinuti Engine koncept (A4)
- Application use case-ovi (A5)
- LearningRepository (A6)
- Presentation migracija (A7)
- Docling adapter (FAZA B / M3)
- Review GUI (FAZA B / M4)
- AI Advisor (FAZA G)
- Codegen (FAZA H)
- Verifier (FAZA I)
- Uklanjanje legacy core/documents/excel_document.py (A7 cleanup)
- Migracija tests/unit/test_excel_document.py (legacy testovi i dalje koriste core/)
- Architecture test (opcioni; može u A3 acceptance ili A7)
- Fix test_f9_no_broken_rows regression
- Cleanup 158 ruff grešaka
- Uklanjanje cryptography iz pyproject.toml
```

Ako implementer pronađe nešto izvan scope-a:

```text
OUT_OF_SCOPE_FINDING:
<opis>
<zašto je izvan scope-a>
<prijedlog kako riješiti>
```

---

## Expected files

```text
Novi:
- src/parser_studio/ports/document_reader.py
- src/parser_studio/adapters/documents/__init__.py
- src/parser_studio/adapters/documents/excel_reader.py
- tests/unit/adapters/__init__.py
- tests/unit/adapters/documents/__init__.py
- tests/unit/adapters/documents/test_excel_reader.py

Izmijenjeni:    nijedan (core/ i legacy testovi netaknuti)
Obrisani:        nijedan
Premješteni:    nijedan
```

---

## Architecture boundaries

A3 NE SMIJE probiti:

```text
[ ] domain/ → adapters/ (smjer: domain NE ZAVISI od adapters)
[ ] ports/ → adapters/ (smjer: ports NE ZAVISI od adapters)
[ ] adapters/documents/ → presentation/ (smjer: adapters NE ZAVISI od presentation)
[ ] adapters/documents/ → contract/ (V3 DEP-002: adapter moze importovati contract)
[ ] adapters/documents/excel_reader.py → core/ (NE SMIJE — adapter je nov kod, ne ovisi o legacy)
```

**Dozvoljeno:**
- `adapters/documents/excel_reader.py` može importovati `openpyxl`, `xlrd` (konkretna tehnologija)
- `adapters/documents/excel_reader.py` može importovati `parser_studio.domain.evidence.*` (output adaptera)
- `adapters/documents/excel_reader.py` može importovati `parser_studio.ports.document_reader` (implementira port)
- `adapters/documents/excel_reader.py` NE SMIJE importovati `core.*` (legacy izolacija)

---

## Compatibility requirements

```text
[ ] Svi postojeći testovi i dalje rade (ista PASS/SKIP statistika)
[ ] Svi legacy importi iz core/ i dalje rade
[ ] NEMA promjene legacy koda (core/, cli/, services/, views/, viewmodels/)
[ ] NEMA promjene legacy testova (tests/unit/test_excel_document.py, test_excel_headers_engine.py)
[ ] NEMA parallel "core/" + "src/" business koda osim novog adaptera
```

---

## Acceptance criteria

```text
[ ] src/parser_studio/ports/document_reader.py sa DocumentReader Protocol
[ ] src/parser_studio/adapters/documents/excel_reader.py sa ExcelDocumentReader
[ ] tests/unit/adapters/documents/test_excel_reader.py sa 5+ testova
[ ] ExcelDocumentReader podrzava .xlsx (openpyxl) i .xls (xlrd)
[ ] ExcelDocumentReader kesira rezultat po path-u
[ ] ExcelDocumentReader cita sve sheetove i celije
[ ] output je DocumentEvidence sa cell Evidence listom
[ ] pytest -q ista ili bolja statistika (max 1 FAIL = test_f9 pre-existing)
[ ] ruff ne značajno gore od baseline (158)
[ ] contract drift PASS
[ ] python -c "from parser_studio.adapters.documents.excel_reader import ExcelDocumentReader" OK
[ ] python -c "from parser_studio.ports.document_reader import DocumentReader" OK
[ ] Graft blast: nema false "impacted dependents" izvan ovih 6 fajlova
[ ] CURRENT_STATE A3 status DONE
[ ] Commit + push na dev
```

---

## Required tests

```text
Unit (novi):
- tests/unit/adapters/documents/test_excel_reader.py
  - konstrukcija (reader_id="excel")
  - supports: .xlsx, .xls, .csv, .pdf, nepostojeci
  - read: .xlsx sa vise sheetova
  - read: .xlsx sa praznim celijama (preskocene)
  - read: .xlsx sa multiline vrijednostima
  - kesiranje (isti path vraca isti DocumentEvidence ID)
  - razliciti formati (.xlsx vs .xls) — pojednostaviti za MVP
  - error: nepostojeci fajl
  - error: nevalidan format (.txt umjesto .xlsx)

Unit (postojeći, ne diraju se):
- tests/unit/test_excel_document.py (legacy, koristi core/)
- tests/unit/test_excel_headers_engine.py (legacy, koristi core/)
- tests/unit/test_contract.py
- tests/unit/test_quality_gate.py (1 FAIL prihvatljivo)
- ... svi ostali

Integration:    nijedan u A3
Architecture:   opcioni (tests/architecture/test_import_boundaries.py)
```

---

## Impact analysis required (Graft SECONDARY period)

```text
[Da] MEDIUM risk

Simboli za praćenje:
- parser_studio.ports.document_reader.DocumentReader
- parser_studio.adapters.documents.excel_reader.ExcelDocumentReader

Legacy simboli (NE SMIJU se mijenjati ali treba provjeriti cross-references):
- core.documents.excel_document.ExcelDocument
- core.documents.base.Cell
- core.documents.base.ExtractionTable

Alati:
- graft build                 # reindeksiranje
- graft grep "ExcelDocument" # cross-reference na legacy
- graft grep "DocumentReader" # novi port
- graft blast                 # diff working tree vs HEAD
- ručni grep fallback za .md i neindeksirane
```

**"Zero callers" NIJE dovoljno** (potvrđeno na `Cell`). Graft `callers` + `grep` zajedno.

---

## Risks

```text
1. openpyxl i xlrd API-ji se razlikuju izmedju verzija.
   Mitigacija: koristiti minimalan API surface; testirati sa oba formata.

2. Keširanje može zauzeti mnogo memorije za velike .xlsx fajlove.
   Mitigacija: u A3 koristiti jednostavan dict cache; u A5 evaluirati
               potrebu za LRU cacheom.

3. .xls (stari format) je kompleksan za parsiranje sa xlrd.
   Mitigacija: A3 podrzava .xls kao "best effort"; testovi samo za .xlsx;
               .xls ostaje u scope-u za buduće iteracije.

4. DocumentEvidence.pages ocekuje list[Any]; sheets su stringovi.
   Mitigacija: pages = list(wb.sheetnames) cast na list[Any].

5. xlrd 2.0+ NE podrzava .xlsx (samo .xls).
   Mitigacija: koristiti openpyxl za .xlsx, xlrd samo za .xls.

6. Legacy test_excel_document.py testira ExcelDocument iz core/.
   Ako A3 mijenja core/ (ne bi trebalo), legacy testovi padaju.
   Mitigacija: A3 NE SMIJE dirati core/. Ako treba, prijaviti.
```

---

## Execution evidence required

```text
[ ] git diff --stat base..HEAD (samo novi fajlovi)
[ ] python -m pytest -q stvarni izlaz
[ ] python -m ruff check . stvarni izlaz
[ ] python -m contract.drift_check "$DEKLARANT_PRO_ROOT" stvarni izlaz
[ ] python -c "from parser_studio.ports.document_reader import DocumentReader" OK
[ ] python -c "from parser_studio.adapters.documents.excel_reader import ExcelDocumentReader" OK
[ ] python -c "from parser_studio.adapters.documents.excel_reader import ExcelDocumentReader; r = ExcelDocumentReader(); print(r.supports.__doc__)" OK
[ ] graft build output
[ ] graft blast output
[ ] File:line dokaz za legacy netaknutost (git diff core/)
```

---

## Reviewer evidence

```text
[ ] vlastiti git diff review
[ ] vlastiti pytest -q reprodukcija
[ ] vlastiti ruff reprodukcija
[ ] vlastiti import sanity provjera
[ ] provjera da legacy core/ NIJE DIRAN (git diff core/)
[ ] provjera da DocumentReader Protocol ima supports() i read()
[ ] provjera da ExcelDocumentReader.produces DocumentEvidence (ne legacy Cell/ExtractionTable)
[ ] provjera kesiranja (isti path vraca isti ID)
[ ] R-001 ... nalazi
```

---

## Integration gate

```text
[ ] Implementer != Reviewer
[ ] Svi acceptance criteria zadovoljeni
[ ] CURRENT_STATE.md A3 status DONE
[ ] nema stvarnih faktura / poslovnih podataka u Git diffu
[ ] nema secret / token podataka u Git diffu
[ ] Post-merge integration gate: ponoviti pytest + ruff + drift
```

---

## Definition of Done — A3

```text
[ ] DocumentReader port kreiran
[ ] ExcelDocumentReader adapter kreiran
[ ] .xlsx podrzan (openpyxl)
[ ] .xls podrzan (xlrd, best effort)
[ ] Kesiranje funkcionise
[ ] DocumentEvidence output sa cell Evidence listom
[ ] 5+ unit testova PASS
[ ] pytest ista ili bolja statistika
[ ] ruff ne značajno gore
[ ] contract drift PASS
[ ] Graft blast čist
[ ] CURRENT_STATE A3: DONE
[ ] commit + push
```

---

## Notes

- A3 je **port + adapter** za Excel. Legacy `core/` ostaje netaknut.
- Migracija legacy koda u novi adapter ide u A7 (cleanup).
- Ako se tokom A3 otkrije da treba dirati `core/documents/excel_document.py`, zaustaviti i prijaviti kao `OUT_OF_SCOPE_FINDING`.

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

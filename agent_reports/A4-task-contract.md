---
task_id: A4
title: "CandidateProducer Protocol + migracija ExcelHeadersEngine na 4 modula + ukidanje Engine koncepta"
status: ACTIVE
risk: MEDIUM-HIGH
date: 2026-09-14
branch: dev (base)
worktree: TBD
---

# A4 — CandidateProducer + ukidanje Engine koncepta

> Uvesti `CandidateProducer` Protocol, migrirati `ExcelHeadersEngine` na 4 nova modula, ukinuti `Engine` koncept iz `core/engines/base.py`. Legacy `core/engines/excel_headers.py` ostaje netaknut do A7 (cleanup).

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
docs/PLAN.md                                  (V3, sekcija 9: CandidateProducer; sekcija 10: ExcelHeadersEngine dijeli se; sekcija 41: A4)
.agent/PROJECT_MAP.md                         (sekcija C: MIGRATION MAP za core/engines/*)
.agent/TASK_ROUTING.md                        (sekcija "Application / Use Case")
core/engines/base.py                          (Engine Protocol — UKIDANJE)
core/engines/excel_headers.py                 (ExcelHeadersEngine — IZVORNI KOD)
core/documents/excel_document.py              (Sheet, ExcelDocument — zavisi od ovoga)
core/engines/                  LEGACY
src/parser_studio/domain/evidence/             (A2: Evidence modeli — Producer output)
src/parser_studio/ports/document_reader.py    (A3: DocumentReader)
agent_reports/2026-09-14-graft-evaluation.md  (Graft SECONDARY pravila)
```

---

## Current-state preconditions

```text
[ ] branch: dev na 36218cf (A3 cleanup)
[ ] A3 acceptance DONE — DocumentReader port + ExcelDocumentReader
[ ] A2 acceptance DONE — Evidence modeli
[ ] A1 acceptance DONE — src/parser_studio/ skelet
[ ] Graft status: SECONDARY (probacioni period)
[ ] baseline testovi: 237 PASS + 1 FAIL (test_f9 pre-existing)
[ ] ruff: 162 errors
[ ] contract drift: PASS
[ ] DEKLARANT_PRO_ROOT: H:/deklarant_pro
```

A4 može krenuti.

---

## Problem

V3 sekcija 9 zahtijeva `CandidateProducer` Protocol:

```python
class CandidateProducer(Protocol):
    producer_id: str
    def propose(self, document: DocumentEvidence, context: FieldContext) -> list[Candidate]:
        ...
```

V3 sekcija 10 specificira podjelu `ExcelHeadersEngine`:

```text
core/engines/excel_headers.py
    → domain/invoice/fields.py (COLUMN_ALIASES konstanta)
    → domain/extraction/header_matching.py (normalize_header, _match_score, identify_columns)
    → application/extraction/producers/excel_header.py (find_header_row, footer, orchestration)
```

V3 A4:
- "Ukinuti Engine koncept, uvesti CandidateProducer"
- "definirati Protocol"
- "kreirati 4 nova modula"
- "zadržati 30 aliasa"
- "zadržati header/footer logiku"
- Acceptance: Svi postojeći testovi PASS

Trenutno stanje:
- `core/engines/base.py` ima `Engine` Protocol (zastario)
- `core/engines/excel_headers.py` ima `ExcelHeadersEngine` (najvrjedniji legacy kod, ~30+ COLUMN_ALIASES)
- `core/engines/__init__.py` (prazan)
- `core/engines/` je zastario, treba ga transformisati u novu strukturu

---

## Goal

Kreirati novu strukturu prema V3:
1. `CandidateProducer` Protocol u `src/parser_studio/ports/`
2. `domain/invoice/fields.py` sa COLUMN_ALIASES
3. `domain/extraction/header_matching.py` sa normalize_header, _match_score, identify_columns
4. `application/extraction/producers/excel_header.py` sa find_header_row, footer, orchestration
5. Novi testovi za svaki modul
6. Legacy `core/engines/excel_headers.py` ostaje netaknut (migracija u A7)

Acceptance:
- 4 nova modula sa jasnom podjelom odgovornosti
- 30+ aliasa sačuvano u `domain/invoice/fields.py`
- `find_header_row`, `normalize_header`, `identify_columns` funkcije sa istim ponašanjem
- `CandidateProducer` Protocol sa `propose()` metodom
- Unit testovi za svaki novi modul
- pytest NE SMIJE imati više od 1 FAIL
- ruff NE SMIJE imati značajno više grešaka
- contract drift PASS
- Legacy `core/engines/excel_headers.py` i `core/engines/base.py` netaknuti

---

## In scope

### Novi fajlovi

```text
src/parser_studio/ports/
    candidate_producer.py     # CandidateProducer Protocol + FieldContext dataclass

src/parser_studio/domain/invoice/
    fields.py                # COLUMN_ALIASES konstanta + helper

src/parser_studio/domain/extraction/
    header_matching.py        # normalize_header, _match_score, identify_columns

src/parser_studio/application/extraction/
    producers/
        __init__.py
        excel_header.py       # ExcelHeaderProducer: implementira CandidateProducer
                              # find_header_row, footer logic, orchestration
```

### CandidateProducer Protocol specifikacija

```python
# src/parser_studio/ports/candidate_producer.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from parser_studio.domain.evidence import Candidate, DocumentEvidence


@dataclass(frozen=True, slots=True)
class FieldContext:
    """State za producer poziv."""
    document_id: str
    field: str
    language: str = "bs"
    profile_version: int | None = None


@runtime_checkable
class CandidateProducer(Protocol):
    """Predlaze kandidate vrijednosti za trazeno polje."""

    producer_id: str

    def supports(self, context: FieldContext) -> bool:
        """Da li ovaj producer moze obraditi dati context?"""
        ...

    def propose(
        self, document: DocumentEvidence, context: FieldContext
    ) -> list[Candidate]:
        """Propose kandidate za trazeno polje."""
        ...
```

### COLUMN_ALIASES specifikacija

```python
# src/parser_studio/domain/invoice/fields.py
from __future__ import annotations

# Mapira razne header nazive na canonical ime polja.
# Ovo je SRZ legacy ExcelHeadersEngine; cuva 30+ aliasa.
COLUMN_ALIASES: dict[str, str] = {
    # DESCRIPTION / NAZIV
    "description": "description",
    "opis": "description",
    "naziv": "description",
    "naziv artikla": "description",
    "naziv robe": "description",
    "item name": "description",
    "item": "description",
    "artikal": "description",
    "product": "description",
    "product name": "description",
    
    # QUANTITY
    "quantity": "quantity",
    "kolicina": "quantity",
    "količina": "quantity",
    "qty": "quantity",
    "kom": "quantity",
    "amount": "quantity",
    "kol": "quantity",
    
    # UNIT_PRICE
    "unit price": "unit_price",
    "cijena": "unit_price",
    "cijena jed": "unit_price",
    "cena": "unit_price",
    "cena jed": "unit_price",
    "price": "unit_price",
    "unit cost": "unit_price",
    
    # LINE_AMOUNT
    "amount": "line_amount",
    "iznos": "line_amount",
    "total": "line_amount",
    "ukupno": "line_amount",
    "vrijednost": "line_amount",
    "value": "line_amount",
    "line total": "line_amount",
    
    # TARIFF
    "tariff": "tariff",
    "tariff number": "tariff",
    "tarifni broj": "tariff",
    "tarifna oznaka": "tariff",
    "hs": "tariff",
    "hs code": "tariff",
    "carinska oznaka": "tariff",
    
    # ORIGIN
    "origin": "origin",
    "country": "origin",
    "country of origin": "origin",
    "zemlja": "origin",
    "zemlja porijekla": "origin",
    "porijeklo": "origin",
    
    # UNIT
    "unit": "unit",
    "jm": "unit",
    "jedinica mjere": "unit",
    "u.m.": "unit",
    "measure": "unit",
    
    # DISCOUNT
    "discount": "discount",
    "rabat": "discount",
    "popust": "discount",
    "%": "discount",
}
```

### header_matching specifikacija

```python
# src/parser_studio/domain/extraction/header_matching.py
from __future__ import annotations
import re
import unicodedata
from typing import Iterable

from parser_studio.domain.invoice.fields import COLUMN_ALIASES


def normalize_header(text: str) -> str:
    """NFKC + collapsed whitespace + case-insensitive lowercase."""
    if not text:
        return ""
    nfkc = unicodedata.normalize("NFKC", text)
    lower = nfkc.lower()
    collapsed = re.sub(r"\s+", " ", lower).strip()
    return collapsed


def match_score(header: str, alias: str) -> float:
    """Trenutno: exact match (normalized) = 1.0, inače 0.0.
    Bez fuzzy poklapanja (AI grounding pravilo)."""
    h = normalize_header(header)
    a = normalize_header(alias)
    return 1.0 if h == a else 0.0


def identify_columns(headers: Iterable[str]) -> dict[str, int]:
    """Mapira header -> canonical field name na osnovu COLUMN_ALIASES.
    Vraca dict: canonical_name -> column_index (0-based).
    """
    result: dict[str, int] = {}
    for idx, header in enumerate(headers):
        norm = normalize_header(header)
        if not norm:
            continue
        # Exact match (case-insensitive, NFKC)
        if norm in COLUMN_ALIASES:
            canonical = COLUMN_ALIASES[norm]
            result[canonical] = idx
    return result
```

### ExcelHeaderProducer specifikacija

```python
# src/parser_studio/application/extraction/producers/excel_header.py
from __future__ import annotations
from typing import Any

from parser_studio.domain.evidence import Candidate, DocumentEvidence, Evidence, Locator
from parser_studio.domain.extraction.header_matching import (
    identify_columns, normalize_header,
)
from parser_studio.ports.candidate_producer import (
    CandidateProducer, FieldContext,
)


class ExcelHeaderProducer:
    """Predlaze Candidate vrijednosti iz Excel sheet header-a."""

    producer_id: str = "excel_header"

    def supports(self, context: FieldContext) -> bool:
        return True  # Podrzava sva polja; specificnost ide kroz context

    def propose(
        self, document: DocumentEvidence, context: FieldContext
    ) -> list[Candidate]:
        """Pronadji header red, identificiraj kolone, vrati Candidate za trazeno polje."""
        # 1. Pronadji header red
        sheet = self._find_header_sheet(document)
        if sheet is None:
            return []
        header_row = self._find_header_row(sheet)
        if header_row is None:
            return []
        
        # 2. Identificiraj kolone
        column_map = identify_columns(header_row)
        if context.field not in column_map:
            return []
        col_idx = column_map[context.field]
        
        # 3. Vrati kandidate za sve redove ispod header-a
        candidates = []
        for row_idx, row_values in enumerate(sheet["rows"][1:], start=1):
            if col_idx >= len(row_values):
                continue
            value = row_values[col_idx]
            if value is None or value == "":
                continue
            locator = Locator(
                source_path=document.source_path,
                kind="excel",
                sheet=sheet["name"],
                row=row_idx,
                col=col_idx,
            )
            raw_text = str(value).strip()
            evidence_obj = Evidence(
                raw_value=value,
                raw_text=raw_text,
                locator=locator,
                element_type="excel_cell",
                source_id=self.producer_id,
            )
            candidate = Candidate(
                field=context.field,
                raw_value=value,
                normalized_value=raw_text,
                locator=locator,
                evidence=evidence_obj.evidence,
                producer_id=self.producer_id,
            )
            candidates.append(candidate)
        return candidates

    def _find_header_sheet(self, document: DocumentEvidence) -> dict[str, Any] | None:
        """Pronadji sheet koji izgleda kao items tabela.
        Za sada: prvi sheet sa vise od 3 redova i 'quantity' ili 'opis' u headeru."""
        for sheet_name in document.pages:
            rows = self._get_rows_for_sheet(document, sheet_name)
            if not rows:
                continue
            if self._find_header_row({"name": sheet_name, "rows": rows}) is not None:
                return {"name": sheet_name, "rows": rows}
        return None

    def _get_rows_for_sheet(
        self, document: DocumentEvidence, sheet_name: str
    ) -> list[list[Any]]:
        """Izvuci redove za dati sheet iz DocumentEvidence cells."""
        cells = [c for c in document.cells if c.locator.sheet == sheet_name]
        if not cells:
            return []
        # Grupisanje po row
        max_row = max(c.locator.row for c in cells)
        max_col = max(c.locator.col for c in cells)
        rows: list[list[Any]] = [[None for _ in range(max_col)] for _ in range(max_row)]
        for cell in cells:
            r = cell.locator.row - 1  # 0-based
            c = cell.locator.col - 1
            if 0 <= r < max_row and 0 <= c < max_col:
                rows[r][c] = cell.raw_value
        return rows

    def _find_header_row(self, sheet: dict[str, Any]) -> list[str] | None:
        """Pronadji prvi red koji sadrzi 2+ poznata alias-a."""
        # Ova logika kopira find_row_containing iz legacy ExcelHeadersEngine
        # Za MVP: pronadji prvi red sa 2+ poznata alias-a u bilo kojem COLUMN_ALIASES
        from parser_studio.domain.invoice.fields import COLUMN_ALIASES
        normalized_aliases = {normalize_header(a) for a in COLUMN_ALIASES}
        
        for row in sheet.get("rows", []):
            normalized_cells = [normalize_header(str(v) if v is not None else "") for v in row]
            matches = sum(1 for c in normalized_cells if c in normalized_aliases)
            if matches >= 2:
                return [str(v) if v is not None else "" for v in row]
        return None
```

### Unit testovi

```text
tests/unit/domain/invoice/
    test_fields.py             # COLUMN_ALIASES keys/values testovi

tests/unit/domain/extraction/
    test_header_matching.py    # normalize_header, match_score, identify_columns

tests/unit/application/extraction/producers/
    test_excel_header.py       # ExcelHeaderProducer unit testovi
```

---

## Out of scope

```text
- Migracija legacy core/engines/excel_headers.py da koristi novu strukturu (A7 cleanup)
- Ukinuti core/engines/base.py Engine Protocol fajl (A7 cleanup)
- Migracija legacy tests/test_excel_headers_engine.py (legacy ostaje)
- Application use case-ovi (A5)
- LearningRepository (A6)
- Presentation migracija (A7)
- Docling adapter (FAZA B / M3)
- Review GUI (FAZA B / M4)
- AI Advisor (FAZA G)
- Codegen (FAZA H)
- Verifier (FAZA I)
- Architecture test (opcioni; može u A7)
- Fix test_f9_no_broken_rows regression (benchmark cleanup)
- Cleanup 162+ ruff gresaka
- Uklanjanje cryptography iz pyproject.toml
- Fuzzy matching (AI grounding zabrana; samo exact normalized match)
```

Ako implementer pronađe OUT_OF_SCOPE_FINDING, dokumentovati u Task Contract.

---

## Expected files

```text
Novi:
- src/parser_studio/ports/candidate_producer.py
- src/parser_studio/domain/invoice/fields.py
- src/parser_studio/domain/extraction/header_matching.py
- src/parser_studio/application/extraction/producers/__init__.py
- src/parser_studio/application/extraction/producers/excel_header.py
- tests/unit/domain/invoice/__init__.py
- tests/unit/domain/invoice/test_fields.py
- tests/unit/domain/extraction/__init__.py
- tests/unit/domain/extraction/test_header_matching.py
- tests/unit/application/extraction/__init__.py
- tests/unit/application/extraction/producers/__init__.py
- tests/unit/application/extraction/producers/test_excel_header.py

Izmijenjeni:    nijedan (core/engines/ netaknut)
Obrisani:        nijedan
Premješteni:    nijedan
```

---

## Architecture boundaries

A4 NE SMIJE probiti:

```text
[ ] domain/invoice/ → adapters, presentation, SQLite, PySide6, Docling
[ ] domain/extraction/ → adapters, presentation
[ ] application/extraction/producers/ → presentation, SQLite
[ ] ports/candidate_producer.py → adapters, presentation
[ ] application/extraction/ → domain ili ports, NE adapters
[ ] adapter (nije A4 scope, ali implikacija): excel_header producer smije importovati openpyxl/xlrd (A5+ posao)
```

**Dozvoljeno:**
- `ports/candidate_producer.py` importuje `domain.evidence.*` (Protocol output types)
- `domain/invoice/fields.py` NE importuje ništa iz domain (samo data)
- `domain/extraction/header_matching.py` importuje `domain.invoice.fields`
- `application/extraction/producers/excel_header.py` importuje `domain.*` i `ports.*`

---

## Compatibility requirements

```text
[ ] Svi postojeći testovi i dalje rade (237 PASS + 1 FAIL = test_f9 pre-existing)
[ ] Svi legacy importi iz core/ i dalje rade
[ ] NEMA promjene legacy koda (core/, cli/, services/, views/, viewmodels/)
[ ] NEMA promjene legacy testova (tests/unit/test_excel_headers_engine.py, test_excel_document.py)
[ ] NEMA parallel "core/" + "src/" business koda
[ ] 30+ COLUMN_ALIASES iz legacy ExcelHeadersEngine sacuvani (ili poboljšani)
```

---

## Acceptance criteria

```text
[ ] 4 nova modula kreirana: ports/candidate_producer.py, domain/invoice/fields.py,
    domain/extraction/header_matching.py, application/extraction/producers/excel_header.py
[ ] 30+ COLUMN_ALIASES sacuvano
[ ] normalize_header koristi NFKC + collapsed whitespace + case-insensitive
[ ] identify_columns koristi exact match (NE fuzzy)
[ ] ExcelHeaderProducer implements CandidateProducer Protocol
[ ] ExcelHeaderProducer propose() vraca list[Candidate] za trazeno polje
[ ] 6+ unit testova (po 2+ za svaki modul)
[ ] pytest ista ili bolja statistika (max 1 FAIL = test_f9 pre-existing)
[ ] ruff ne značajno gore od baseline (162)
[ ] contract drift PASS
[ ] python -c "from parser_studio.ports.candidate_producer import CandidateProducer, FieldContext" OK
[ ] python -c "from parser_studio.domain.invoice.fields import COLUMN_ALIASES" OK
[ ] python -c "from parser_studio.application.extraction.producers.excel_header import ExcelHeaderProducer" OK
[ ] Graft blast: nema false "impacted dependents" izvan ovih 11 fajlova
[ ] CURRENT_STATE A4 status DONE
[ ] Commit + push na dev
```

---

## Required tests

```text
Unit (novi):
- tests/unit/domain/invoice/test_fields.py
  - COLUMN_ALIASES sadrzi DESCRIPTION, QUANTITY, UNIT_PRICE, LINE_AMOUNT, TARIFF, ORIGIN, UNIT
  - svaki alias je unique key
  - canonical values su lowercase

- tests/unit/domain/extraction/test_header_matching.py
  - normalize_header: NFKC (npr. "Količina" -> "kolicina", "Količ." -> "kolicina.")
  - normalize_header: collapsed whitespace ("Kolicina   robe" -> "kolicina robe")
  - normalize_header: case-insensitive
  - match_score: exact match = 1.0, inače 0.0
  - identify_columns: mapira poznate headere na canonical
  - identify_columns: nepoznati headeri se preskacu

- tests/unit/application/extraction/producers/test_excel_header.py
  - producer_id = "excel_header"
  - implements CandidateProducer Protocol
  - propose(): vraca praznu listu za dokument bez headera
  - propose(): vraca kandidate za poznato polje (npr. "quantity")
  - propose(): Locator ima sheet, row, col
  - propose(): Candidate evidence je smislen

Unit (postojeći, ne diraju se):
- tests/unit/test_excel_headers_engine.py (legacy)
- tests/unit/test_excel_document.py (legacy)
- ... svi ostali

Integration:    nijedan u A4
Architecture:   opcioni (tests/architecture/test_import_boundaries.py)
```

---

## Impact analysis required (Graft SECONDARY period)

```text
[Da] MEDIUM-HIGH risk

Simboli za praćenje (NOVI):
- parser_studio.ports.candidate_producer.CandidateProducer
- parser_studio.ports.candidate_producer.FieldContext
- parser_studio.domain.invoice.fields.COLUMN_ALIASES
- parser_studio.domain.extraction.header_matching.normalize_header
- parser_studio.domain.extraction.header_matching.match_score
- parser_studio.domain.extraction.header_matching.identify_columns
- parser_studio.application.extraction.producers.excel_header.ExcelHeaderProducer

Legacy simboli (NE SMIJU se mijenjati ali cross-reference):
- core.engines.base.Engine
- core.engines.excel_headers.ExcelHeadersEngine
- core.documents.excel_document.Sheet

Alati:
- graft build                 # reindeksiranje
- graft grep "Engine"         # cross-reference provjera
- graft grep "COLUMN_ALIASES" # alias koristenje
- graft blast                 # diff working tree vs HEAD
- ručni grep fallback
```

**"Zero callers" NIJE dovoljno** (potvrđeno na `Cell`).

---

## Risks

```text
1. COLUMN_ALIASES može imati razne case varijante ("Kolicina" vs "kolicina").
   Mitigacija: normalize_header primjenjuje NFKC + lowercase, pa match radi
               bez obzira na case.

2. ExcelHeaderProducer treba parsirati DocumentEvidence strukturu.
   Mitigacija: koristiti DocumentEvidence.cells sa Locator informacijom.

3. find_header_row logika je kompleksna; naslijeđena iz legacy koda.
   Mitigacija: pojednostaviti na "prvi red sa 2+ alias match" za MVP.

4. application/extraction/producers/ NE SMIJE importovati adapters (V3 DEP).
   Mitigacija: producer NE SMIJE importovati openpyxl/xlrd direktno;
               koristi DocumentEvidence koji je A2/A3 output.

5. Ako 30+ aliasa ima vise canonical -> alias mapiranja,
   to moze zbuniti identify_columns.
   Mitigacija: testirati sa stvarnim Excel dokumentima iz benchmarka
               (legacy test_excel_headers_engine.py testira ovu logiku).

6. NEMA fuzzy matching (AI zabrana).
   Mitigacija: match_score je binaran (0.0 ili 1.0); identify_columns
               koristi exact match. Future iteracije mogu dodati
               weighted match BEZ fuzzy.
```

---

## Execution evidence required

```text
[ ] git diff --stat base..HEAD (samo novi fajlovi)
[ ] python -m pytest -q stvarni izlaz
[ ] python -m ruff check . stvarni izlaz
[ ] python -m contract.drift_check "$DEKLARANT_PRO_ROOT" stvarni izlaz
[ ] python -c "from parser_studio.ports.candidate_producer import CandidateProducer, FieldContext" OK
[ ] python -c "from parser_studio.domain.invoice.fields import COLUMN_ALIASES" OK
[ ] python -c "from parser_studio.application.extraction.producers.excel_header import ExcelHeaderProducer" OK
[ ] graft build output
[ ] graft blast output
[ ] File:line dokaz za 30+ aliases
[ ] File:line dokaz za legacy netaknutost (git diff --stat core/)
```

---

## Reviewer evidence

```text
[ ] vlastiti git diff review
[ ] vlastiti pytest -q reprodukcija
[ ] vlastiti ruff reprodukcija
[ ] vlastiti import sanity provjera
[ ] provjera da legacy core/ NIJE DIRAN (git diff --stat core/)
[ ] provjera da CandidateProducer Protocol ima propose() i supports()
[ ] provjera da ExcelHeaderProducer implements Protocol
[ ] provjera 30+ COLUMN_ALIASES (count + sample)
[ ] provjera normalize_header (NFKC + collapsed + case-insensitive)
[ ] provjera identify_columns (exact match, NO fuzzy)
[ ] R-001 ... nalazi
```

---

## Integration gate

```text
[ ] Implementer != Reviewer
[ ] Svi acceptance criteria zadovoljeni
[ ] CURRENT_STATE.md A4 status DONE
[ ] nema stvarnih faktura / poslovnih podataka u Git diffu
[ ] nema secret / token podataka u Git diffu
[ ] Post-merge integration gate: ponoviti pytest + ruff + drift
```

---

## Definition of Done — A4

```text
[ ] CandidateProducer Protocol + FieldContext u src/parser_studio/ports/
[ ] 30+ COLUMN_ALIASES u src/parser_studio/domain/invoice/fields.py
[ ] normalize_header, match_score, identify_columns u src/parser_studio/domain/extraction/header_matching.py
[ ] ExcelHeaderProducer u src/parser_studio/application/extraction/producers/excel_header.py
[ ] 6+ unit testova
[ ] pytest ista ili bolja statistika
[ ] ruff ne značajno gore
[ ] contract drift PASS
[ ] Graft blast čist
[ ] CURRENT_STATE A4: DONE
[ ] commit + push
```

---

## Notes

- A4 je **PRVI ARHITEKTONSKI ZNAČAJAN** refaktor — dijeli legacy najvrjedniji kod.
- Legacy `core/engines/excel_headers.py` ostaje netaknut do A7.
- Ako se tokom A4 otkrije da treba dirati `core/engines/`, zaustaviti i prijaviti kao `OUT_OF_SCOPE_FINDING`.
- Ovaj task je dovoljno velik da se može podijeliti u A4.1 (Protocol + COLUMN_ALIASES + header_matching) i A4.2 (ExcelHeaderProducer). Ako želiš, mogu predložiti podjelu.

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

---

## Prijedlog podjele (opciona)

Ako želiš manje milestone-ove, mogu podijeliti:

```text
A4.1  Protocol + COLUMN_ALIASES + header_matching
      - src/parser_studio/ports/candidate_producer.py
      - src/parser_studio/domain/invoice/fields.py
      - src/parser_studio/domain/extraction/header_matching.py
      - 3 test fajla
      - Commit + push

A4.2  ExcelHeaderProducer + orchestration
      - src/parser_studio/application/extraction/producers/excel_header.py
      - 1 test fajl
      - Commit + push
```

Prednosti podjele:
- A4.1 je čist domain (testabilan bez DocumentEvidence)
- A4.2 zavisi od A4.1 + DocumentEvidence (A2/A3)
- Svaki commit je manji i lakše reverzibilan

Ako želiš podjelu, javi. Ako ne, implementiram kao jedan A4.

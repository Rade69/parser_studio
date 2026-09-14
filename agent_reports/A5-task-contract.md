---
task_id: A5
title: "Application use case-ovi — ImportDocument, AnalyzeInvoice, ConfirmInvoice"
status: DONE
risk: MEDIUM-HIGH
date: 2026-09-14
branch: dev (base)
worktree: TBD
---

# A5 — Application use case-ovi (skeleton + 3 MVP use case-a)

> Kreirati application use case-ovi prema V3 sekcija 19: `ImportDocument`, `AnalyzeInvoice`, `ConfirmInvoice`. Use case-ovi koordiniraju domain + ports, NE importuju adapters. Wiring u `bootstrap.py`.

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
docs/PLAN.md                                  (V3, sekcija 19: Application use case-ovi; sekcija 41: A5; sekcija 15: Application use case-ovi opis)
.agent/PROJECT_MAP.md                         (sekcija B: application)
.agent/TASK_ROUTING.md                        (sekcija "Application / Use Case")
src/parser_studio/domain/evidence/             (A2: Evidence modeli)
src/parser_studio/ports/document_reader.py    (A3: DocumentReader)
src/parser_studio/adapters/documents/excel_reader.py  (A3: ExcelDocumentReader)
src/parser_studio/ports/candidate_producer.py (A4: CandidateProducer)
src/parser_studio/application/extraction/producers/excel_header.py  (A4: ExcelHeaderProducer)
src/parser_studio/bootstrap.py                (composition root, A1: prazan)
agent_reports/2026-09-14-graft-evaluation.md  (Graft SECONDARY pravila)
```

---

## Current-state preconditions

```text
[ ] branch: dev na 3570f86 (A3/A4 cleanup)
[ ] A4 acceptance DONE — CandidateProducer Protocol + ExcelHeaderProducer
[ ] A3 acceptance DONE — DocumentReader port + ExcelDocumentReader
[ ] A2 acceptance DONE — Evidence modeli
[ ] A1 acceptance DONE — src/parser_studio/ skelet
[ ] Graft status: SECONDARY (probacioni period)
[ ] baseline testovi: 286 PASS + 1 FAIL (test_f9 pre-existing)
[ ] ruff: 170 errors
[ ] contract drift: PASS
[ ] DEKLARANT_PRO_ROOT: H:/deklarant_pro
```

A5 može krenuti.

---

## Problem

V3 sekcija 19 specificira use case-ove:

```text
- ImportDocument          cita fajl, vraca DocumentEvidence
- AnalyzeInvoice          pokreće Producer-e, agregira Candidate-e u ExtractionDraft
- ReviewInvoice           GUI koristi za prikaz ExtractionDraft
- ConfirmInvoice          korisnik potvrđuje vrijednosti, generiše LearningEvent
- BuildLayoutFingerprint  izracunava hash/layout signature
- BuildLayoutProfile      grupiše Gold podatke u Profile
- MatchLayoutProfile      nalazi najbolji Profile za dati dokument
- RecoverFieldOCR         ponovni OCR za polja koja nisu uspjela
- GenerateVendorParser    kreira standalone .py iz VendorParserModel
- VerifyVendorParser      pokreće generisani parser u subprocess, poredi sa Gold
- ExportVendorParser      izvoz parsera na disk (FAZA H/I)
```

Trenutno stanje:
- `src/parser_studio/bootstrap.py` je prazan (composition root)
- NEMA application use case-ova
- NEMA wiring između use case-ova i portova/adaptera
- Legacy `core/engines/` nema use case pattern (samo `ExcelHeadersEngine.probe/extract`)

---

## Goal

Kreirati minimum 3 use case-a za MVP:
1. `ImportDocument` — cita fajl preko DocumentReader, vraca DocumentEvidence
2. `AnalyzeInvoice` — pokreće ExcelHeaderProducer (i ostale producer-e), agregira Candidate-e u ExtractionDraft
3. `ConfirmInvoice` — korisnik potvrđuje vrijednosti (placeholder bez GUI), generiše LearningEvent

Plus:
- Wiring u `bootstrap.py`
- ExtractionDraft model u domain (za AnalyzeInvoice output)
- Unit testovi za svaki use case

Acceptance:
- 3 nova use case-a sa jasnim kontraktom (input/output dataclass)
- `bootstrap.py` sa wiring primjerom
- `ExtractionDraft` domain model
- 5+ unit testova
- pytest NE SMIJE imati više od 1 FAIL
- ruff NE SMIJE imati značajno više grešaka
- contract drift PASS
- Legacy `core/` netaknut

---

## In scope

### Novi fajlovi

```text
src/parser_studio/domain/extraction/
    extraction_draft.py    # ExtractionDraft dataclass

src/parser_studio/application/
    ingest/
        __init__.py
        import_document.py    # ImportDocument use case
    extraction/
        analyze_invoice.py    # AnalyzeInvoice use case
    review/
        confirm_invoice.py    # ConfirmInvoice use case
        __init__.py

tests/unit/application/
    ingest/
        __init__.py
        test_import_document.py
    extraction/
        test_analyze_invoice.py
    review/
        __init__.py
        test_confirm_invoice.py
```

Izmjene:
- `src/parser_studio/bootstrap.py` — dodati primjer wiring-a

### ExtractionDraft specifikacija

```python
# src/parser_studio/domain/extraction/extraction_draft.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from parser_studio.domain.evidence import Candidate, DocumentEvidence


@dataclass(frozen=True, slots=True)
class ExtractionDraft:
    """Rezultat AnalyzeInvoice: skup kandidata po polju."""
    document_id: str
    document: DocumentEvidence
    candidates_by_field: dict[str, tuple[Candidate, ...]] = field(default_factory=dict)
    conflicts: tuple[tuple[str, Candidate, Candidate], ...] = ()
    unresolved: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def candidates_for(self, field: str) -> tuple[Candidate, ...]:
        return self.candidates_by_field.get(field, ())
```

### ImportDocument specifikacija

```python
# src/parser_studio/application/ingest/import_document.py
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

from parser_studio.domain.evidence import DocumentEvidence
from parser_studio.ports.document_reader import DocumentReader


@dataclass(frozen=True, slots=True)
class ImportRequest:
    path: Path
    document_id: str | None = None


@dataclass(frozen=True, slots=True)
class ImportResult:
    document: DocumentEvidence
    reader_id: str


class ImportDocument:
    """Use case: cita izvorni dokument preko DocumentReader porta."""

    def __init__(self, readers: tuple[DocumentReader, ...]) -> None:
        if not readers:
            raise ValueError("ImportDocument zahtijeva bar jedan DocumentReader")
        self._readers = readers

    def execute(self, request: ImportRequest) -> ImportResult:
        for reader in self._readers:
            if reader.supports(request.path):
                document = reader.read(request.path)
                return ImportResult(
                    document=document,
                    reader_id=reader.reader_id,
                )
        raise ValueError(
            f"Nijedan DocumentReader ne podržava fajl: {request.path}"
        )
```

### AnalyzeInvoice specifikacija

```python
# src/parser_studio/application/extraction/analyze_invoice.py
from __future__ import annotations
from dataclasses import dataclass

from parser_studio.domain.evidence import Candidate, DocumentEvidence
from parser_studio.domain.extraction.extraction_draft import ExtractionDraft
from parser_studio.ports.candidate_producer import CandidateProducer, FieldContext


@dataclass(frozen=True, slots=True)
class AnalyzeRequest:
    document: DocumentEvidence
    target_fields: tuple[str, ...]
    language: str = "bs"


class AnalyzeInvoice:
    """Use case: pokreće Producer-e, agregira Candidate-e."""

    def __init__(
        self,
        producers: tuple[CandidateProducer, ...],
    ) -> None:
        if not producers:
            raise ValueError("AnalyzeInvoice zahtijeva bar jedan CandidateProducer")
        self._producers = producers

    def execute(self, request: AnalyzeRequest) -> ExtractionDraft:
        candidates_by_field: dict[str, list[Candidate]] = {}
        for producer in self._producers:
            for field in request.target_fields:
                ctx = FieldContext(
                    document_id=request.document.document_id,
                    field=field,
                    language=request.language,
                )
                if not producer.supports(ctx):
                    continue
                for cand in producer.propose(request.document, ctx):
                    candidates_by_field.setdefault(field, []).append(cand)
        # Konverzija u tuple radi frozen dataclass
        frozen = {f: tuple(cs) for f, cs in candidates_by_field.items()}
        return ExtractionDraft(
            document_id=request.document.document_id,
            document=request.document,
            candidates_by_field=frozen,
        )
```

### ConfirmInvoice specifikacija

```python
# src/parser_studio/application/review/confirm_invoice.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from parser_studio.domain.extraction.extraction_draft import ExtractionDraft
from parser_studio.domain.learning.learning_event import (
    LearningEvent, EventType,
)


@dataclass(frozen=True, slots=True)
class FieldConfirmation:
    field: str
    raw_value: Any
    normalized_value: Any
    locator: Any  # Locator
    confirmed: bool
    note: str = ""


@dataclass(frozen=True, slots=True)
class ConfirmRequest:
    draft: ExtractionDraft
    confirmations: tuple[FieldConfirmation, ...]
    actor: str  # user id (za learning events)


class ConfirmInvoice:
    """Use case: korisnik potvrđuje vrijednosti, generiše LearningEvent-ove.

    Za MVP: BEZ GUI; poziva se programski sa vec pripremljenim confirmations.
    Pravi GUI (FAZA B / M4) bude pozivao ovaj use case sa korisnickim inputom.
    """

    def __init__(self, learning_repo: Any) -> None:
        # learning_repo je port; A5 ne uvodi SQLite (A6 posao)
        # Za MVP koristimo Any / TYPE_CHECKING
        self._learning_repo = learning_repo

    def execute(self, request: ConfirmRequest) -> list[LearningEvent]:
        events: list[LearningEvent] = []
        for conf in request.confirmations:
            event = LearningEvent(
                document_id=request.draft.document_id,
                item_id=None,
                field_name=conf.field,
                event_type=EventType.USER_CONFIRMED,
                old_value=None,
                new_value=conf.normalized_value,
                locator=conf.locator,
                source=request.actor,
            )
            events.append(event)
            # MVP: NE pohranjuj u repo (A6)
            # if self._learning_repo is not None:
            #     self._learning_repo.append(event)
        return events
```

**NAPOMENA**: `ConfirmInvoice` koristi `LearningEvent` iz `src/parser_studio/domain/learning/`. To zahtijeva da se taj modul kreira u A5 (iako V3 stavlja u A6). Razlog: ConfirmInvoice contract zahtijeva LearningEvent kao output.

ALI — alternativno: `ConfirmInvoice` može samo vratiti `list[dict]` (plain dicts) u MVP, a A6 uvede LearningEvent. ALI to krši V3 contract.

**Odluka**: A5 kreira `LearningEvent` i `EventType` u `src/parser_studio/domain/learning/learning_event.py` (minimalno), ali NE implementira LearningRepository port (A6 posao). `ConfirmInvoice` VRAĆA `list[LearningEvent]` ali NE pohranjuje (poziva se samo na A6).

### LearningEvent specifikacija (A5 minimum)

```python
# src/parser_studio/domain/learning/learning_event.py
from __future__ import annotations
import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from parser_studio.domain.evidence.locator import Locator


class EventType(str, enum.Enum):
    """Tip learning event-a. Koristi str za JSON serijalizaciju."""
    OCR_EXTRACTED = "OCR_EXTRACTED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    USER_CORRECTED = "USER_CORRECTED"
    USER_VERIFIED = "USER_VERIFIED"
    USER_CONFIRMED = "USER_CONFIRMED"


@dataclass(frozen=True, slots=True)
class LearningEvent:
    """Append-only zapis promjene na dokumentu.
    Svaki event je jedna 'činjenica' koju parser smije zapamtiti.
    """
    document_id: str
    field_name: str
    event_type: EventType
    new_value: Any
    locator: Locator | None
    source: str  # ko je generisao (producer_id, "user:radovan", itd.)
    item_id: str | None = None
    old_value: Any = None
    note: str = ""
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        if not self.document_id:
            raise ValueError("document_id ne može biti prazan string")
        if not self.field_name:
            raise ValueError("field_name ne može biti prazan string")
        if not self.source:
            raise ValueError("source ne može biti prazan string")
```

### bootstrap.py izmjene (primjer wiring-a)

```python
# src/parser_studio/bootstrap.py (nadogradnja)
"""Parser Studio composition root.

Wiring između use case-ova, portova i adaptera.
"""
from __future__ import annotations

from parser_studio.adapters.documents.excel_reader import ExcelDocumentReader
from parser_studio.application.extraction.analyze_invoice import AnalyzeInvoice
from parser_studio.application.ingest.import_document import ImportDocument
from parser_studio.application.review.confirm_invoice import ConfirmInvoice
from parser_studio.application.extraction.producers.excel_header import (
    ExcelHeaderProducer,
)


def build_default_application() -> tuple[
    ImportDocument, AnalyzeInvoice, ConfirmInvoice,
]:
    """Kreiraj default aplikaciju sa svim raspolozivim portovima/adapterima."""
    excel_reader = ExcelDocumentReader()
    import_doc = ImportDocument(readers=(excel_reader,))

    excel_header_producer = ExcelHeaderProducer()
    analyze = AnalyzeInvoice(producers=(excel_header_producer,))

    # ConfirmInvoice bez LearningRepository (A6 ce dodati)
    confirm = ConfirmInvoice(learning_repo=None)

    return import_doc, analyze, confirm
```

### Unit testovi

```text
tests/unit/application/ingest/test_import_document.py
tests/unit/application/extraction/test_analyze_invoice.py
tests/unit/application/review/test_confirm_invoice.py
tests/unit/domain/learning/test_learning_event.py (novi)
```

---

## Out of scope

```text
- Implementacija LearningRepository port + SQLite adapter (A6)
- Use case-ovi BuildLayout*, MatchLayout*, RecoverFieldOCR, GenerateVendorParser, VerifyVendorParser, ExportVendorParser
- Review GUI / Annotation tool (FAZA B / M4)
- AI Advisor (FAZA G)
- Codegen, Verifier CLI (FAZA H/I/J)
- Migracija legacy core/engines/excel_headers.py (A7 cleanup)
- Migracija legacy core/documents/excel_document.py (A7 cleanup)
- Architecture test (opcioni; moze u A7)
- Fix test_f9_no_broken_rows regression (benchmark cleanup)
- Cleanup 170+ ruff gresaka
- Uklanjanje cryptography iz pyproject.toml
```

---

## Expected files

```text
Novi:
- src/parser_studio/domain/extraction/extraction_draft.py
- src/parser_studio/domain/learning/__init__.py
- src/parser_studio/domain/learning/learning_event.py
- src/parser_studio/application/ingest/__init__.py
- src/parser_studio/application/ingest/import_document.py
- src/parser_studio/application/extraction/__init__.py (vec postoji)
- src/parser_studio/application/extraction/analyze_invoice.py
- src/parser_studio/application/review/__init__.py
- src/parser_studio/application/review/confirm_invoice.py
- tests/unit/application/ingest/__init__.py
- tests/unit/application/ingest/test_import_document.py
- tests/unit/application/extraction/__init__.py (vec postoji)
- tests/unit/application/extraction/test_analyze_invoice.py
- tests/unit/application/review/__init__.py
- tests/unit/application/review/test_confirm_invoice.py
- tests/unit/domain/learning/__init__.py
- tests/unit/domain/learning/test_learning_event.py

Izmijenjeni:
- src/parser_studio/bootstrap.py (dodati build_default_application funkciju)

Obrisani:        nijedan
Premješteni:    nijedan
```

---

## Architecture boundaries

A5 NE SMIJE probiti:

```text
[ ] domain/ → application/, adapters/, presentation/
[ ] application/ → adapters/, presentation/
[ ] application/ingest/ → openpyxl/xlrd direktno (mora ici kroz DocumentReader port)
[ ] application/extraction/ → openpyxl/xlrd direktno (mora ici kroz DocumentReader port)
[ ] application/ → SQLite (A6)
[ ] ports/ → adapters/, presentation/
```

**Dozvoljeno:**
- `application/ingest/import_document.py` importuje `ports.document_reader.DocumentReader`
- `application/extraction/analyze_invoice.py` importuje `ports.candidate_producer.CandidateProducer`
- `application/review/confirm_invoice.py` importuje `domain.learning.learning_event.LearningEvent` (A5 minimum)
- `application/*` importuje `domain.*` (dozvoljeno, application ovisi o domain)

---

## Compatibility requirements

```text
[ ] Svi postojeći testovi i dalje rade (286 PASS + 1 FAIL = test_f9 pre-existing)
[ ] Svi legacy importi iz core/ i dalje rade
[ ] NEMA promjene legacy koda (core/, cli/, services/, views/, viewmodels/)
[ ] NEMA promjene legacy testova
[ ] NEMA parallel "core/" + "src/" business koda
[ ] LearningEvent NE implementira SQLite (A6)
```

---

## Acceptance criteria

```text
[ ] ExtractionDraft kreiran u src/parser_studio/domain/extraction/extraction_draft.py
[ ] LearningEvent + EventType kreiran u src/parser_studio/domain/learning/learning_event.py
[ ] ImportDocument use case u src/parser_studio/application/ingest/import_document.py
[ ] AnalyzeInvoice use case u src/parser_studio/application/extraction/analyze_invoice.py
[ ] ConfirmInvoice use case u src/parser_studio/application/review/confirm_invoice.py
[ ] bootstrap.py sa build_default_application funkcijom
[ ] 5+ unit testova (po 2+ za svaki use case + LearningEvent)
[ ] pytest ista ili bolja statistika (max 1 FAIL = test_f9 pre-existing)
[ ] ruff ne značajno gore od baseline (170)
[ ] contract drift PASS
[ ] python -c "from parser_studio.application.ingest.import_document import ImportDocument" OK
[ ] python -c "from parser_studio.application.extraction.analyze_invoice import AnalyzeInvoice" OK
[ ] python -c "from parser_studio.application.review.confirm_invoice import ConfirmInvoice" OK
[ ] python -c "from parser_studio.bootstrap import build_default_application" OK
[ ] Graft blast: nema false "impacted dependents" izvan ovih fajlova
[ ] CURRENT_STATE A5 status DONE
[ ] Commit + push na dev
```

---

## Required tests

```text
Unit (novi):
- tests/unit/domain/learning/test_learning_event.py
  - konstrukcija sa svim poljima
  - frozen provjera
  - EventType enum (USER_CONFIRMED, OCR_EXTRACTED, itd.)
  - default created_at = utcnow
  - validation (prazan document_id, field_name, source)

- tests/unit/application/ingest/test_import_document.py
  - ImportDocument.execute() sa .xlsx vraca ImportResult
  - ImportDocument.execute() baca ValueError za nepodrzan format
  - ImportDocument.execute() baca ValueError ako nema readera
  - ImportDocument.execute() koristi prvi reader koji supports() vraca True
  - ImportRequest default document_id

- tests/unit/application/extraction/test_analyze_invoice.py
  - AnalyzeInvoice.execute() za poznato polje vraca ExtractionDraft sa kandidatima
  - AnalyzeInvoice.execute() za nepoznato polje vraca prazan candidates_by_field
  - AnalyzeInvoice.execute() agregira kandidate iz vise producer-a (ako ih ima)
  - AnalyzeRequest.target_fields tuples

- tests/unit/application/review/test_confirm_invoice.py
  - ConfirmInvoice.execute() sa praznim confirmations vraca []
  - ConfirmInvoice.execute() sa 1 confirmation generise 1 LearningEvent
  - LearningEvent ima event_type=USER_CONFIRMED
  - ConfirmInvoice.execute() NE pohranjuje (za MVP, learning_repo=None)

Unit (postojeći):
- svi ostali testovi i dalje PASS

Integration:    nijedan u A5
Architecture:   opcioni
```

---

## Impact analysis required (Graft SECONDARY period)

```text
[Da] MEDIUM-HIGH risk

Simboli za praćenje (NOVI):
- parser_studio.application.ingest.import_document.ImportDocument
- parser_studio.application.ingest.import_document.ImportRequest
- parser_studio.application.ingest.import_document.ImportResult
- parser_studio.application.extraction.analyze_invoice.AnalyzeInvoice
- parser_studio.application.extraction.analyze_invoice.AnalyzeRequest
- parser_studio.application.review.confirm_invoice.ConfirmInvoice
- parser_studio.application.review.confirm_invoice.FieldConfirmation
- parser_studio.application.review.confirm_invoice.ConfirmRequest
- parser_studio.domain.extraction.extraction_draft.ExtractionDraft
- parser_studio.domain.learning.learning_event.LearningEvent
- parser_studio.domain.learning.learning_event.EventType
- parser_studio.bootstrap.build_default_application

Legacy simboli (NE SMIJU se mijenjati):
- core.engines.base.Engine
- core.engines.excel_headers.ExcelHeadersEngine
- core.documents.excel_document.ExcelDocument

Alati:
- graft build                 # reindeksiranje
- graft grep "ImportDocument" # novi use case
- graft grep "AnalyzeInvoice"
- graft grep "LearningEvent"
- graft blast                 # diff working tree vs HEAD
- ručni grep fallback
```

**"Zero callers" NIJE dovoljno.**

---

## Risks

```text
1. ConfirmInvoice ovisi o LearningEvent koji nije u V3 za A5 (V3 stavlja u A6).
   Mitigacija: kreirati minimalni LearningEvent u A5 (bez SQLite); A6 doda
               LearningRepository port i SQLite adapter.

2. Use case-ovi moraju biti testabilni bez adaptera.
   Mitigacija: koristiti TYPE_CHECKING za legacy, fake/mock readere za testove.

3. Application sloj NE SMIJE importovati openpyxl/xlrd.
   Mitigacija: application ovisi o DocumentReader port (A3), ne o
               openpyxl/xlrd direktno.

4. bootstrap.py kreira sve objekte; ali ciklicni importi su rizik.
   Mitigacija: bootstrap.py je jedini fajl koji uvozi SVE; ostali importuju
               samo sto im treba.

5. AnalyzeInvoice.execute() sa praznim producers baca ValueError.
   Mitigacija: eksplicitna provjera u __init__.

6. ConfirmInvoice.execute() za MVP NE pohranjuje u LearningRepository.
   Mitigacija: dokumentovati u Contract + Commit poruci da je storage A6.
```

---

## Execution evidence required

```text
[ ] git diff --stat base..HEAD (samo novi fajlovi + bootstrap.py izmjena)
[ ] python -m pytest -q stvarni izlaz
[ ] python -m ruff check . stvarni izlaz
[ ] python -m contract.drift_check "$DEKLARANT_PRO_ROOT" stvarni izlaz
[ ] python -c "from parser_studio.application.ingest.import_document import ImportDocument" OK
[ ] python -c "from parser_studio.application.extraction.analyze_invoice import AnalyzeInvoice" OK
[ ] python -c "from parser_studio.application.review.confirm_invoice import ConfirmInvoice" OK
[ ] python -c "from parser_studio.bootstrap import build_default_application" OK
[ ] python -c "from parser_studio.bootstrap import build_default_application; i, a, c = build_default_application(); print(i, a, c)" OK
[ ] graft build output
[ ] graft blast output
[ ] File:line dokaz za legacy netaknutost
```

---

## Reviewer evidence

```text
[ ] vlastiti git diff review
[ ] vlastiti pytest -q reprodukcija
[ ] vlastiti ruff reprodukcija
[ ] vlastiti import sanity provjera (5 use case-ova)
[ ] provjera da legacy core/ NIJE DIRAN
[ ] provjera da application NE importuje openpyxl/xlrd
[ ] provjera da ConfirmInvoice NE pohranjuje u SQLite (MVP)
[ ] provjera ExtractionDraft i LearningEvent konstrukcija
[ ] R-001 ... nalazi
```

---

## Integration gate

```text
[ ] Implementer != Reviewer
[ ] Svi acceptance criteria zadovoljeni
[ ] CURRENT_STATE.md A5 status DONE
[ ] nema stvarnih faktura / poslovnih podataka u Git diffu
[ ] nema secret / token podataka u Git diffu
[ ] Post-merge integration gate: ponoviti pytest + ruff + drift
```

---

## Definition of Done — A5

```text
[ ] 3 use case-a (ImportDocument, AnalyzeInvoice, ConfirmInvoice)
[ ] ExtractionDraft + LearningEvent modeli
[ ] bootstrap.py sa wiring-om
[ ] 5+ unit testova
[ ] pytest ista ili bolja statistika
[ ] ruff ne značajno gore
[ ] contract drift PASS
[ ] Graft blast čist
[ ] CURRENT_STATE A5: DONE
[ ] commit + push
```

---

## Notes

- A5 je **PRVI PRAVI USE CASE SLOJ** — koordinira domain + ports.
- A5 uvodi MINIMALNI LearningEvent (bez SQLite) jer ConfirmInvoice ga zahtijeva.
  LearningRepository port i SQLite adapter su u A6.
- Migracija legacy `core/engines/` u novi application sloj je u A7.
- Ako zelis podjelu, mogu predloziti:
  - A5.1 — ImportDocument + AnalyzeInvoice (bez LearningEvent)
  - A5.2 — ConfirmInvoice + LearningEvent + bootstrap

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

---
title: "Parser Studio — plan arhitektonskog refaktora"
description: "Detaljan plan refaktora postojećeg Parser Studio repozitorija prema Modular Monolith + Hexagonal Architecture + MVVM + Evidence-first Learning pristupu."
project: "Parser Studio"
version: "1.0"
date: "2026-09-14"
status: "PLAN ZA REFAKTOR"
source_repo: "https://github.com/Rade69/parser_studio"
---

# Parser Studio — plan arhitektonskog refaktora

## 1. Polazno stanje i zaključak nakon pregleda repozitorija

Pregledano je stvarno stanje repozitorija `Rade69/parser_studio`, ne samo postojeći planovi.

Dobra vijest je da je arhitektonski refaktor trenutno relativno jeftin, jer stvarnog implementiranog koda još nema mnogo.

Najvrednije što već postoji i što treba sačuvati:

- `ExcelDocument`
- `Cell`
- `ExtractionTable`
- `ExcelHeadersEngine`
- vendorovani Deklarant Pro contract
- drift check
- postojeći unit testovi za Excel i contract

Veliki broj ostalih direktorijuma još je prazan i predstavlja samo ranije zamišljene skelete.

Zbog toga je sada pravi trenutak da se arhitektura promijeni prije nego što:

- Learning Database,
- Docling,
- AI,
- GUI,
- codegen,
- verification

počnu da pune postojeću `core/services/views` strukturu.

---

# 2. Šta je trenutno arhitektonski problematično

## 2.1 `core/documents/base.py`

Trenutno na jednom mjestu miješa tri različita koncepta:

- domain podatak `Cell`
- rezultat ekstrakcije `ExtractionTable`
- `Document` protokol

To znači da su:

```text
domain model
+
port
+
infrastructure concern
```

praktično spojeni u isti modul.

To treba razdvojiti.

## 2.2 `ExcelDocument`

`ExcelDocument` je dobro napisan tehnički adapter:

- otvara `.xlsx` i `.xls`
- koristi `openpyxl` i `xlrd`
- kešira sadržaj
- čuva provenance
- omogućava pristup sheetovima i ćelijama

Ali upravo zato ne treba dugoročno živjeti u `core/documents/`.

To je infrastructure adapter.

## 2.3 `Engine` koncept

Postojeći model:

```text
Engine
 ├─ probe(document)
 └─ extract(document, config)
```

je naslijeđe starog pravca:

```text
wizard
→ predloži engine
→ suggested_config
→ korisnički/deklarativni profil
```

Taj pravac više nije centralna arhitektura Parser Studija.

Zbog toga `Engine` koncept treba ukinuti, a ne samo preimenovati.

## 2.4 `ExcelHeadersEngine`

Ovaj kod ne treba baciti.

Naprotiv, to je jedan od najvrjednijih postojećih dijelova.

Treba sačuvati:

- normalizaciju headera
- rangirano poklapanje
- zaštitu kratkih aliasa
- footer detekciju
- mapiranje kolona
- provenance
- postojeće testove

Ali treba rastaviti engine na manje, arhitektonski pravilno smještene dijelove.

## 2.5 README i stara dokumentacija

README i postojeća struktura još opisuju stari pravac:

```text
bez LLM-a
deklarativni JSON profil
wizard
PBE
engine selection
```

To više ne odgovara novoj Learning-first arhitekturi.

---

# 3. Preporučena konačna arhitektura

Za Parser Studio treba koristiti:

> **Modular Monolith + Hexagonal Architecture (Ports & Adapters) + MVVM za PySide6 + Evidence-first Learning model**

Ne mikroservise.

Ne full Event Sourcing framework.

Ne težak enterprise DDD.

Jedna lokalna desktop aplikacija sa jasno razdvojenim modulima.

---

# 4. Predložena konačna struktura repozitorija

```text
parser_studio/
│
├── src/
│   └── parser_studio/
│
│       ├── domain/
│       │   ├── invoice/
│       │   │   ├── models.py
│       │   │   ├── fields.py
│       │   │   └── status.py
│       │   │
│       │   ├── evidence/
│       │   │   ├── locator.py
│       │   │   ├── models.py
│       │   │   └── tables.py
│       │   │
│       │   ├── extraction/
│       │   │   ├── candidate.py
│       │   │   ├── header_matching.py
│       │   │   └── validation.py
│       │   │
│       │   ├── learning/
│       │   │   ├── events.py
│       │   │   └── models.py
│       │   │
│       │   ├── profiles/
│       │   │   ├── models.py
│       │   │   ├── fingerprint.py
│       │   │   └── builder.py
│       │   │
│       │   └── parser_model/
│       │       └── vendor_parser_model.py
│       │
│       ├── application/
│       │   ├── ingest/
│       │   ├── extraction/
│       │   │   ├── analyze_invoice.py
│       │   │   ├── resolver.py
│       │   │   └── producers/
│       │   │
│       │   ├── review/
│       │   │   ├── review_invoice.py
│       │   │   └── confirm_invoice.py
│       │   │
│       │   ├── learning/
│       │   ├── profiles/
│       │   ├── generation/
│       │   └── verification/
│       │
│       ├── ports/
│       │   ├── document_reader.py
│       │   ├── candidate_producer.py
│       │   ├── learning_repository.py
│       │   ├── advisor.py
│       │   ├── parser_oracle.py
│       │   ├── parser_generator.py
│       │   └── parser_verifier.py
│       │
│       ├── adapters/
│       │   ├── documents/
│       │   │   ├── excel_reader.py
│       │   │   ├── docling_reader.py
│       │   │   └── rasterizer.py
│       │   │
│       │   ├── persistence/
│       │   │   └── sqlite/
│       │   │
│       │   ├── ai/
│       │   ├── declarant_pro/
│       │   ├── codegen/
│       │   │   └── templates/
│       │   └── verification/
│       │
│       ├── presentation/
│       │   ├── qt/
│       │   │   ├── views/
│       │   │   ├── viewmodels/
│       │   │   └── widgets/
│       │   └── cli/
│       │       └── psbuild.py
│       │
│       └── bootstrap.py
│
├── tests/
│   ├── unit/
│   │   ├── domain/
│   │   ├── application/
│   │   └── adapters/
│   ├── integration/
│   ├── architecture/
│   └── fixtures/
│
└── docs/
```

---

# 5. Tačno šta radimo sa postojećim fajlovima

| Sada | Poslije refaktora | Akcija |
|---|---|---|
| `core/documents/base.py` | `domain/evidence/*` + `ports/document_reader.py` | razbiti postojeći modul |
| `core/documents/excel_document.py` | `adapters/documents/excel_reader.py` | sačuvati postojeću Excel logiku |
| `core/engines/base.py` | obrisati | `Engine` zamijeniti `CandidateProducer` |
| `core/engines/excel_headers.py` | podijeliti na više modula | zadržati domensku logiku |
| `core/library/` | `domain/invoice/fields.py` | prenamijeniti u concept library |
| `core/profile/` | `domain/profiles/` | profil postaje izvedeni learning artifact |
| `core/mapping/` | ukloniti generic folder | mapiranje smjestiti uz konkretan use case |
| `core/synth/` | ukloniti | stari PBE pravac |
| `core/transforms/` | ukloniti kao catch-all | transformacije smjestiti uz odgovarajući domain modul |
| `core/codegen/` | `adapters/codegen/` | Jinja2 je adapter/tehnologija |
| `core/verify/` | application + adapter verification | razdvojiti pravila od subprocess implementacije |
| `services/` | `application/` | ne koristiti generic services folder |
| `views/` | `presentation/qt/views/` | MVVM presentation |
| `viewmodels/` | `presentation/qt/viewmodels/` | MVVM presentation |
| `views/wizard/` | obrisati | zastario i prazan |
| `cli/` | `presentation/cli/` | CLI je presentation adapter |

---

# 6. Novi Evidence model

Postojeći `Cell` trenutno nosi:

```text
value
row
col
page
x0
x1
top
sheet
```

To treba zamijeniti jasnijim modelom.

## Locator

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
```

## Evidence

```python
@dataclass(frozen=True, slots=True)
class Evidence:
    raw_value: Any
    raw_text: str
    locator: Locator
    element_type: str
```

Time isti model može opisati:

```text
Excel cell
PDF word
PDF table cell
Docling paragraph
text span
```

To će biti temelj za:

- bbox highlight
- AI grounding
- Review GUI
- Learning DB
- Gold Dataset
- OCR Recovery
- verification

---

# 7. Ukinuti Engine i uvesti CandidateProducer

Postojeći model:

```text
Engine
 ├─ probe(document)
 └─ extract(document, config)
```

treba zamijeniti modelom:

```python
class CandidateProducer(Protocol):
    producer_id: str

    def propose(
        self,
        evidence: DocumentEvidence,
        context: ExtractionContext,
    ) -> list[Candidate]:
        ...
```

Implementacije mogu biti:

```text
ExcelHeaderProducer
LabelRightProducer
LabelBelowProducer
ColumnContentProducer
ValueShapeProducer
KnownLayoutProducer
OcrRecoveryProducer
AiAdvisorProducer
ParserOracleProducer
```

Svi daju istu vrstu izlaza:

```text
Candidate
```

Resolver ne zna da li je kandidat došao iz:

- Excela
- Doclinga
- Layout profila
- AI-ja
- postojećeg parsera
- OCR recovery sloja

To je ključna prednost Ports & Adapters arhitekture.

---

# 8. Kako rastaviti `ExcelHeadersEngine`

Postojeći kod treba podijeliti ovako:

## 8.1 Concept library

```text
COLUMN_ALIASES
```

ide u:

```text
domain/invoice/fields.py
```

## 8.2 Header matching

```text
normalize_header()
_match_score()
identify_columns()
```

ide u:

```text
domain/extraction/header_matching.py
```

## 8.3 Orchestration

```text
find_header_row()
footer detection
row interpretation
```

ide u:

```text
application/extraction/producers/excel_header.py
```

## 8.4 Novi izlaz

`ExcelHeaderProducer` više ne vraća:

```text
ProbeResult
suggested_config
```

nego proizvodi kandidate:

```text
Candidate(field="quantity", ...)
Candidate(field="description", ...)
Candidate(field="unit_price", ...)
Candidate(field="line_amount", ...)
```

plus strukturirani evidence za redove.

Postojeće testove ne brisati.

Samo:

- premjestiti ih
- promijeniti import putanje
- sačuvati kao regression zaštitu

---

# 9. ExcelDocument postaje adapter

Trenutno `ExcelDocument` direktno koristi:

```text
openpyxl
xlrd
```

Zato treba postati:

```text
DocumentReader port
       ▲
       │
ExcelDocumentReader
DoclingDocumentReader
```

## Port

```python
class DocumentReader(Protocol):
    reader_id: str

    def supports(self, path: Path) -> bool:
        ...

    def read(self, path: Path) -> DocumentEvidence:
        ...
```

Application sloj ne smije raditi:

```python
ExcelDocument(path)
```

nego:

```python
evidence = document_reader.read(path)
```

Isti princip će kasnije koristiti Docling adapter.

---

# 10. Learning Database iza porta

Domain ne smije znati za SQLite.

Uvesti:

```python
class LearningRepository(Protocol):
    def append_event(self, event: LearningEvent) -> None:
        ...

    def get_document_state(
        self,
        document_id: str
    ) -> VerifiedDocument:
        ...

    def list_gold_documents(
        self,
        vendor_id: str
    ) -> list[VerifiedDocument]:
        ...
```

Konkretna implementacija:

```text
adapters/persistence/sqlite/
    connection.py
    migrations.py
    learning_repository.py
    projections.py
```

Domain ne smije imati:

```python
import sqlite3
```

---

# 11. Append-only Learning log

Centralni learning mehanizam ne treba biti obični CRUD.

Umjesto:

```sql
UPDATE verified_fields
SET value = 72.77
```

čuvamo istoriju:

```text
EXTRACTED
12.7

VALIDATION_FAILED
Q × P != A

USER_CORRECTED
12.7 → 72.77

USER_VERIFIED
72.77
```

Tabela:

```text
learning_events
```

može imati:

```text
id
document_id
item_id
field_name
event_type
old_value
new_value
locator
source
created_at
```

`verified_fields`, Gold Dataset i training view mogu biti projekcije.

---

# 12. Gold Dataset je projection

Ne treba imati više paralelnih izvora istine:

```text
verified_fields
corrections
gold_dataset
profile
```

Bolje:

```text
Evidence + Learning Events
            ↓
        projections
      ┌─────┼──────┐
      ▼     ▼      ▼
 Current   Gold   Training
 State   Dataset    View
```

Gold Dataset se može ponovo napraviti.

Layout Profile se takođe može ponovo napraviti.

Centralno pravilo:

```text
Gold Ground Truth
       ↓
Profile Builder
       ↓
Layout Profile
```

Nikada:

```text
Layout Profile
       ↓
   Ground Truth
```

---

# 13. Contract sa Deklarant Pro

Postojeći `contract/` treba sačuvati.

On sadrži vendorovanu kopiju:

- `Party`
- `InvoiceLine`
- `ImportResult`
- `ImportStrategy`
- drift check

To je korisno.

Ali contract nije Parser Studio domain.

Dugoročno treba završiti u:

```text
src/parser_studio/adapters/declarant_pro/contract/
```

Međutim, to ne treba raditi u prvom refaktor commit-u.

Prvo ostaviti `contract/` gdje jeste da se ne miješaju:

- arhitektonski refaktor
- contract migracija

Pravilo:

```text
domain      X→ contract
application X→ contract

declarant_pro adapter → contract
codegen adapter       → contract
verification adapter  → contract
```

Parser Studio domain treba da koristi svojih 20 poslovnih polja.

Tek adapter prevodi:

```text
CanonicalInvoice
       ↓
Deklarant Pro ImportResult
```

---

# 14. PySide6 koristi MVVM samo u presentation sloju

Za GUI:

```text
View
 ↓
ViewModel
 ↓
Application Use Case
```

Primjer:

```text
InvoiceReviewView
        ↓
InvoiceReviewViewModel
        ↓
ReviewInvoiceUseCase
```

ViewModel može znati:

- koji field je selektovan
- koji bbox treba označiti
- šta korisnik uređuje
- da li je faktura potvrđena

Ne smije sadržavati:

- OCR logiku
- SQL
- extraction heuristike
- Profile Builder
- parser generation

---

# 15. Application layer kao use-case sloj

GUI i CLI ne smiju direktno zvati infrastrukturu.

Ne:

```python
db.save(...)
docling.parse(...)
profile_builder.build(...)
```

direktno iz GUI-a.

Umjesto toga:

```text
ImportDocument
AnalyzeInvoice
ReviewInvoice
ConfirmInvoice
BuildLayoutProfile
GenerateParser
VerifyParser
ExportParser
```

Primjer:

```text
GUI
 ↓
ConfirmInvoiceUseCase
 ↓
Domain
 ↓
LearningRepository port
 ↓
SQLite adapter
```

---

# 16. `pyproject.toml` refaktor

Trenutni projekt nema `src/` layout.

Predložena konfiguracija:

```toml
[project]
name = "parser-studio"
version = "0.2.0"
description = "Learning-first alat za izradu i verifikaciju parsera faktura za Deklarant Pro"
requires-python = ">=3.11"

[project.scripts]
psbuild = "parser_studio.presentation.cli.psbuild:main"

[tool.setuptools.packages.find]
where = ["src"]
```

## Zavisnosti

Zadržati:

```text
pydantic
jinja2
PySide6
openpyxl
xlrd
rapidfuzz
```

`cryptography` za sada:

- ukloniti
- ili prebaciti u future optional `signing`

Docling dodati tek kada se implementira:

```text
DoclingDocumentReader
```

Ne u čistom architecture-refactor commit-u.

---

# 17. Architecture tests

Dodati:

```text
tests/architecture/test_import_boundaries.py
```

Test treba AST-om provjeravati granice.

## `domain/` ne smije importovati

```text
PySide6
sqlite3
openpyxl
xlrd
docling
requests
httpx
adapters
presentation
contract
```

## `application/` ne smije importovati

```text
adapters
presentation
PySide6
sqlite3
docling
```

## `ports/` ne smije importovati

```text
adapters
presentation
```

## `presentation/` ne smije direktno importovati

```text
sqlite3
docling
openpyxl
```

Ovo sprečava da se kasnije desi:

```text
View → sqlite
ViewModel → Docling
Resolver → PySide6
```

---

# 18. Refaktor bez big-bang promjene

Ne raditi:

```text
premjesti sve
→ popravljaj dok ne proradi
```

Raditi kroz male, kontrolisane korake.

## R1 — Nova package struktura

Napraviti:

```text
src/parser_studio/
    domain/
    application/
    ports/
    adapters/
    presentation/
```

Podesiti `pyproject.toml`.

Bez promjene poslovne logike.

## R2 — Evidence model

Uvesti:

```text
Locator
Evidence
Candidate
DocumentEvidence
```

Prebaciti semantiku `Cell` / `ExtractionTable`.

Stari modeli mogu privremeno ostati kao compatibility shim.

## R3 — Excel adapter

Premjestiti postojeći `ExcelDocument` u:

```text
adapters/documents/excel_reader.py
```

Uvesti:

```text
DocumentReader
```

port.

Svi postojeći Excel testovi moraju ostati zeleni.

## R4 — Ukinuti Engine

Rastaviti:

```text
ExcelHeadersEngine
```

na:

```text
domain/invoice/fields.py
domain/extraction/header_matching.py
application/extraction/producers/excel_header.py
```

Ukinuti:

```text
Engine
ProbeResult
suggested_config
```

Uvesti:

```text
CandidateProducer
```

Postojeći matching/footer testovi ostaju.

## R5 — Application use cases

Uvesti:

```text
ImportDocument
AnalyzeInvoice
ReviewInvoice
ConfirmInvoice
```

Ovo postaje prvi pravi application flow.

## R6 — Learning Repository

Uvesti:

```text
LearningRepository
SQLiteLearningRepository
LearningEvent
```

I:

```text
append-only learning_events
```

Tu počinje pravi Learning-first sistem.

## R7 — Presentation migracija

Premjestiti:

```text
views/
viewmodels/
cli/
```

u:

```text
presentation/qt/
presentation/cli/
```

Obrisati:

```text
views/wizard/
services/
stare prazne core direktorijume
compatibility shimove
```

Tek tada je arhitektura stvarno zaključana.

---

# 19. Šta radimo poslije R7

Tek nakon arhitektonskog refaktora:

```text
Docling adapter
      ↓
Review GUI
      ↓
Gold Dataset
      ↓
Profile Builder
      ↓
Learned Extraction
      ↓
OCR Recovery
      ↓
AI Advisor
      ↓
VendorParserModel
      ↓
Codegen
      ↓
Verifier
```

---

# 20. Stare import putanje tokom migracije

Privremeno se može koristiti compatibility re-export.

Primjer:

```python
# core/documents/excel_document.py

from parser_studio.adapters.documents.excel_reader import (
    ExcelDocumentReader,
)
```

Ali samo tokom jednog ili dva PR-a.

Finalno treba ukloniti:

```text
core/
services/
views/
viewmodels/
cli/
```

na root nivou.

Ne treba održavati dvije arhitekture paralelno.

---

# 21. Najvažnija nova granica

Precizan tok treba biti:

```text
FILE
  ↓
DOCUMENT ADAPTER
  ↓
DocumentEvidence
  ↓
CandidateProducers
  ↓
Candidates
  ↓
Resolver
  ↓
ExtractionDraft
  ↓
Review Use Case
  ↓
LearningEvent
  ↓
LearningRepository PORT
  ↓
SQLite Adapter
```

To je čišće i lakše testirati od starog toka:

```text
Document
→ Engine
→ Suggested Config
→ Profile
→ Mapping
```

---

# 22. Šta sačuvati iz postojećeg koda

Obavezno sačuvati:

```text
ExcelDocument logiku
header matching
footer zaštite
provenance ideju
contract + drift check
postojeće unit testove
```

---

# 23. Šta definitivno ukloniti

Definitivno ukloniti kao centralne arhitektonske koncepte:

```text
Engine
ProbeResult
suggested_config
wizard
korisnički JSON profil
PBE kao centralni pravac
generic services folder
generic mapping folder
generic transforms folder
```

---

# 24. Zašto je ovo bolja arhitektura

Parser Studio više nije samo:

```text
document
→ parser generator
```

nego:

```text
document
→ evidence
→ candidates
→ resolution
→ human verification
→ persistent learning
→ layout knowledge
→ improved extraction
→ parser generation
→ verification
```

To znači da je centralna vrijednost aplikacije:

```text
dokazano znanje
```

a ne samo trenutni parser kod.

---

# 25. Konačna preporuka

Arhitekturu zaključati kao:

> **Modular Monolith**
>
> + **Hexagonal / Ports & Adapters**
>
> + **MVVM za PySide6**
>
> + **Evidence-first domain**
>
> + **append-only Learning history**
>
> + **SQLite projections**
>
> + **derived Layout Profiles**
>
> + **deterministički VendorParserModel → Codegen → Verification**

Prvi posao za agenta ne treba biti Learning DB niti Docling.

Prvo uraditi:

```text
R1
R2
R3
R4
```

odnosno:

```text
nova package struktura
→ Evidence model
→ Excel adapter
→ CandidateProducer umjesto Engine
```

bez promjene postojećeg ponašanja.

Tek onda graditi nove Learning-first funkcije na čistoj osnovi.

# Parser Studio — Project Map

Praktična mapa za agente u tri odvojena pogleda:

A) trenutna stvarna struktura,
B) target arhitektura,
C) migraciona mapa,
D) sensitive boundaries.

---

## A) CURRENT REPOSITORY MAP

Stvarno stanje na disku (provjereno 2026-09-14, `dev` granа, HEAD `348d5eb4d0da16ee13af805ca6c5bae0648dc161`).

### Root

```text
H:/parser_studio/
├── .git/
├── .pytest_cache/             (gitignored)
├── .gitignore
├── pyproject.toml
│
├── cli/                       LEGACY — entry point psbuild
├── contract/                  TRANSITIONAL — vendorovana kopija Deklarant Pro ugovora
├── core/                      LEGACY — stari paketi koji se migriraju
├── services/                  LEGACY — prazno, ukloniti
├── viewmodels/                LEGACY — prazno, ukloniti
├── views/                     LEGACY — prazno + views/wizard
│
├── tests/                     ACTIVE — unit testovi
├── experiments/               ACTIVE — benchmark moduli
├── docs/                      ACTIVE — istorija + PLAN.md
├── agent_reports/             ACTIVE — benchmark izvještaji
│
├── PARSER_STUDIO_AGENTS.md           SOURCE — predložak za AGENTS.md
├── PARSER_STUDIO_README.md           SOURCE — predložak za README.md
├── PARSER_STUDIO_KANONSKI_PLAN_V3.md SOURCE — V3 kanonski plan
├── GRAFT_ADOPTION_PLAYBOOK.md        SOURCE — Graft procedura
│
├── AGENTS.md                  NEW — thin router
├── CLAUDE.md                  NEW — coordinator router
├── README.md                  NEW — project overview
└── docs/PLAN.md               NEW — V3 kopija
```

### `contract/` — TRANSITIONAL

```text
contract/
├── __init__.py
├── CONTRACT_VERSION
├── draft_types.py
├── import_result.py
├── base_strategy.py
├── drift_check.py
└── tests/                     (pokazuje PASS u baseline)
```

Status: ostaje u root-u tokom migracije (V3 sekcija 38). Dugoročno ide u `adapters/declarant_pro/contract/`.

### `core/` — LEGACY

```text
core/
├── documents/
│   ├── __init__.py
│   ├── base.py                Cell + ExtractionTable + Document — mješovito
│   └── excel_document.py      ExcelDocument — dobro napisan adapter
├── engines/
│   ├── __init__.py
│   ├── base.py                Engine protokol — ZASTARILO, ukinuti
│   └── excel_headers.py       ExcelHeadersEngine — najvrjedniji
├── profile/                   PRAZNO — ukloniti ili pretvoriti u domain/profiles/
├── library/                   PRAZNO — ukloniti
├── mapping/                   PRAZNO — ukloniti
├── synth/                     PRAZNO — ukloniti (stari PBE pravac)
├── transforms/                PRAZNO — ukloniti
├── codegen/                   PRAZNO — migrira u adapters/codegen/
├── verify/                    PRAZNO — dijeli se u application/verification/ + adapters/verification/
├── ai/                        PRAZNO — M14 posao
└── model/                     PRAZNO — M1 posao
```

### `views/`, `viewmodels/`, `services/`, `cli/` — LEGACY

```text
cli/
└── psbuild.py                 LEGACY entry point (pyproject.toml "psbuild")

views/                         PRAZNO
views/widgets/                 PRAZNO
views/wizard/                  PRAZNO — ukloniti

viewmodels/                    PRAZNO

services/                      PRAZNO
```

### `tests/` — ACTIVE

```text
tests/
├── __init__.py
├── conftest.py
├── unit/
│   ├── test_quality_gate.py
│   ├── test_normalization.py
│   ├── test_table_classifier.py
│   ├── test_table_stitcher.py
│   ├── test_semantic_resolver.py
│   ├── test_price_amount_resolver.py
│   └── test_invoice_meta_extractor.py
└── fixtures/                  (ili prazno)
```

Baseline: 180 PASS, 1 FAIL (`test_f9_no_broken_rows`).

### `experiments/` — ACTIVE (privremeno)

```text
experiments/
└── document_engines/
    ├── benchmark/             kvality_gate, normalization, table_* , semantic_*, price_*, invoice_*
    ├── docling_env/           (gitignored)
    ├── paddle_env/            (gitignored)
    └── parser_readiness_v4/   (UNTRACKED — novi benchmark output)
```

Status: eksperimentalan sloj; V3 ne predviđa njegovu buduću ulogu. Treba odluku da li prelazi u `adapters/` (Docling) ili se arhivira.

### `docs/` — ACTIVE

```text
docs/
├── PLAN.md                                        NEW (V3 kopija)
├── PARSER_STUDIO_IMPLEMENTACIONI_PLAN_ZA_AGENTA.md  istorijski
├── Parser_Studio_Learning_First_Plan.md             istorijski
└── PARSER_STUDIO_PLAN_ARHITEKTONSKOG_REFAKTORA.md   istorijski (SUPERSEDED by V3)
```

### `agent_reports/` — ACTIVE

```text
agent_reports/
├── 2026-09-13-docling-vs-paddle-benchmark.md
├── 2026-09-13-docling-paddle-benchmark-v2.md
├── 2026-09-13-docling-quality-benchmark-v3.md
├── 2026-09-13-docling-parser-readiness-v4.md
├── TASK_CONTRACT_TEMPLATE.md   NEW
└── REVIEW_TEMPLATE.md          NEW
```

---

## B) TARGET ARCHITECTURE MAP

Iz V3 sekcija 6 i 7.

```text
src/parser_studio/
├── domain/                    NE ZA infrastrukturu
│   ├── invoice/               models, fields, status
│   ├── evidence/              locator, models, tables
│   ├── extraction/            candidate, context, header_matching, validation
│   ├── learning/              events, models, projections
│   ├── profiles/              models, fingerprint, rules
│   └── parser_model/          vendor_parser_model
│
├── application/               use cases + resolver orchestration
│   ├── ingest/
│   ├── extraction/            analyze_invoice, resolver, validators/, producers/
│   ├── review/                review_invoice, confirm_invoice
│   ├── learning/
│   ├── profiles/              build_profile, match_profile
│   ├── generation/
│   └── verification/
│
├── ports/                     contracts; NE ZAVISI od adaptera/presentation
│   ├── document_reader.py
│   ├── candidate_producer.py
│   ├── learning_repository.py
│   ├── advisor.py
│   ├── parser_oracle.py
│   ├── parser_generator.py
│   └── parser_verifier.py
│
├── adapters/                  tehnologija; zavise prema unutra (domain + ports)
│   ├── documents/             excel_reader, docling_reader, rasterizer
│   ├── persistence/sqlite/    connection, migrations, learning_repository, projections
│   ├── ai/                    http_vision_advisor, cache, transport
│   ├── declarant_pro/         oracle adapter + contract (migracija iz root-a)
│   ├── codegen/               generator, guards, templates/
│   └── verification/          subprocess runner
│
├── presentation/
│   ├── qt/                    views, viewmodels, widgets
│   └── cli/                   psbuild
│
└── bootstrap.py               composition root
```

### domain

**Posjeduje:**

- Invoice model (svih 20 polja + statusi).
- Evidence / Locator / DocumentEvidence.
- Candidate (field, raw_value, normalized_value, locator, evidence, producer_id, ai_assisted, issues).
- ExtractionDraft (resolved fields, candidate sets, conflicts, unresolved).
- CanonicalInvoice.
- LearningEvent (append-only history).
- LayoutProfile, LayoutFingerprint.
- VendorParserModel.

**Ne zna za:**

- PySide6, sqlite3, openpyxl, xlrd, docling, requests, httpx.
- `adapters/`, `presentation/`, `contract/`.
- Konkretne AI providere.

### application

**Posjeduje:**

- Use case-ovi: ImportDocument, AnalyzeInvoice, ReviewInvoice, ConfirmInvoice, BuildLayoutFingerprint, BuildLayoutProfile, MatchLayoutProfile, RecoverFieldOCR, GenerateVendorParser, VerifyVendorParser, ExportVendorParser.
- Resolver orchestration.
- Validators.
- Profile workflows.
- Generation/verification workflows.

**Smije zavisiti samo od:**

- `domain/`, `ports/`.

### ports

**Posjeduje contracts (Protocol klase):**

- DocumentReader.
- CandidateProducer.
- LearningRepository.
- Advisor.
- ParserOracle.
- ParserGenerator.
- ParserVerifier.

**Ne zavisi od:**

- Adaptera, presentation sloja, konkretne tehnologije.

### adapters

**Posjeduje konkretne implementacije portova:**

- ExcelDocumentReader, DoclingDocumentReader, Rasterizer.
- SQLiteLearningRepository + projections + migrations.
- HttpVisionAdvisor + cache + transport.
- DeklarantProOracle + contract.
- JinjaParserGenerator + guards + templates/.
- SubprocessParserVerifier.

**Smije zavisiti samo od:**

- `domain/`, `ports/`, konkretne tehnologije.

### presentation

**Posjeduje:**

- PySide6 View / ViewModel / Widgets (MVVM).
- CLI (psbuild).

**Smije zavisiti samo od:**

- `application/` (use-case-ove).

**Ne smije direktno:**

- Otvarati SQLite konekciju.
- Zvati Docling.
- Otvarati Excel fajl preko openpyxl.
- Pozivati AI transport.

---

## C) MIGRATION MAP

Iz V3 sekcija 5 i 57. Usklađeno sa stvarnim stanjem.

### Direktna migracija postojećih fajlova

```text
core/documents/base.py
    → domain/evidence/* (Locator, Evidence, DocumentEvidence, Candidate)
    → ports/document_reader.py (DocumentReader Protocol)

core/documents/excel_document.py
    → adapters/documents/excel_reader.py (ExcelDocumentReader)

core/engines/base.py
    → UKLONITI (Engine koncept)
    → ports/candidate_producer.py (CandidateProducer Protocol)

core/engines/excel_headers.py
    → domain/invoice/fields.py           (COLUMN_ALIASES)
    → domain/extraction/header_matching.py (normalize_header, _match_score, identify_columns)
    → application/extraction/producers/excel_header.py (find_header_row, footer, orchestration)

core/profile/
    → domain/profiles/                  (models, fingerprint, rules)
    → application/profiles/             (build_profile, match_profile)

core/library/
    → domain/invoice/fields.py          (concept library)

core/mapping/
    → ukloniti kao generic layer

core/synth/
    → ukloniti

core/transforms/
    → ukloniti kao generic catch-all

core/codegen/
    → adapters/codegen/                 (generator, guards, templates/)

core/verify/
    → application/verification/
    → adapters/verification/

core/ai/
    → adapters/ai/                      (M14 posao)

core/model/
    → domain/ (M1 posao)

services/
    → application/

views/
    → presentation/qt/views/

viewmodels/
    → presentation/qt/viewmodels/

views/wizard/
    → ukloniti

cli/
    → presentation/cli/

contract/
    → ostaje u root-u tokom migracije
    → dugoročno: adapters/declarant_pro/contract/
```

### `views/wizard/`

**NE POSTOJI stvarno** sadržajno (samo `__init__.py`). Ukloniti kao direktorijum.

### `core/ai/` i `core/model/`

Nisu prazni u smislu postojanja, ali nemaju kod. V3 predviđa `adapters/ai/` (M14) i `domain/` (M1) za te funkcije.

### Migraciona pravila

- Neka pravila zabranjuju `core/engines` ostatke poslije migracije — `Engine` koncept se **gasi**, ne samo preimenuje.
- `core/synth/`, `core/mapping/`, `core/transforms/`, `services/`, `views/wizard/` se **uklanjaju** bez zamjene.
- `contract/` se NE briše i NE pretvara u Parser Studio domain; ostaje Deklarant Pro read-only vendorovan.
- `views/`, `viewmodels/`, `cli/` se premještaju u `presentation/`, NE brišu se.
- Stari import putanje mogu postojati kao **compatibility shim** samo tokom jednog ili dva PR-a, sa planom uklanjanja.

---

## D) SENSITIVE BOUNDARIES

Granice koje zahtijevaju poseban oprez i architecture testove.

### Contract boundary

```text
Parser Studio domain   X-> contract
Parser Studio application X-> contract

deklarant_pro adapter  -> contract
codegen adapter        -> contract
verification adapter   -> contract
```

`contract/` je vendorovana kopija Deklarant Pro tipova (`Party`, `InvoiceLine`, `ImportResult`, `ImportStrategy`). Parser Studio ne smije tretirati te tipove kao svoj domain.

### Deklarant Pro boundary

- `H:/deklarant_pro` je **read-only** za Parser Studio razvoj.
- Koristi se za `contract.drift_check`, oracle poređenje, referentnu verifikaciju.
- Parser Studio NE mijenja Deklarant Pro.
- Ako generisani parser zahtijeva promjenu Deklarant Pro, prijaviti kao nalaz Human Owneru.

### PDF / Docling boundary

- Docling je **adapter**, ne domain.
- Implementiran iza `DocumentReader` porta (M3 posao).
- Markdown NIJE autoritativni format za internu evidenciju.
- Raw Docling output za stvarne fakture NE ide u Git.

### Persistence boundary

- SQLite je adapter iza `LearningRepository` porta.
- Domain NE smije importovati `sqlite3`.
- Append-only `learning_events` + projection tabele.
- Stvarni poslovni podaci iz Gold Dataseta NE idu u Git.

### AI boundary

- AI je opcionalan advisor; default `PS_AI_MODE=off`.
- AI kandidat mora imati `Locator` + `evidence`.
- AI kandidat bez groundinga (NFKC + collapsed whitespace + case-insensitive, BEZ fuzzy) NE ulazi u resolver.
- AI cache stvarnih dokumenata je lokalni privatni podatak i NE ide u Git.
- AI se ne koristi za pravno značajne odluke (tarifni broj, iznos, masa).

### Codegen boundary

- Jinja2 templates su adapter; ne u domain.
- Generisani `.py` NE smije importovati `parser_studio`.
- `ast.parse()` + `compile()` + import allowlist + ruff su obavezni.
- `eval`, `exec`, `__import__`, `from parser_studio ...` su zabranjeni u generisanom kodu.

### Verification boundary

- Verifikacija pokreće stvarni generisani `.py` u zasebnom procesu.
- To je **stabilnost/izolacija**, NE sigurnosni sandbox.
- Subprocess pokretanje je u `adapters/verification/`.
- Poređenje sa Gold Datasetom je u `application/verification/`.

---

## Kako koristiti ovu mapu

- Ako radiš na **legacy migraciji** — sekcija C.
- Ako dodaješ **novi domain model** — sekcija B (`domain/`).
- Ako pišeš **adapter** — sekcija B (`adapters/`) + sekcija D (relevantna granica).
- Ako gradiš **GUI** — sekcija B (`presentation/`) + MVVM pravilo iz V3.
- Ako sumnjaš u **dependency smjer** — sekcija D + V3 DEP-001 do DEP-005.

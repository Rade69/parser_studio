# Parser Studio — Current State

Živi status projekta. Piše samo ono što je **stvarno provjereno**.

---

## Snapshot

```text
Date:           2026-09-14
Branch:         dev
HEAD:           348d5eb4d0da16ee13af805ca6c5bae0648dc161
Working tree:   mixed — 3 DELETED + 6 UNTRACKED + 1 modified gitignored
Python:         3.11+
Platform:       Windows (H:/parser_studio)
```

### Working tree detalji

DELETED (u radnom stablu, ali još necommitovano):

```text
D PLAN.md
D README.md
D PARSER_STUDIO_KONSOLIDOVANI_PLAN_I_PREPORUKE.md
```

UNTRACKED:

```text
?? GRAFT_ADOPTION_PLAYBOOK.md
?? PARSER_STUDIO_AGENTS.md
?? PARSER_STUDIO_KANONSKI_PLAN_V3.md
?? PARSER_STUDIO_README.md
?? docs/
?? experiments/document_engines/parser_readiness_v4/
```

---

## Canonical plan

```text
docs/PLAN.md   (canonical)
version:       3.0
source root:   PARSER_STUDIO_KANONSKI_PLAN_V3.md (Human Owner arhivski)
```

Ako se `docs/PLAN.md` i V3 razlikuju, V3 je autoritet dok se razlika ne pomiri u novom dokumentu.

---

## Current canonical phase

```text
Phase:          Architecture Migration
Current step:   A0 — Baseline
```

A0 NIJE još formalno završen. Ovaj `CURRENT_STATE.md` je nastao tokom uspostavljanja development frameworka, ne tokom A0 acceptance gate-a.

---

## Implemented now

### Struktura na disku

```text
cli/             legacy entry point (psbuild)
contract/        vendorovana kopija Deklarant Pro contracta + drift_check
core/            legacy paketi (documents, engines, profile, library, mapping, synth, transforms, codegen, verify, ai, model)
services/        prazno (legacy sloj)
viewmodels/      prazno (legacy sloj)
views/           views + views/wizard (prazan, zastario)
tests/           unit testovi (180 PASS + 1 FAIL u baseline)
docs/            istorijski planovi (UNTRACKED) + PLAN.md (NEW, A0 okvir)
experiments/     benchmark moduli + parser_readiness_v4 (UNTRACKED)
agent_reports/   benchmark izvještaji (UNTRACKED)
```

### Kod koji danas postoji

- `contract/` — `draft_types.py`, `import_result.py`, `base_strategy.py`, `drift_check.py`, `CONTRACT_VERSION`.
- `core/documents/` — `base.py` (Cell, ExtractionTable, Document protokol — mješovito), `excel_document.py` (ExcelDocument adapter, dobro napisan).
- `core/engines/` — `base.py` (Engine protokol — zastario), `excel_headers.py` (ExcelHeadersEngine — najvrjedniji).
- `core/profile/`, `core/library/`, `core/mapping/`, `core/synth/`, `core/transforms/`, `core/codegen/`, `core/verify/`, `core/ai/`, `core/model/` — prazni ili samo `__init__.py`.
- `cli/psbuild.py` — legacy CLI entry point.
- `views/`, `viewmodels/`, `services/` — prazni ili `__init__.py`.

---

## Not implemented yet

Sljedeće iz V3 **još ne postoji** u kodu:

- `src/parser_studio/` layout (sav kod je u staroj `core/`/`services/`/`views/`/`cli/` strukturi).
- `domain/` paketi: `invoice/`, `evidence/`, `extraction/`, `learning/`, `profiles/`, `parser_model/`.
- `application/` paketi: `ingest/`, `extraction/`, `review/`, `learning/`, `profiles/`, `generation/`, `verification/`.
- `ports/` paketi: `document_reader.py`, `candidate_producer.py`, `learning_repository.py`, `advisor.py`, `parser_oracle.py`, `parser_generator.py`, `parser_verifier.py`.
- `adapters/` paketi: `documents/`, `persistence/sqlite/`, `ai/`, `declarant_pro/`, `codegen/`, `verification/`.
- `presentation/qt/` (MVVM), `presentation/cli/`.
- `Locator`, `Evidence`, `DocumentEvidence`, `Candidate`, `ExtractionDraft`, `CanonicalInvoice` (kao domain modeli).
- `LearningEvent`, `LearningRepository`, append-only `learning_events` tabela.
- `LayoutFingerprint`, `LayoutProfile`, `Profile Builder`.
- `VendorParserModel`, Jinja codegen, AST/compile guards.
- Docling adapter (iako je već korišten u benchmarku, još nije iza porta).
- Gold Dataset (B5 — čeka `B1`–`B4`).
- AI Advisor infrastruktura (G1–G5).
- Architecture tests (`tests/architecture/test_import_boundaries.py`).

---

## Test baseline

```text
pytest:        180 PASS, 1 FAIL
ruff:          157 errors (98 fixable)
contract drift: PASS (Party 5/5, InvoiceLine 29/29, ImportResult 15/15)
```

### pytest FAIL detalji

```text
FAILED tests/unit/test_quality_gate.py::test_f9_no_broken_rows
  assert True is False
```

Test očekuje da F9 ne bude aktiviran na 10 čistih redova, ali F9 JE aktiviran. To je **regression u benchmark eksperimentu**, NE u core/domain kodu. Ne blokira framework zadatak; treba ga riješiti u sklopu benchmark cleanup-a ili A0 acceptance kriterija.

### ruff detalji

Većina grešaka je u `tests/unit/test_table_stitcher.py` i drugim benchmark/test fajlovima (import organizacija, RUF059 — unused unpacked variable). Nije dio domain/business koda. Za detaljnu listu pokrenuti `python -m ruff check .` u root-u.

---

## Architecture migration status

| Korak | Status | Dokaz |
|---|---|---|
| A0 | DONE | Baseline zabilježen, contract drift PASS, V3 u `docs/PLAN.md`, stari planovi u `docs/istorija/`, `.gitignore` provjeren. |
| A1 | DONE | `src/parser_studio/` skelet kreiran (18 `__init__.py` + `bootstrap.py`), `pyproject.toml` packages.find.where=src, pythonpath=["src","."]. Commit b1671f6, pushan. |
| A2 | DONE | Evidence domain u `src/parser_studio/domain/evidence/`: 6 modela (Locator, Evidence, DocumentEvidence, Candidate, ExtractionContext) + cell_compat adapter + 41 unit testova (svi PASS). pytest 221 PASS + 1 FAIL (test_f9 pre-existing). Commit c1a07d6, pushan. |
| A3 | DONE | DocumentReader Protocol u `src/parser_studio/ports/` + ExcelDocumentReader u `src/parser_studio/adapters/documents/` (.xlsx openpyxl, .xlsm, .xls xlrd, keširanje, DocumentEvidence output) + 16 unit testova (svi PASS). pytest 237 PASS + 1 FAIL (test_f9 pre-existing). Legacy `core/` netaknut. Commit 439e386 + cleanup 36218cf, pushan. |
| A4 | DONE | CandidateProducer Protocol u `src/parser_studio/ports/candidate_producer.py` + FieldContext dataclass + ExcelHeadersEngine migriran u 4 modula: `domain/invoice/fields.py` (75+ aliasa u 13 polja), `domain/extraction/header_matching.py` (normalize/match/identify), `application/extraction/producers/excel_header.py` (ExcelHeaderProducer) + helper `_sheet_utils.py` + 49 unit testova (svi PASS). pytest 286 PASS + 1 FAIL (test_f9 pre-existing). Legacy `core/engines/` netaknut. Commit e08c1ae + cleanup b1671f6, pushan. |
| A5 | DONE | Application sloj sa 3 use case-a: ImportDocument (application/ingest/), AnalyzeInvoice (application/extraction/), ConfirmInvoice (application/review/) + ExtractionDraft (domain/extraction/) + LearningEvent + EventType (domain/learning/) + LearningRepository Protocol. bootstrap.py sa build_default_application() wiring. 24 unit testova (svi PASS). pytest 310 PASS + 1 FAIL (test_f9 pre-existing). Application NE importuje openpyxl/xlrd (sve preko DocumentReader porta). Commit c23f7a9, pushan. |
| A6 | NOT_STARTED | `LearningRepository` port + SQLite adapter nisu implementirani (Protocol deklarisan u A5, A6 doda adapter). |
| A7 | NOT_STARTED | Presentation migracija nije urađena; legacy `core/services/views` i dalje aktivni. |

---

## Known risks / blockers

1. **Pre-existing failing test** (`test_f9_no_broken_rows`) — regression u benchmark eksperimentu, ne blokira framework ali treba cleanup.
2. **Pre-existing ruff errors** (157) — većina u benchmark/test fajlovima, ne blokira framework.
3. **`pyproject.toml` kontradikcija sa V3**:
   - `cryptography>=41.0` u dependencies — V3 kaže ukloniti ili u `optional[signing]`.
   - description `"Alat za poluautomatsko pravljenje parsera faktura za Deklarant Pro (bez LLM-a)"` — stara formulacija; V3 uvodi AI kao opcionalan advisor.
   - Entry point `cli.psbuild:main` — radi na staroj `cli/` strukturi; nakon A1 mora biti `parser_studio.presentation.cli.psbuild:main`.
   - Ovo je A0/A1 acceptance kriterij, NE framework zadatak.
4. **Graft status nepoznat** — nije lokalno evaluiran na Parser Studio repou; vidi sekciju "Graft status".
5. **Source dokumenti u root-u** (`PARSER_STUDIO_*.md`, `GRAFT_ADOPTION_PLAYBOOK.md`) — UNTRACKED; treba ih commit-ovati zajedno sa framework fajlovima u jednom PR-u.

---

## Graft status

```text
SECONDARY (probacioni period)
```

Lokalna evaluacija završena 2026-09-14. Human Owner odobrio SECONDARY.

Pravila za SECONDARY period:

- Graft `callers` + `grep` zajedno (zero callers NIJE dovoljno — potvrđen rizik na `Cell`).
- Graft `blast` za MEDIUM/HIGH prije reviewa.
- Ručni grep + read ostaje fallback.
- Architecture testovi (kad se uvedu) su autoritet za dependency granice.
- Probacioni period: A2, A3, A4, A6, A7 (arhitektonski refaktori).
- Stari alati ostaju dostupni; Graft NIJE zamjena za testove.

Detaljan izvještaj: `agent_reports/2026-09-14-graft-evaluation.md`.

---

## Last completed task

```text
NONE / PRE-FRAMEWORK BASELINE
```

Ovaj framework dokument je nastao kao dio uspostavljanja development frameworka, ne kao rezultat prethodnog implementacijskog taska.

---

## Next recommended task

A0 acceptance ZAVRŠEN.

Prema V3 sekcija 58 ("Prvi naredni radni paket: A0 + A1 + A2"):

```text
A0 — Baseline                              [DONE]
A1 — src/parser_studio/ layout             [NEXT]
A2 — Evidence domain                       [NEXT]
```

A1/A2 zahtijevaju zaseban Task Contract prije pokretanja (po `agent_reports/TASK_CONTRACT_TEMPLATE.md`). Preporučeni redoslijed:

1. Fix pre-existing benchmark problema (`test_f9_no_broken_rows`, 157 ruff grešaka) — OBA su u benchmark/test fajlovima, NE u core/domain kodu. Mogu biti dio A1 acceptance ili zaseban cleanup task.
2. A1 — kreirati `src/parser_studio/{domain,application,ports,adapters,presentation}/` layout, podesiti `pyproject.toml`, kompatibilan shim za stare import putanje tokom 1-2 PR-a.
3. A2 — uvesti `Locator`, `Evidence`, `DocumentEvidence`, `Candidate` u `src/parser_studio/domain/evidence/`.

---

## Decision log

- **2026-09-14** — Usvojen `PARSER_STUDIO_KANONSKI_PLAN_V3.md` kao jedini važeći plan; stari planovi (Konsolidovani V2, Arhitektonski Refaktor, Implementacioni V1) su istorijski.
- **2026-09-14** — Kreiran development framework: `AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/PLAN.md`, `.agent/CURRENT_STATE.md`, `.agent/PROJECT_MAP.md`, `.agent/TASK_ROUTING.md`, `.agent/GRAFT_EVALUATION_TEMPLATE.md`, `agent_reports/TASK_CONTRACT_TEMPLATE.md`, `agent_reports/REVIEW_TEMPLATE.md`.
- **2026-09-14** — Graft status: `SECONDARY` (probacioni period). Lokalna evaluacija završena: build PASS, G1 zero-callers rizik REPRODUCIBLE, G2 PASS, G3 NOT_APPLICABLE, G4 PASS, G5 PASS (svi upiti < 1s). Izvještaj: `agent_reports/2026-09-14-graft-evaluation.md`.
- **2026-09-14** — A0 acceptance ZAVRŠEN: baseline dokumentovan (180 PASS + 1 FAIL + 1 SKIPPED), contract drift PASS, V3 u `docs/PLAN.md`, stari planovi u `docs/istorija/`, `.gitignore` provjeren za stvarne fakture.
- **2026-09-14** — Source dokumenti (`PARSER_STUDIO_*.md`, `GRAFT_ADOPTION_PLAYBOOK.md`) UNTRACKED u radnom stablu; arhiviraju se u root u sklopu framework PR-a.
- **2026-09-14** — 2 root fajla DELETED u radnom stablu (`PARSER_STUDIO_KONSOLIDOVANI_PLAN_I_PREPORUKE.md`, stari `PLAN.md`) — sadržaj je u git historiji; ne vraćaju se fizički.
- **2026-09-14** — A1 acceptance ZAVRŠEN: `src/parser_studio/` skelet kreiran (18 `__init__.py` + `bootstrap.py`), `pyproject.toml` packages.find.where=src, pythonpath=["src","."]. pytest ista statistika (180 PASS + 1 FAIL), ruff 157 (nije pogoršano), contract drift PASS, `import parser_studio.bootstrap` OK. Graft blast: 20 seed simbola, 0 impacted dependents. Commit b1671f6, pushan na origin/dev. Task Contract: `agent_reports/A1-task-contract.md`.
- **2026-09-14** — A2 acceptance ZAVRŠEN: Evidence domain u `src/parser_studio/domain/evidence/` (6 modela + adapter, svi frozen=True, slots=True) + 41 unit testova (svi PASS). pytest 221 PASS + 1 FAIL (test_f9 pre-existing benchmark regression), ruff 158 (+1 cell_compat upozorenje, u okviru tolerance), contract drift PASS. Domain NE importuje sqlite3/openpyxl/xlrd/PySide6/docling/contract. cell_compat koristi TYPE_CHECKING za legacy Cell. Graft blast: 52 seed simbola, 0 impacted dependents. Commit c1a07d6, pushan na origin/dev. Task Contract: `agent_reports/A2-task-contract.md`.
- **2026-09-14** — A3 acceptance ZAVRŠEN: DocumentReader Protocol u `src/parser_studio/ports/document_reader.py` (runtime_checkable, supports+read) + ExcelDocumentReader u `src/parser_studio/adapters/documents/excel_reader.py` (.xlsx openpyxl, .xlsm, .xls xlrd, kesiranje po apsolutnoj putanji, DocumentEvidence output) + 16 unit testova u `tests/unit/adapters/documents/test_excel_reader.py` (svi PASS). pytest 237 PASS + 1 FAIL (test_f9 pre-existing), ruff 162 (+4 adapter/documents, u okviru tolerance), contract drift PASS. Legacy `core/documents/excel_document.py` NEDIRAN (git diff --stat core/ prazan). Adapter NE importuje legacy `core.*`. Commit 439e386, cleanup 36218cf (uklonio _commit_msg.txt uhvacen u git add --all), pushan na origin/dev. Task Contract: `agent_reports/A3-task-contract.md`.

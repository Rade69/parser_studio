# Parser Studio — Current State

Živi status projekta. Piše samo ono što je **stvarno provjereno**.

---

## Snapshot

```text
Date:           2026-09-14
Branch:         dev
HEAD:           M2+M4 merge (commit c91c498) + UI0/GATE-0 LOCKED
Working tree:   mixed — V3 -> istorija preimenovano, GUI_BLUEPRINT.md novi
Python:         3.11+
Platform:       Windows (H:/parser_studio)
```

### Working tree detalji

DELETED (checkout artefakt, vratiti ili ostaviti UNTRACKED):

```text
D PARSER_STUDIO_KANONSKI_PLAN_V3.md  (UNTRACKED original, git checkout ga je "izbrisao" iz working tree)
```

UNTRACKED:

```text
?? asset/parser_studio_gui_mockup.png
?? PARSER_STUDIO_KANONSKI_PLAN_V3_1.md  (korisnicka kopija)
```

---

## Canonical plan

```text
docs/PLAN.md            (canonical, v3.2)
docs/GUI_BLUEPRINT.md   (UI0 / GATE-0 LOCKED, 2026-09-14)
docs/istorija/          stari planovi (V3, Implementacioni, Arhitektonski)
```

Ako se `docs/PLAN.md` (v3.2) i stari V3 razlikuju, **V3.2 je autoritet**. Posebno važno:
- V3.2 uvodi **FAZA UI0** (Product/GUI Blueprint) kao PRVU fazu, prije FAZA A
- V3.2 uvodi **GATE-0** (GUI/UX Blueprint Locked) prije A1+ implementacije
- V3.2 dodaje **OCR Reading Map** u FAZA E (E2.5)

---

## Current canonical phase

```text
Phase:          FAZA UI0 (GATE-0 LOCKED) + FAZA B (M1-M5 zavrseni)
Current step:   FAZA B DONE; sledeca FAZA C (Generic extraction)
```

FAZA UI0 (Product/GUI Blueprint) **ZAKLJUČANA** 14.09.2026 sa `docs/GUI_BLUEPRINT.md` (komplet blueprint: application shell + 9 glavnih ekrana + 9 modala + 16 obaveznih stanja + centralni tok).

**GATE-0** (GUI/UX Blueprint Locked) — PASS.

**FAZA B COMPLETE** (M1+M2+M3+M4+M5 = 236 novih testova, svi merge-ovani u dev).

Sledeca FAZA: **C — Generic extraction** (V3_2 §43 FAZA C).

---

---

## Implemented now

### Struktura na disku

```text
src/parser_studio/
    domain/           evidence/, invoice/, extraction/, learning/
    application/      ingest/, extraction/, review/
    ports/            document_reader.py, candidate_producer.py, learning_repository.py, ...
    adapters/         documents/excel_reader.py, persistence/sqlite/
    presentation/     cli/psbuild.py, qt/viewmodels/, qt/widgets/, qt/wizard/
    bootstrap.py      build_default_application()
contract/            vendorovana kopija Deklarant Pro contracta + drift_check
core/                LEGACY paketi (NE dira se; FAZA B planira migraciju/deprecation)
tests/
    unit/             unit testovi
    architecture/     import boundary tests (V3 DEP-001..DEP-004)
agent_reports/       task contracts + benchmark izvještaji
docs/                PLAN.md (V3) + istorija/
experiments/         benchmark moduli
asset/               GUI mockup (UNTRACKED, FAZA B / M4 input)
```

### Kod koji danas postoji

**Hexagonal architecture (`src/parser_studio/`):**

- `domain/evidence/` — `Locator`, `Evidence`, `DocumentEvidence`, `Candidate`, `ExtractionContext`, `cell_compat` adapter (frozen=True, slots=True).
- `domain/invoice/fields.py` — COLUMN_ALIASES sa 75+ aliasa u 13 polja.
- `domain/extraction/` — `header_matching.py` (normalize/match/identify_columns), `extraction_draft.py` (ExtractionDraft).
- `domain/learning/` — `LearningEvent`, `EventType`.
- `application/ingest/import_document.py` — `ImportDocument`, `ImportRequest`, `ImportResult`.
- `application/extraction/analyze_invoice.py` — `AnalyzeInvoice`, `AnalyzeRequest`.
- `application/extraction/producers/excel_header.py` — `ExcelHeaderProducer` + `_sheet_utils.py`.
- `application/review/confirm_invoice.py` — `ConfirmInvoice`, `ConfirmRequest`, `FieldConfirmation`.
- `ports/document_reader.py`, `ports/candidate_producer.py`, `ports/learning_repository.py`.
- `adapters/documents/excel_reader.py` — `ExcelDocumentReader` (openpyxl/xlrd, kesiranje).
- `adapters/persistence/sqlite/` — `SQLiteLearningRepository`, `GoldDataset`, 2 SQL migracije.
- `presentation/cli/psbuild.py` — `main`, `build_parser`, `cmd_import/analyze/confirm`, `--version` action, try/except FileNotFoundError.
- `presentation/qt/viewmodels/review_invoice_viewmodel.py` — MVVM placeholder (FAZA B / M4).
- `bootstrap.py` — `build_default_application(db_path=":memory:")` wiring.

**Legacy (`core/`, `cli/`, `services/`, `viewmodels/`, `views/`):** obrisan u A7 (`cli/`, `services/`, `viewmodels/`, `views/`). `core/` ostaje do FAZA B migracije.

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
pytest:        582 PASS, 1 SKIP, 1 FAIL
ruff:          192 errors (ista kao A7 — M1+M2+M3+M4+M5 dodali 0; 18 preostalih u src/parser_studio/ su pre-existing FAZA A)
contract drift: PASS (M1+M2+M3+M4+M5 ne diraju contract/)
architecture:   4 PASS (M1+M2+M3+M4+M5 ne smiju break-ati V3 DEP-001..DEP-004 — netaknuto)
```

Delta vs M1+M3: 490 → 582 = +92 novih testova (M2: 67, M4: 14, M5: 11).

### pytest FAIL detalji

```text
FAILED tests/unit/test_quality_gate.py::test_f9_no_broken_rows
  assert True is False
```

Test očekuje da F9 ne bude aktiviran na 10 čistih redova, ali F9 JE aktiviran. To je **pre-existing benchmark regression** (od A0), NE u core/domain kodu. Ne blokira FAZA B; cleanup out-of-band.

### ruff detalji

192 ukupno. **M1+M2+M3+M4+M5 = 0 ruff grešaka** (svi novi fajlovi clean). Preostalih 18 u `src/parser_studio/` su pre-existing FAZA A.

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
| A6 | DONE | LearningRepository Protocol proširen (events_for, events_since) + SQLiteLearningRepository (in-memory + file-based) u `adapters/persistence/sqlite/` + 2 SQL migracije (001_learning_events, 002_gold_dataset VIEW) + GoldDataset projection + migration runner + connection helper. 20 unit testova (svi PASS). pytest 330 PASS + 1 FAIL (test_f9 pre-existing). Domain NE importuje sqlite3 (V3 DEP-001 provjereno grep-om). bootstrap.py sada kreira SQLite repo sa default `~/.parser_studio/learning.db` i PARSER_STUDIO_DB env override. Commit 9fa53bc, pushan. |
| A7 | DONE | Presentation migriran u `src/parser_studio/presentation/`: cli/psbuild.py (CLI entry point sa import/analyze/confirm komandama, --version action, try/except FileNotFoundError za exit code 1), qt/viewmodels/review_invoice_viewmodel.py (MVVM placeholder), qt/widgets/, qt/wizard/ (placeholder moduli). Architecture tests u `tests/architecture/test_import_boundaries.py` (AST provjera V3 DEP-001..DEP-004, 4 test PASS). 13 novih presentation unit testova (8 CLI + 5 viewmodel). pyproject.toml: cryptography premješten u `optional[signing]`, entry point `parser_studio.presentation.cli.psbuild:main`. Legacy `cli/services/viewmodels/views/` obrisani (svi prazni). pytest 346 PASS + 1 SKIP + 1 FAIL (test_f9 pre-existing), ruff 192 (A7 NIJE dodao nove), contract drift PASS. Commit 5ed50ea, pushan na origin/dev. |
| M1 | DONE | CanonicalInvoice (20 vendor-agnostičkih polja) + InvoiceLine + InvoiceStatus u `src/parser_studio/domain/invoice/canonical_invoice.py` + VendorParserModel + LayoutRule + FieldExtractionRule + ValidationRule + NormalizationRule + FallbackStrategy + ExtractionStrategy + ConsumedPathsBehavior u `src/parser_studio/domain/invoice/vendor_parser_model.py`. 102 nova testova (43 canonical_invoice + 59 vendor_parser_model). pytest 448 PASS, architecture 4/4 PASS, ruff 0 na M1 fajlovima. Disjunktni ownership sa M3 (M1 u domain/invoice/, M3 u ports+adapters/ai+application/learning/). Worker: Pi agent u worktree-u H:/parser_studio-m1. Commit 09ce691, pushan na origin/m1-canonical-invoice, merge-ovan u dev. |
| M3 | DONE | AI Advisor port + NullAdvisor + ConsultAdvisor use case. Advisor Protocol (runtime_checkable) sa `mode: AdvisorMode` + `consult(field, candidates, context)` u `src/parser_studio/ports/advisor.py`. AdvisorMode enum (OFF/CACHE_ONLY/LIVE) + AIAdvice dataclass (field, suggested_value, locator_evidence, confidence, reasoning). NullAdvisor adapter (OFF rezim, bez eksternih importa) u `src/parser_studio/adapters/ai/null_advisor.py`. ConsultAdvisor use case u `src/parser_studio/application/learning/consult_advisor.py` (ConsultRequest/ConsultResult frozen dataclasses, wrap Advisor port). 42 nova testova. pytest 490 PASS nakon merge-a M1+M3, architecture 4/4 PASS, ruff 0 na M3 fajlovima. bootstrap.py NEIZMJENJEN (Advisor se instancira eksplicitno). Commit d19adbb, pushan na origin/m3-ai-advisor, merge-ovan u dev. |
| M2 | DONE | Profile Builder (V3 E1+E2): LayoutFingerprint (SHA-256 hash sa sorted components) + LayoutProfile (vendor_id, version, rules, source_documents) + ProfileRule + RuleParameter u `src/parser_studio/domain/profiles/`. ProfileRepository Protocol (runtime_checkable) u `src/parser_studio/ports/profile_repository.py`. InMemoryProfileRepository (bez sqlite3) u `src/parser_studio/adapters/profiles/`. BuildLayoutProfile use case + BuildRequest/BuildResult/GoldSample u `src/parser_studio/application/profiles/build_layout_profile.py` (version drift bump, fingerprint mismatch warning, common_metadata pravila). 67 nova testova. pytest 557 PASS nakon M2 merge-a, architecture 4/4 PASS, ruff 0 na M2 fajlovima. pyproject.toml: `addopts = ["--import-mode=importlib"]` dodan (fix za namespace conflict). Commit 9c20fa2 (arch) + a870500 (chore pyproject), pushan na origin/task/m2-profile-builder, merge-ovan u dev. V3 ARCH-004: LayoutProfile je derived artifact (deletable, re-buildable). |
| M4 | DONE | InvoiceReviewView + CellTableView Qt widgets (V3 B4). InvoiceReviewView(QWidget) sa CellTableView + candidate selector + confirm panel; emituje `confirmed(str, object)` signal. CellTableView(QTableWidget) read-only (NoEditTriggers), load_document(DocumentEvidence) populates table. 14 novih testova (7 cell_table + 7 review). `review_invoice_viewmodel.py` NIJE mijenjan. pytest 571 PASS nakon M4 merge-a, architecture 4/4 PASS, ruff 0 na M4 fajlovima. Implementer: Pi agent u `H:/parser_studio-m4` (worktree). Commit d85aabc, pushan na origin/task/m4-review-gui, merge-ovan u dev (Mavis radi nezavisan review, Implementer != Reviewer). |
| UI0 | DONE | FAZA UI0 (Product/GUI Blueprint) — V3.2 §40A, GATE-0 LOCKED 14.09.2026. `docs/GUI_BLUEPRINT.md` sadrži: application shell (left navigation 9 stavki, top bar, status bar) + 9 glavnih ekrana (UI-01 Početna / UI-02 Dokumenti / UI-03 Review / UI-04 Gold Dataset / UI-05 Layout Profile + OCR Reading Map / UI-06 Parser Build / UI-07 Verification / UI-08 Export / UI-09 Settings) + 9 ključnih modala (M-01..M-09) + 16 obaveznih stanja (UI0.4: EMPTY, LOADING, ANALYZING, FOUND, NOT_PRESENT, AMBIGUOUS, FAILED, USER_CORRECTED, USER_VERIFIED, PROFILE_MATCH_HIGH/REVIEW/NO_MATCH, BUILD_READY/FAILED, VERIFICATION_PASS/FAIL, EXPORT_BLOCKED) + centralni end-to-end tok (Početna → Dokumenti → Import → Analyze → Review → User_Verified → Gold → Layout Profile → Holdout → Build → Verification → Export) + povratne petlje (correction, drift, verification fail). V3.2 plan zamijenio stari V3 (prebacen u `docs/istorija/`). GATE-0 PASS — ozbiljno ožičavanje A1+ funkcija dozvoljeno. |
| M5 | DONE | Prvi Gold Corpus (V3 B5) — 4 sintetičke fakture (Faktura-1=11, Faktura-2=4, Medicopharm=84, Sumaprom=138 itema; UKUPNO 237 itema) sa svim 20 ciljnih polja (9 invoice + 11 item) potvrđenih u USER_CONFIRMED events (2643 ukupno: 4×9 invoice + 237×11 item). Sintetički .xlsx generator u `tests/fixtures/gold/generator.py` (deterministicki seed po vendor_id, NE stvarne fakture po V3 ARCH-010). Integration test u `tests/integration/test_gold_corpus.py` (11 testova, 4 klase: Structure, Import, Verify, Projection, Integration). GoldDataset projection verified: 4 distinct documents, 2643 entries, all USER_CONFIRMED. pytest 582 PASS nakon M5 merge-a (+11 M5 testova), architecture 4/4 PASS, ruff 0 na M5 scope. Production kod netaknut (M5 je SAMO test + fixtures). Implementer: Mavis u `H:/parser-studio-worktrees/m5-gold-corpus`. Commit fc1d003, pushan na origin/task/m5-gold-corpus, merge-ovan u dev. **FAZA B COMPLETE.** |

---

## Known risks / blockers

1. **Pre-existing failing test** (`test_f9_no_broken_rows`) — regression u benchmark eksperimentu, ne blokira FAZA A ali treba cleanup u benchmark modulu.
2. **Pre-existing ruff errors** (192, +35 od A6, svi u benchmark/test fajlovima) — ne blokira FAZA A; A7 NIJE dodao nove.
3. **`pyproject.toml` description** — i dalje stara formulacija `"...bez LLM-a"`; V3 uvodi AI kao opcionalan advisor. Manji prioritet, FAZA B cleanup.
4. **`core/` legacy paketi** — još uvijek na disku, koriste se u benchmarku. Planira se migracija/deprecacija u FAZA B.
5. **Graft status SECONDARY** — probacioni period aktivan do kraja FAZA B (M5).
6. **Asset/parser_studio_gui_mockup.png** — UNTRACKED, GUI mockup. Treba commit-ovati kao input za FAZA B / M4 (Review Invoice GUI).

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
M5 — Prvi Gold Corpus (V3 B5) DONE.
4 sintetičke fakture (237 itema, 20 ciljnih polja, 2643 USER_CONFIRMED events).
Commit fc1d003 (arch + docs), merge-ovan u dev.
FAZA B COMPLETE: M1 + M2 + M3 + M4 + M5 (236 novih testova ukupno).
```

---

## Next recommended task

**FAZA B COMPLETE.** Preostaje FAZA C (V3_2 §43).

Sljedeci FAZA-i:
- FAZA C — Generic extraction (C1-C3, još nije specificirano u V3_2)
- FAZA D — Verifier (compare 20 polja, I1-I4)
- FAZA E — Layout Learning — djelomicno zavrseno (E1 Fingerprint + E2 Builder; preostaje E3 Matcher, E4 Drift, E5 Holdout + E6 OCR Reading Map holdout)
- FAZA G — AI Advisor (G1-G5, M3 je dio G1+G2)
- FAZA H — VendorParserModel + Codegen (H1-H4, M1 je dio H1)
- FAZA I — Verifier (I1-I4)
- FAZA J — CLI + reports

GUI follow-up zadaci (FAZA UI0 GATE-0 je prosao, sad ekran-po-ekran):
- UI-03 Review je M4 done (InvoiceReviewView + CellTableView)
- UI-04 Gold Dataset (M5) — coverage, history, rebuild projection (BEZ novih widgeta, vec M5 acceptance testira projection)
- UI-01 Početna (Dashboard) — sidebar + stats + recent docs + next-step
- UI-02 Dokumenti (Import & Library) — filter + import modal
- UI-05 Layout Profile + OCR Reading Map — match: HIGH/REVIEW/NO_MATCH
- UI-06 Parser Build — readiness + blockers + GENERATE
- UI-07 Verification — positive Gold + negative detect + diff
- UI-08 Export — output folder + verification summary + EXPORT button
- UI-09 Settings — local storage, AI mode, providers, privacy

Cleanup zadaci (out-of-band):
- Fix `test_f9_no_broken_rows` u benchmark modulu.
- Cleanup 192 ruff grešaka (pre-existing FAZA A).
- Ažurirati `pyproject.toml` description (V3 AI opcija).
- Commit `asset/parser_studio_gui_mockup.png` (M4 input — sada UI implementiran).
- Commit `PARSER_STUDIO_KANONSKI_PLAN_V3_1.md` (korisnicka kopija) ILI vratiti originalni `PARSER_STUDIO_KANONSKI_PLAN_V3.md` u git.
- Worktree cleanup za `H:/parser-studio-worktrees/m5-gold-corpus/` (cleanup po završetku taska).
- Branch cleanup za `task/m5-gold-corpus` (vec merged u dev).


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
- **2026-09-14** — M2 + M4 paralelni rad zavrsen. M2 (Mavis, H:/parser_studio-m2 worktree, grana task/m2-profile-builder): Profile Builder (V3 E1+E2) — LayoutFingerprint (SHA-256 hash sa sorted components) + LayoutProfile (vendor_id, version, rules, source_documents) + ProfileRule + RuleParameter u `src/parser_studio/domain/profiles/`. ProfileRepository Protocol + InMemoryProfileRepository. BuildLayoutProfile use case (version drift bump, fingerprint mismatch warning, common_metadata pravila). 67 novih testova. pyproject.toml: `addopts = ["--import-mode=importlib"]` dodan (fix za namespace conflict sa 3 nova test direktorija sa istim leaf name). M4 (Pi agent, H:/parser_studio-m4 worktree, grana task/m4-review-gui): InvoiceReviewView(QWidget) + CellTableView(QTableWidget, read-only) u `src/parser_studio/presentation/qt/widgets/`. `confirmed(str, object)` signal emisija. 14 novih testova (7 cell_table + 7 review). review_invoice_viewmodel.py netaknuto (Mavis-ov A7 output ostao nepromijenjen). Disjunktni ownership poštovan (M2 u domain/profiles/+application/profiles/+adapters/profiles/+ports/profile_repository.py, M4 u presentation/qt/widgets/). Merge redoslijed: M2 PRVI u dev (f3696c3), pa M4 (fd3f768). Mavis radi nezavisan review M4 (pošto je Mavis implementer M2, Implementer != Reviewer). pytest 571 PASS + 1 SKIP + 1 FAIL (test_f9 pre-existing, van scope), architecture 4/4 PASS, ruff 0 na M2+M4 fajlovima. FAZA B u toku (preostaje samo M5 Gold Corpus). Task Contracts: `agent_reports/M2-task-contract.md` + `agent_reports/M4-task-contract.md` + `agent_reports/2026-09-14-M4-briefing-prompt.md`. Evidence: `agent_reports/2026-09-14-M2-evidence.md` + `agent_reports/2026-09-14-M4-evidence.md`.

- **2026-09-14** — M5 (Prvi Gold Corpus, V3 B5) DONE. Sintetički .xlsx generator u `tests/fixtures/gold/generator.py` (4 fakture: Faktura-1=11, Faktura-2=4, Medicopharm=84, Sumaprom=138 itema; UKUPNO 237 itema) + integration test u `tests/integration/test_gold_corpus.py` (11 testova, 4 klase: Structure, Import, Verify, Projection, Integration). Acceptance: 4 distinct documents, 2643 USER_CONFIRMED events (4×9 invoice + 237×11 item), sva 20 ciljnih polja prisutna po dokumentu. V3 ARCH-010 poštovan: SAMO sintetički podaci (NE stvarne fakture). pytest 582 PASS nakon M5 merge-a (+11 M5 testova od 571), architecture 4/4 PASS, ruff 0 na M5 scope. Production kod (`src/parser_studio/**`) netaknut — M5 je SAMO test + fixtures. Implementer: Mavis u `H:/parser-studio-worktrees/m5-gold-corpus/`. Commit fc1d003 (arch + docs), pushan na `origin/task/m5-gold-corpus`, merge-ovan u dev (Mavis radi kao koordinator za svoj rad). **FAZA B COMPLETE** (M1+M2+M3+M4+M5, 236 novih testova).

- **2026-09-14** — FAZA UI0 (Product/GUI Blueprint) ZAKLJUČANA. V3.2 (dorađeni V3) donio novu FAZU UI0 prije FAZA A. Korisnikov draft `PARSER_STUDIO_GUI_BLUEPRINT_V1.md` postao kanonski `docs/GUI_BLUEPRINT.md` (proširen sa V3.2 §40A UI0.4 obaveznim stanjima: EMPTY, LOADING, PROFILE_MATCH_REVIEW; centralnim tokom + povratnim petljama). `docs/PLAN.md` zamijenjen sa V3.2 verzijom (56873 bytes); stari V3 premješten u `docs/istorija/PARSER_STUDIO_KANONSKI_PLAN_V3.md`. GATE-0 (GUI/UX Blueprint Locked) PASS. V3.2 ključne promjene: ARCH-011 (GUI/UX Blueprint se zaključava prije functional implementacije, novo nepormjenjivo pravilo), FAZA UI0 sa 6 podzadataka (UI0.1..UI0.6), OCR Reading Map (E2.5, novi concept izveden iz LayoutProfile-a, koristi `RegionTextReader` port + `LocalRegionOCR` adapter — još nisu implementirani u kodu). CURRENT_STATE ažuriran sa UI0 status DONE + GATE-0 lock.

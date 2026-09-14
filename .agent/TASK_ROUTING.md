# Parser Studio — Task Routing

Agent čita najmanje:

```text
AGENTS.md
CLAUDE.md
docs/PLAN.md
.agent/CURRENT_STATE.md
.agent/PROJECT_MAP.md
agent_reports/<TASK-ID>-task-contract.md
```

Ova datoteka dodaje **specifičan read-set za kategoriju taska**.

---

## Architecture / Refactor

Čitaj:

```text
docs/PLAN.md                              (V3 sekcija 41: FAZA A)
.agent/CURRENT_STATE.md                   (trenutni A0–A7 status)
.agent/PROJECT_MAP.md                     (sekcija C: MIGRATION MAP)
tests/architecture/test_import_boundaries.py  (ako postoji)
relevantni legacy source (core/, services/, views/, cli/)
relevantni target source (src/parser_studio/...)
relevantni testovi u tests/unit/ i tests/integration/
```

Ne čitaj UI/Presentation detalje po defaultu.

Ne diraj `contract/` osim ako task eksplicitno zahtijeva drift.

---

## Domain / Evidence

Čitaj:

```text
domain/evidence/                          (Locator, Evidence, DocumentEvidence)
domain/invoice/                           (models, fields, status)
domain/extraction/                        (candidate, context, header_matching)
domain/learning/                          (events, models, projections)
relevantne unit testove u tests/unit/domain/
```

Ne čitaj UI po defaultu.

Ne importuj `adapters/`, `presentation/`, `contract/`, `sqlite3`, `PySide6`, `docling`, `openpyxl`, `xlrd` iz domain koda.

---

## Application / Use Case

Čitaj:

```text
relevantni domain/
ports/                                    (samo one portove koje use-case koristi)
konkretan application workflow fajl
tests/unit/application/ (ako postoji)
```

Ne importuj `adapters/`, `presentation/`, `PySide6`, `sqlite3`, `docling`, `openpyxl`, `xlrd` iz application koda.

Ako use-case treba novi port, definiraj ga u `ports/` prvo.

---

## Adapter

Čitaj:

```text
odgovarajući port u ports/
domain model koji adapter proizvodi ili konzumira
sam adapter
integration testove za adapter
```

Adapter smije koristiti konkretnu tehnologiju (openpyxl, docling, sqlite3, httpx, Jinja2).

Adapter NE smije importovati `presentation/` niti drugi adapter (osim ako je to nužno i dokumentovano).

---

## Excel

Čitaj:

```text
ports/document_reader.py
domain/evidence/                          (Evidence, Locator)
adapters/documents/excel_reader.py        (ili core/documents/excel_document.py tokom migracije)
domain/extraction/header_matching.py      (kada se uvede)
tests/unit/ testove za ExcelDocument / ExcelHeaderProducer
```

Stari kod: `core/documents/excel_document.py`, `core/engines/excel_headers.py`.

`openpyxl` i `xlrd` su isključivo u Excel adapteru.

---

## Docling / PDF

Čitaj:

```text
ports/document_reader.py
domain/evidence/locator.py                (Locator.page, bbox)
adapters/documents/docling_reader.py      (kada se uvede — M3)
adapters/documents/rasterizer.py          (kada se uvede)
experiments/document_engines/benchmark/  (za postojeći benchmark kod)
tests/integration/ PDF/real-data testove
```

Raw Docling output za stvarne fakture: lokalni cache, NE u Git.

---

## Learning / SQLite

Čitaj:

```text
domain/learning/                          (LearningEvent, models, projections)
ports/learning_repository.py
adapters/persistence/sqlite/              (connection, migrations, learning_repository, projections)
relevantne migrations fajlove
tests za persistence (kad se uvedu)
```

Domain ne smije importovati `sqlite3`.

Learning događaji su append-only; nikad ne prepisuj istoriju.

Stvarni poslovni podaci iz learning_events ne idu u Git.

---

## Review / PySide6

Čitaj:

```text
presentation/qt/                          (views, viewmodels, widgets)
odgovarajuće application use-caseove
tests/presentation/ (kad se uvedu)
```

GUI ne smije direktno:

```text
otvarati SQLite
zvati Docling
otvarati Excel preko openpyxl
pozivati AI transport
pokretati codegen template
pokretati subprocess verifier
```

GUI uvijek ide preko application use-case-a (MVVM).

---

## Layout / Profile

Čitaj:

```text
domain/profiles/                          (models, fingerprint, rules)
application/profiles/                     (build_profile, match_profile)
domain/learning/                          (za Gold projection)
relevantne evaluation testove
```

Profil se gradi iz Gold podataka, nikad obrnuto.

---

## AI

Čitaj:

```text
ports/advisor.py
domain/extraction/candidate.py            (Candidate, ai_assisted flag)
domain/evidence/locator.py                (za grounding)
adapters/ai/                              (kad se uvede)
GRAFT_ADOPTION_PLAYBOOK.md                (NE — to je za development alat, ne za runtime AI)
```

`PS_AI_MODE=off` je default.

AI kandidat mora imati `Locator` + `evidence`.

Grounding: NFKC + collapsed whitespace + case-insensitive; BEZ fuzzy.

---

## Codegen

Čitaj:

```text
domain/parser_model/vendor_parser_model.py
ports/parser_generator.py
adapters/codegen/                         (generator, guards, templates/)
contract/                                 (za ImportResult contract)
tests za generisani parser
```

Generisani `.py`:

- NE smije importovati `parser_studio`.
- NE smije imati `eval`, `exec`, `__import__`, `from parser_studio ...`.
- MORA proći `ast.parse()` + `compile()` + import allowlist + ruff.

---

## Verification

Čitaj:

```text
ports/parser_verifier.py
application/verification/                 (pravila)
adapters/verification/                    (subprocess)
domain/learning/                          (za Gold compare)
domain/invoice/                           (za 20-polja compare)
negative detect corpus                    (kad se uvede)
```

Verifier pokreće stvarni `.py` u zasebnom procesu (stabilnost, NE sigurnosni sandbox).

Export je dozvoljen samo ako:

```text
pozitivni Gold testovi PASS
negative detect testovi PASS
sva obavezna polja odgovaraju
nema neriješenog pravno značajnog konflikta
svi AI-assisted elementi su USER_VERIFIED
nema Parser Studio runtime importa
```

---

## Deklarant Pro Contract

Čitaj:

```text
contract/                                 (vendorovana kopija)
contract/drift_check.py
H:/deklarant_pro/                         (read-only, ako je lokalno dostupan)
adapters/declarant_pro/                   (kad se uvede)
```

**Nikad ne mijenjaj Deklarant Pro u okviru Parser Studio taska** bez eksplicitne odluke Human Ownera.

Za drift check:

```bash
python -m contract.drift_check "$DEKLARANT_PRO_ROOT"
```

Ako `$DEKLARANT_PRO_ROOT` nije postavljen, drift check ostaje `NOT VERIFIED` (NE `PASS`).

---

## Performance / Metrics

**NE RADITI** u Parser Studio razvoju dok GATE-3 (B5 — Full Gold corpus) nije prošao.

Ako task zahtijeva performance, prijaviti kao `OUT_OF_SCOPE_FINDING` i vratiti se na `docs/PLAN.md` sekcija 56 ("Šta se trenutno NE radi").

---

## Kada nisi siguran

1. Pogledaj `AGENTS.md` sekciju "Zabranjeni prečaci".
2. Pogledaj `docs/PLAN.md` sekciju 3 (nepromjenjive odluke) i sekciju 55 (pravila rada).
3. Pogledaj `.agent/CURRENT_STATE.md` — šta je već urađeno.
4. Pogledaj stvarni kod.
5. Prijavi konflikt.

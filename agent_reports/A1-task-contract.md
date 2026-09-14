---
task_id: A1
title: "src/parser_studio/ package layout — kreiranje nove fizičke strukture"
status: DONE
risk: MEDIUM
date: 2026-09-14
branch: dev (base)
worktree: TBD
---

# A1 — `src/parser_studio/` package layout

> Kreiranje nove fizičke strukture Parser Studija prema V3 sekcija 6 i 18, BEZ funkcionalne promjene. Logika ostaje u legacy `core/services/views/cli` do A2–A7; A1 samo priprema novi layout i `pyproject.toml`.

---

## Roles

```text
Human Owner:    <tvoj unos>
Coordinator:    Claude Code
Implementer:    <tvoj unos — Claude | Pi | Crush | MiniMax>
Reviewer:       <tvoj unos — Codex | drugi nezavisni>
```

**Implementer != reviewer.** Ako se moraju poklopiti, prijaviti kao nalaz.

---

## Canonical references

```text
docs/PLAN.md                                  (V3, sekcija 6: konačna package struktura; sekcija 18: R1; sekcija 41: A1)
.agent/PROJECT_MAP.md                         (sekcija B: TARGET ARCHITECTURE MAP)
.agent/PROJECT_MAP.md                         (sekcija C: MIGRATION MAP)
.agent/TASK_ROUTING.md                        (sekcija "Architecture / Refactor")
agent_reports/2026-09-14-graft-evaluation.md  (Graft SECONDARY pravila)
pyproject.toml                                (trenutno stanje)
```

---

## Current-state preconditions

Provjeriti prije početka:

```text
[ ] branch: dev na 589e12d (framework commit)
[ ] baseline testovi: 180 PASS, 1 FAIL (test_f9_no_broken_rows), 1 SKIPPED — DOKUMENTOVANO u CURRENT_STATE
[ ] ruff: 157 errors (pretežno benchmark/test fajlovi) — DOKUMENTOVANO u CURRENT_STATE
[ ] contract drift: PASS
[ ] Graft status: SECONDARY (probacioni period)
[ ] DEKLARANT_PRO_ROOT: H:/deklarant_pro
```

A0 acceptance je ZAVRŠEN. A1 može krenuti.

---

## Problem

V3 sekcija 6 zahtijeva novu fizičku strukturu:

```text
src/parser_studio/
    domain/
    application/
    ports/
    adapters/
    presentation/
```

Trenutno stanje:

```text
cli/                  legacy entry point
core/                 legacy paketi
contract/             TRANSITIONAL (u root-u)
services/             prazno, legacy
viewmodels/           prazno, legacy
views/                prazno + views/wizard/
```

**NEMA** `src/parser_studio/` direktorijuma. Domain modeli, portovi, adapteri, use case-ovi iz V3 **ne postoje**.

`pyproject.toml` nema `[tool.setuptools.packages.find] where = ["src"]`, pa `pip install -e .` instalira sa root-a umjesto iz novog layouta.

---

## Goal

Kreirati **prazan** `src/parser_studio/` skelet sa svim V3 poddirektorijima, te podesiti `pyproject.toml` da prepozna novu strukturu. BEZ migracije poslovne logike (to su A2–A7).

Acceptance: testovi i dalje zeleni (ista PASS/SKIP statistika kao baseline), nema novih grešaka.

---

## In scope

### Novi direktorijumi

```text
src/parser_studio/
    __init__.py
    domain/
        __init__.py
        invoice/__init__.py
        evidence/__init__.py
        extraction/__init__.py
        learning/__init__.py
        profiles/__init__.py
        parser_model/__init__.py
    application/
        __init__.py
        ingest/__init__.py
        extraction/__init__.py
        review/__init__.py
        learning/__init__.py
        profiles/__init__.py
        generation/__init__.py
        verification/__init__.py
    ports/__init__.py
    adapters/__init__.py
    presentation/__init__.py
    bootstrap.py
```

**Samo `__init__.py` fajlovi** — prazni (ili sa kratkim docstring-om "owns / does not own").

### `bootstrap.py`

Minimalni composition root:

```python
"""Parser Studio composition root.

Drži wiring između use case-ova, portova i adaptera.
Trenutno prazan — popunjava se u A5 (application use cases).
"""
```

### `pyproject.toml` izmjene

```toml
[tool.setuptools.packages.find]
where = ["src"]
include = ["parser_studio*"]
```

**Opciono (preporučeno, ALI može u A7):**

```toml
[project.scripts]
psbuild = "parser_studio.presentation.cli.psbuild:main"
```

ALI — `presentation/cli/psbuild.py` ne postoji. Ova izmjena NE MOŽE ići u A1. Ostaviti na staro:

```toml
[project.scripts]
psbuild = "cli.psbuild:main"
```

do A7 (Presentation migration).

### Test pythonpath

Verifikovati da `pytest` radi iz novog layouta:

```bash
python -m pytest -q
```

Ako pythonpath ne uključuje `src/`, dodati u `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src", "."]
```

ALI — OBA `src/` i `.` mogu konfliktovati (legacy importi koriste `from core.X import ...`). Testirati pa odlučiti.

---

## Out of scope

Sljedeće je EKSPLICITNO van A1:

```text
- Migracija bilo kojeg fajla iz core/services/views/cli u src/parser_studio/...
  (to su A2–A7)
- Kreiranje domain modela (Locator, Evidence, DocumentEvidence, Candidate)
  (A2)
- Migracija ExcelDocument u adapters/documents/excel_reader.py
  (A3)
- Ukinuti Engine koncept, uvesti CandidateProducer
  (A4)
- Application use case-ovi (ImportDocument, AnalyzeInvoice, ...)
  (A5)
- LearningRepository + SQLite adapter
  (A6)
- Presentation migracija (views → presentation/qt/, cli → presentation/cli/)
  (A7)
- Docling adapter (FAZA B, M3)
- Review GUI (FAZA B, M4)
- Gold corpus (FAZA B, M5)
- AI Advisor (FAZA G)
- Codegen, Verifier, CLI export (FAZA H-J)
- Fix test_f9_no_broken_rows regression u benchmark eksperimentu
  (zaseban cleanup task — NIJE core/domain kod)
- Cleanup 157 ruff grešaka (pretežno benchmark/test fajlovi)
  (zaseban cleanup task)
- Uklanjanje cryptography iz pyproject.toml dependencies
  (preporuka V3 sekcija 16, ali može ići u zaseban task jer nije layout)
- Update pyproject.toml description ("Alat za poluautomatsko pravljenje...")
  (V3 sekcija 16, ali može u zaseban task)
- Uklanjanje legacy core/services/views/cli direktorijuma
  (V3 sekcija 20: tek kad A2–A7 završe; do tada compatibility shim po potrebi)
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
Novi:           src/parser_studio/ sa svim __init__.py
                src/parser_studio/bootstrap.py (minimalni)
Izmijenjeni:    pyproject.toml ([tool.setuptools.packages.find])
Opcioni:        pyproject.toml ([tool.pytest.ini_options] pythonpath)
Obrisani:       nijedan
Premješteni:    nijedan
```

---

## Architecture boundaries

A1 NE SMIJE probiti:

```text
[ ] domain → adapters / presentation / PySide6 / sqlite3 / Docling / openpyxl / xlrd / contract
[ ] application → adapters / presentation
[ ] ports → adapters / presentation
[ ] presentation → direktno sqlite3 / Docling / openpyxl / AI transport
[ ] legacy core/ → novi src/parser_studio/  (smjer je dozvoljen SAMO kroz compatibility shim sa planom uklanjanja)
```

Ako treba probiti bilo koju granicu, **prijaviti koordinatoru** prije početka.

---

## Compatibility requirements

```text
[ ] Svi postojeći testovi i dalje rade (ista PASS/SKIP statistika)
    - Provjeriti: pytest 180 PASS, 1 FAIL (test_f9_no_broken_rows), 1 SKIPPED
[ ] Svi legacy importi i dalje rade
    - core/documents/base.py, core/engines/excel_headers.py, cli/psbuild.py
    - contract/drift_check.py, contract/import_result.py, itd.
[ ] NEMA compatibility shim-ova između novog i starog layouta u A1
    - shim se uvodi tek u A2 (Cell → Evidence) ili kasnije
[ ] NEMA parallel "core/" + "src/" business koda
    - src/parser_studio/ ostaje PRAZAN (samo __init__.py + bootstrap.py)
```

---

## Acceptance criteria

```text
[ ] src/parser_studio/ postoji sa svim V3 poddirektorijima (15+ __init__.py)
[ ] bootstrap.py postoji (minimalni, bez logike)
[ ] pyproject.toml ima [tool.setuptools.packages.find] where = ["src"]
[ ] python -m pytest -q: isti rezultat kao baseline (180 PASS, 1 FAIL, 1 SKIPPED)
[ ] python -m ruff check .: NE SMIJE imati više grešaka od baseline (157)
[ ] python -m contract.drift_check "$DEKLARANT_PRO_ROOT": PASS (isti kao baseline)
[ ] python -c "import parser_studio.bootstrap" radi bez greške (sanity)
[ ] git diff --stat base..HEAD pokazuje samo nove src/ i izmjenu pyproject.toml
[ ] NEMA novih import putanja između legacy i novog layouta
[ ] NEMA business logike u src/parser_studio/ (samo skelet)
[ ] CURRENT_STATE ažuriran sa A1 statusom
[ ] Architecture testovi (kad se uvedu) PASS za novu strukturu — NOT_YET u A1
```

---

## Required tests

```text
Unit (postojeći, moraju ostati zeleni):
- tests/unit/test_contract.py
- tests/unit/test_excel_document.py
- tests/unit/test_excel_headers_engine.py
- tests/unit/test_quality_gate.py (1 FAIL prihvatljivo — benchmark regression)
- tests/unit/test_normalization.py
- tests/unit/test_table_classifier.py
- tests/unit/test_table_stitcher.py
- tests/unit/test_semantic_resolver.py
- tests/unit/test_price_amount_resolver.py
- tests/unit/test_invoice_meta_extractor.py

Integration:    nijedan u A1
Architecture:   NOT_YET (uvodi se u A2 acceptance)
```

---

## Impact analysis required (Graft SECONDARY period)

```text
[Da] MEDIUM/HIGH risk — Graft impact za nove __init__.py i bootstrap.py

Simboli za praćenje:
- parser_studio (top-level package)
- parser_studio.bootstrap
- src/ (novi layout)

Alati:
- graft build                # reindeksirati poslije izmjene
- graft grep "parser_studio" # provjeriti da nema false positive
- graft blast                # diff working tree vs HEAD
- ručni grep fallback        # za .md i neindeksirane fajlove
```

**"Zero callers" NIJE dovoljno** (potvrđeno na `Cell`). Graft `callers` + `grep` zajedno za svaku izmjenu.

---

## Risks

```text
1. Pyproject.toml promjena može slomiti `pip install -e .`.
   Mitigacija: pokrenuti odmah poslije izmjene. Ako pukne, revert i dokumentovati.

2. Pytest pythonpath konfiguracija može biti dvosmislena (`src/` vs `.`).
   Mitigacija: testirati pa odlučiti. Ako `pythonpath = ["src", "."]` puca legacy import,
   koristiti `pythonpath = ["src"]` i prilagoditi legacy import putanje.

3. CLI entry point (`psbuild = "cli.psbuild:main"`) postaje neupotrebljiv ako
   cli/psbuild.py premjesti prerano.
   Mitigacija: NE migrirati cli/ u A1. Ostaje u root-u. Migracija ide u A7.

4. Pytest može prijaviti "no tests collected" ako pythonpath ne uključuje `tests/`.
   Mitigacija: provjeriti `[tool.pytest.ini_options] testpaths = ["tests"]`.

5. .ignore / .gitignore Graft pravila mogu uticati na novi layout.
   Mitigacija: `graft build` reindeksira, `git diff .gitignore` poslije.
```

---

## Execution evidence required

Implementer mora dostaviti:

```text
[ ] git diff --stat base..HEAD (samo nove src/ i pyproject.toml)
[ ] python -m pytest -q stvarni izlaz
[ ] python -m ruff check . stvarni izlaz
[ ] python -m contract.drift_check "$DEKLARANT_PRO_ROOT" stvarni izlaz (AKO DEKLARANT_PRO_ROOT dostupan)
[ ] python -c "import parser_studio.bootstrap" stvarni izlaz
[ ] graft build output (reindeksiranje)
[ ] graft blast output (diff working tree vs HEAD)
[ ] File:line dokaz za svaku tvrdnju o prihvatljivim PASS/SKIP statistikama
```

**Self-reported "PASS" bez stvarnog izlaza nije prihvatljiv.**

---

## Reviewer evidence

Reviewer (Codex ili drugi nezavisni):

```text
[ ] vlastiti git diff review (bez self-reporta)
[ ] vlastiti pytest -q reprodukcija
[ ] vlastiti ruff check reprodukcija
[ ] vlastiti import sanity provjera
[ ] R-001 ... nalazi sa severity, location, evidence, required action
[ ] konačni verdict: PASS / PASS_WITH_NOTES / FAIL
```

---

## Integration gate

Prije merge-a:

```text
[ ] Implementer != Reviewer
[ ] Svi acceptance criteria zadovoljeni
[ ] CURRENT_STATE.md ažuriran (A1: NOT_STARTED → DONE)
[ ] nema stvarnih faktura / poslovnih podataka u Git diffu
[ ] nema secret / token podataka u Git diffu
[ ] Post-merge integration gate: ponoviti pytest + ruff na origin/dev HEAD
```

---

## Definition of Done — A1

```text
[ ] src/parser_studio/ kreiran sa svim V3 poddirektorijima (15+ __init__.py)
[ ] bootstrap.py kreiran (minimalni, bez logike)
[ ] pyproject.toml: [tool.setuptools.packages.find] where = ["src"]
[ ] pythonpath podešen (ako je potrebno)
[ ] pytest ista statistika (180 PASS, 1 FAIL, 1 SKIPPED)
[ ] ruff ne više od baseline (≤157)
[ ] contract drift PASS
[ ] import parser_studio.bootstrap radi
[ ] Graft blast čist
[ ] CURRENT_STATE A1: DONE
[ ] commit + push na dev
```

---

## Notes

- A1 je **čist layout + tooling task**, NE business refactor.
- Ako se tokom A1 otkrije da treba više od layout + pyproject.toml (npr. mora se pomjerati `cli/psbuild.py`), zaustaviti i prijaviti.
- Ako `pyproject.toml` promjena pukne `pip install -e .` (što utiče na CI), NE forsirati — prijaviti i tražiti alternativu (npr. ostaviti `packages.find` prazno, samo dodati `pythonpath = ["src"]` za pytest).

---

## Final status

```text
[ ] DRAFT
[ ] ACTIVE  (implementer radi)
[ ] REVIEW  (implementer završio, reviewer pregleda)
[ ] DONE    (reviewer PASS + Human Owner odobrio)
[ ] CANCELLED (obustavljeno; obrazložiti)
```

---

## OUT_OF_SCOPE_FINDING (popunjava implementer)

```text
OUT_OF_SCOPE_FINDING #1:
<opis>
<zašto je izvan scope-a>
<prijedlog kako riješiti>
```

(ostavi prazno ako nema nalaza)

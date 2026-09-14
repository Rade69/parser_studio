# FAZA C Evidence — Generic extraction (V3_2 §43)

**Date:** 2026-09-14
**Phase:** FAZA C (Generic extraction)
**Implementer:** Mavis (serijski default po user preference)
**Worktree:** `H:/parser-studio-worktrees/faza-c/`
**Branch:** `task/faza-c`
**Merge commit:** `12a1ccb` (no-ff merge u dev)
**CURRENT_STATE update:** `c196e82`

---

## Scope delivered

5 podzadataka, 148 novih testova, architecture 4/4 PASS, ruff FAZA C clean.

| ID | Opis | Fajlova | Testova | Commit |
|---|---|---|---|---|
| C1 | Concept library (20 polja × 4 jezika) | 3 src + 3 test | 34 | `e3ba97e` |
| C2 | 5 Candidate producers + `_normalize_for_match` lokalni fix | 5 src + 5 test | 37 | `b9ccfb9` |
| C3 | ResolveCandidates use case (3 strategije) | 1 src + 1 test | 18 | `bbab674` |
| C4 | 6 Validators (Syntax/Structure/Arithmetic/Domain/CrossField/CrossDocument) | 6 src + 6 test | 43 | `b2f8e97` |
| C5 | RealGoldEvaluator + EvaluationReport + DocumentEvaluation | 1 src + 2 test | 16 | `8dd2ece` |
| — | Ruff cleanup (F401×3 + SIM102 u `excel_header.py`) | 1 src | 0 | `c3d2174` |
| — | CURRENT_STATE status update | 1 doc | 0 | `c196e82` |

**Total:** 40 files changed, 4237 insertions, 26 deletions.

---

## Stvarni pytest output

FAZA C scope (163 testova — svi PASS):

```text
tests/unit/domain/concepts/ tests/unit/application/extraction/ tests/integration/test_real_gold_evaluation.py
........................................................................ [ 44%]
........................................................................ [ 88%]
...................                                                      [100%]
163 passed in 0.55s
```

Full regresija (730 PASS + 1 SKIP + 1 FAIL — isti baseline kao M5):

```text
1 failed, 730 passed, 1 skipped in 60.13s (0:01:00)
FAILED tests/unit/test_quality_gate.py::test_f9_no_broken_rows
  assert True is False
```

`test_f9_no_broken_rows` je **pre-existing benchmark regression** (od A0), ne blokira FAZA C; cleanup out-of-band.

---

## Stvarni ruff output

```text
$ python -m ruff check src/parser_studio/domain/concepts/ src/parser_studio/application/extraction/ tests/unit/domain/concepts/ tests/unit/application/extraction/ tests/integration/test_real_gold_evaluation.py tests/integration/real_gold/
All checks passed!
```

Ruff globalni (FAZA C ne dodaje nove):

```text
192 errors (ista kao M5; preostali su pre-existing FAZA A)
```

---

## Stvarni architecture test output

```text
$ python -m pytest tests/architecture/test_import_boundaries.py -q
....                                                                     [100%]
4 passed in 0.05s
```

V3 DEP-001..DEP-004 netaknuti: domain ne importuje adapters/presentation/sqlite3/openpyxl/xlrd/contract; application ne importuje adapters/presentation; ports ne importuje adapters/presentation.

---

## Stvarni git output

### Commits na `task/faza-c` grani

```text
c3d2174 chore(FAZA C): ruff clean u producers/excel_header.py
8dd2ece arch(FAZA C/C5): RealGoldEvaluator — accuracy measurement za GATE-3 (V3_2 §43.5)
b2f8e97 arch(FAZA C/C4): Validators — 6 validatora za ExtractionDraft (V3_2 §43.4)
bbab674 arch(FAZA C/C3): ResolveCandidates use case — FIRST_MATCH/HIGHEST_CONFIDENCE/CONSENSUS (V3_2 §43.3)
b9ccfb9 arch(FAZA C/C2): Candidate producers — LabelRight/LabelBelow/TableHeader/ColumnContent/ValueShape (V3_2 §43.2)
e3ba97e arch(FAZA C/C1): Concept library — sinonimi i kontekst za 20 ciljnih polja × 4 jezika
b9bb472 docs(FAZA C): M6 task contract — C1-C5 Generic extraction (V3_2 §43)
```

### Push

```text
$ git push -u origin task/faza-c
 * [new branch]      task/faza-c -> task/faza-c
branch 'task/faza-c' set up to track 'origin/task/faza-c'.
```

### Merge u dev

```text
$ git merge --no-ff origin/task/faza-c -m "merge(FAZA C): Generic extraction — C1-C5 (V3_2 §43)"
Merge made by the 'ort' strategy.
...
 create mode 100644 tests/unit/application/extraction/validators/test_arithmetic.py
 create mode 100644 tests/unit/application/extraction/validators/test_cross_document.py
 ...
```

### Push dev

```text
$ git push origin dev
   b9bb472..12a1ccb  dev -> dev
```

### Diff stat (M5 base → FAZA C merge)

```text
40 files changed, 4237 insertions(+), 26 deletions(-)
```

---

## Ključne odluke tokom FAZA C

1. **`_normalize_for_match` lokalni u `Concept`** (NE u `domain/extraction/header_matching.py`) jer domain/concepts ne smije ovisiti o domain/extraction (V3 DEP-001). Dupliran je logika u `concept.py`.
2. **Resolver strategija**: prioritet po producer confidence (excel_header=0.90, table_header=0.85, label_right=0.80, label_below=0.75, column_content=0.70, value_shape=0.60). HIGHEST_CONFIDENCE je default.
3. **ArithmeticValidator V3 ARCH-009**: NE izmišlja vrijednosti, SAMO flaggira (tolerance 0.02).
4. **CrossDocumentValidator placeholder INFO**: implementacija u FAZA D (Oracle bootstrap).
5. **Količina validator**: hrvatski decimal separator (`,`) → tocka (`replace(",", ".")`).
6. **Ruff cleanup kao poseban commit** (c3d2174) umjesto rebase/amend na C2 commit — sigurnija opcija.

---

## FAZA C acceptance summary

| Acceptance criterion | Status | Dokaz |
|---|---|---|
| C1 Concept library sa 80 koncepata (20 polja × 4 jezika) | PASS | `e3ba97e` commit + 34 testova |
| C2 5 producers (LabelRight/LabelBelow/TableHeader/ColumnContent/ValueShape) | PASS | `b9ccfb9` commit + 37 testova |
| C3 Resolver sa FIRST_MATCH/HIGHEST_CONFIDENCE/CONSENSUS | PASS | `bbab674` commit + 18 testova |
| C4 6 validators + ArchitectureValidator poštuje V3 ARCH-009 | PASS | `b2f8e97` commit + 43 testa |
| C5 RealGoldEvaluator + integration sa M5 Gold korpusom | PASS | `8dd2ece` commit + 16 testova |
| Architecture tests (4/4 PASS) | PASS | V3 DEP-001..DEP-004 netaknuti |
| Ruff FAZA C scope clean | PASS | All checks passed! |
| Full pytest 730 + 1 SKIP + 1 FAIL (test_f9 pre-existing) | PASS | Isti baseline kao M5 |
| Contract drift | PASS | FAZA C ne dira contract/ |
| Production kod (src/parser_studio/) poštuje V3 DEP granice | PASS | domain NE importuje application/ports/adapters/presentation |
| Disjunktni ownership (FAZA C samo u dogovorenim fajlovima) | PASS | domain/concepts/, application/extraction/{producers,resolve,validators}, tests/integration/real_gold/ |

**FAZA C COMPLETE.**

---

## Preostali rizici

1. **test_f9_no_broken_rows** — pre-existing benchmark regression, čeka cleanup.
2. **Ruff globalni 192** — pre-existing FAZA A, FAZA C nije dodala nove.
3. **CrossDocumentValidator placeholder** — implementacija u FAZA D.

---

## Sljedeći korak

**FAZA D — Oracle bootstrap** (V3_2 §44): compare vendor parser output vs Gold dataset (M5 korpus + C5 RealGoldEvaluator).
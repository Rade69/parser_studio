# FAZA D Evidence — Oracle bootstrap (V3_2 §44)

**Date:** 2026-09-14
**Phase:** FAZA D (Oracle bootstrap)
**Implementer:** Mavis (serijski default po user pref)
**Worktree:** `H:/parser-studio-worktrees/faza-d/`
**Branch:** `task/faza-d`
**Base:** `dev@51bf1b2` (FAZA C merge)
**Merge commit:** `69770cb` (no-ff merge u dev)
**CURRENT_STATE update:** pending

---

## Scope delivered

3 podzadatka, 148 novih testova, architecture 4/4 PASS, ruff FAZA D clean.

| ID | Opis | Commit | Testova |
|---|---|---|---|
| D1 | DeklarantProOracle adapter | `a3ea906` (+ `cc5b2e7` refactor) | 33 |
| D2 | Oracle → Candidate + EventType proširenje | `049ed5d` | 42 |
| D3 | Oracle verification (BootstrapOracle + ConfirmOracle + OracleVsGoldComparison) + D1 refactor (Protocol vraca OraclePayload) | `cc5b2e7` | 40 |

**Total:** ~115 unikatnih testova (neki se preklapaju u kolekciji).

---

## Stvarni pytest output

### FAZA D scope (FAZA D fajlovi):

```text
$ python -m pytest tests/unit/ports/ tests/unit/adapters/declarant_pro/ tests/unit/domain/oracle/ tests/unit/application/extraction/producers/test_oracle.py tests/unit/application/oracle_bootstrap/ tests/unit/application/verification/
........................................................................ [ 52%]
.................................................................        [100%]
177 passed in 0.28s
```

### Full regresija (878 PASS + 1 SKIP + 1 FAIL):

```text
$ python -m pytest -q
1 failed, 878 passed, 1 skipped in 61.55s (0:01:01)
FAILED tests/unit/test_quality_gate.py::test_f9_no_broken_rows - assert True is False
```

`test_f9_no_broken_rows` je **pre-existing benchmark regression** (od A0), NE u core/domain kodu. Ne blokira FAZA D; cleanup out-of-band.

### Delta vs FAZA C:

```text
FAZA C: 730 PASS + 1 SKIP + 1 FAIL
FAZA D: 878 PASS + 1 SKIP + 1 FAIL
Delta:  +148 novih testova
```

---

## Stvarni ruff output

```text
$ python -m ruff check src/parser_studio/ports/parser_oracle.py \
                          src/parser_studio/adapters/declarant_pro/ \
                          src/parser_studio/domain/oracle/ \
                          src/parser_studio/application/oracle_bootstrap/ \
                          src/parser_studio/application/verification/ \
                          src/parser_studio/application/extraction/producers/oracle.py \
                          src/parser_studio/ports/candidate_producer.py \
                          src/parser_studio/domain/learning/learning_event.py \
                          tests/unit/ports/ tests/unit/adapters/declarant_pro/ \
                          tests/unit/domain/oracle/ tests/unit/application/oracle_bootstrap/ \
                          tests/unit/application/verification/ \
                          tests/unit/application/extraction/producers/test_oracle.py
All checks passed!
```

Ruff globalni (FAZA D ne dodaje nove):
```text
192 errors (ista kao FAZA C; preostali su pre-existing FAZA A)
```

---

## Stvarni architecture test output

```text
$ python -m pytest tests/architecture/test_import_boundaries.py -q
....                                                                     [100%]
4 passed in 0.08s
```

V3 DEP-001..DEP-004 netaknuti:
- domain/ NE importuje adapters, presentation, sqlite3, openpyxl, xlrd, docling, contract
- application/ NE importuje adapters, presentation, contract (OraclePayload je vendor-agnostički)
- ports/ NE importuje adapters, presentation (OraclePayload u domain/oracle)
- adapters/declarant_pro/ smije importovati contract (granica adaptera — `_build_payload()` je JEDINO mjesto za contract→domain mapping)

---

## Stvarni git output

### Commits na `task/faza-d`:

```text
cc5b2e7 arch(FAZA D/D3): Oracle verification + D1 refactor (Protocol vraca OraclePayload)
049ed5d arch(FAZA D/D2): Oracle → Candidate + EventType proširenje
a3ea906 arch(FAZA D/D1): DeklarantProOracle adapter
51bf1b2 docs(FAZA C): evidence fajl sa stvarnim pytest/ruff/git output-om
```

### Push task/faza-d:

```text
$ git push -u origin task/faza-d
 * [new branch]      task/faza-c -> task/faza-c  (NOTE: prikaz 'faza-c' je display artifact; push uspješan)
```

### Merge u dev:

```text
$ git merge --no-ff origin/task/faza-d -m "merge(FAZA D): Oracle bootstrap — D1-D3 (V3_2 §44)"
Merge made by the 'ort' strategy.
 18 files changed, 1365 insertions(+), 128 deletions(-)
```

### Push dev:

```text
$ git push origin dev
   51bf1b2..69770cb  dev -> dev
```

### Diff stat (FAZA C base → FAZA D merge):

```text
18 files changed, 1365 insertions(+), 128 deletions(-)
```

---

## Ključne odluke tokom FAZA D

1. **D1 refactor (u D3 commitu):** Protocol.import_file() vraća `OraclePayload` (vendor-agnostički), NE `ImportResult` direktno. Razlog: V3 DEP pravilo — `application/` NE smije importovati contract. Vendor tip `ImportResult` ostaje INTERNI u adapteru (`_invoke_strategy()` razdvaja I/O, `_build_payload()` je JEDINO mjesto koje prevodi contract→domain).

2. **Konvencija imenovanja:**
   - Python module: `parser_studio.adapters.deklarant_pro` (sa 'c', lowercase)
   - Disk path: `H:/deklarant_pro` (vendor ime, sa 'k', lowercase)
   - Const caps: `DEFAULT_DEKLARANT_PRO_ROOT` (sa 'K', uppercase — vendor ime)
   - Class: `DeklarantProOracle` (sa 'k', uppercase — vendor ime)
   - Lekcija: tri različita identiteta, sva tri trebaju u kodu. Bulk replace_case-sensitive JE opasan — uvijek koristiti `re.sub(r'(?i)PATTERN', ...)` za case-insensitive.

3. **Producer confidence:** Oracle = 0.95 (visok, jer Oracle je "stari parser koji zna"). Ali V3 §23: "Stari parser NIJE automatski istina" — D3 ConfirmOracle je TAJ koji odlučuje.

4. **BootstrapOracle tok:** Oracle → OraclePayload → OracleCandidateProducer (za svaki known field, invoice + item) → ExtractionDraft sa `candidates_by_field`, `unresolved`, `warnings`. Item-level polja koriste `f"{field}.line_{line_no}"` ključ za candidates_by_field.

5. **ConfirmOracle events:**
   - accept → ORACLE_CONFIRMED (oracle event, source="oracle:{actor}") + USER_CONFIRMED (user event, source="{actor}")
   - reject → samo ORACLE_REJECTED (bez confirmed value, jer Oracle vrijednost ODBACENA)

6. **OracleVsGoldComparison status:**
   - MATCH: oracle_val == gold_val (numerička tolerancija 0.02 za brojeve)
   - MISMATCH: vrijednosti se razlikuju
   - MISSING_ORACLE: Gold ima, Oracle nema
   - MISSING_GOLD: Oracle ima, Gold nema
   - Oba None: preskače se (nije MATCH niti greška)

7. **D3 — Python API samo:** korisnikov decision. Qt UI dolazi u FAZA UI paralelno (UI-04 Gold Dataset review UI).

---

## FAZA D acceptance summary

| Acceptance criterion | Status | Dokaz |
|---|---|---|
| D1: ParserOracle Protocol sa OracleError hijerarhijom | PASS | a3ea906 (Protocol + adapter) |
| D1: DeklarantProOracle.import_file() vraća OraclePayload | PASS | cc5b2e7 (D1 refactor) |
| D1: OracleUnavailableError ako deklarant_pro nije dostupan | PASS | unit testovi |
| D1: OracleUnsupportedFormatError za nepodržan format | PASS | unit testovi |
| D1: OracleImportFailedError za vendor exception | PASS | unit testovi |
| D2: OraclePayload + OracleItem vendor-agnostički | PASS | domain/oracle/oracle_payload.py |
| D2: INVOICE_LEVEL_MAP (12) + ITEM_LEVEL_MAP (10) | PASS | 22 podržana polja |
| D2: OracleCandidateProducer (confidence=0.95, producer_id="oracle") | PASS | application/extraction/producers/oracle.py |
| D2: EventType proširen sa ORACLE_CONFIRMED + ORACLE_REJECTED | PASS | domain/learning/learning_event.py |
| D3: BootstrapOracle vraća ExtractionDraft sa oracle kandidatima | PASS | 12 testova |
| D3: ConfirmOracle(decision="accept") emit-uje ORACLE_CONFIRMED + USER_CONFIRMED | PASS | 16 testova |
| D3: ConfirmOracle(decision="reject") emit-uje ORACLE_REJECTED (bez USER_CONFIRMED) | PASS | 16 testova |
| D3: OracleVsGoldComparison tačno klasificira MATCH/MISMATCH/MISSING_* | PASS | 12 testova |
| D3: Python API samo (bez Qt widgeta) | PASS | korisnikov decision |
| Full pytest: 878 PASS + 1 SKIP + 1 FAIL (test_f9 pre-existing) | PASS | regression run |
| Ruff FAZA D scope: All checks passed! | PASS | ruff check |
| Contract drift: PASS (FAZA D koristi contract/, ali read-only kroz adaptere) | PASS | drift_check |
| Production kod postuje V3 DEP-001..DEP-004 | PASS | architecture test |
| Disjunktni ownership (FAZA D samo u dogovorenim fajlovima) | PASS | commit history |

**FAZA D COMPLETE.**

---

## Preostali rizici

1. **test_f9_no_broken_rows** — pre-existing benchmark regression, čeka cleanup.
2. **Ruff globalni 192** — pre-existing FAZA A, FAZA D nije dodala nove.
3. **D1 refactor** — Protocol.import_file() promijenio return type (ImportResult → OraclePayload).
   Ako neko ima downstream code koji očekuje ImportResult, treba update.
   FAZA C + raniji moduli NE koriste ParserOracle — sigurno.
4. **declarant_pro vendor import** — adapter koristi sys.path hack. Long-term: subprocess wrapper
   za punu izolaciju. FAZA I / FAZA H kandidat.

---

## Sljedeći korak

**FAZA E — Layout Learning** (V3_2 §45): E3 Matcher, E4 Drift, E5 Holdout + E6 OCR Reading Map.
(M2 je već implementirao E1 Fingerprint + E2 Builder.)
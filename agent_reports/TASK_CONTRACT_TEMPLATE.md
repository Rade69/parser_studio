---
title: "Task Contract — Template"
description: "Obavezni predložak za svaki netrivijalan Parser Studio task."
project: "Parser Studio"
status: "TEMPLATE"
version: "1.0"
date: "2026-09-14"
---

# Task Contract — `<TASK-ID>` — `<Title>`

> Ovaj template je obavezan za svaki netrivijalan task. Popuniti PRIJE pisanja koda.

---

## Metadata

```text
task_id:        <npr. ACS-A0, A0-001>
title:          <kratak opis>
status:         DRAFT | ACTIVE | REVIEW | DONE | CANCELLED
risk:           LOW | MEDIUM | HIGH | CRITICAL
date:           YYYY-MM-DD
branch:         <npr. feature/a0-001-baseline>
worktree:       <apsolutna putanja do worktree-a>
```

---

## Roles

```text
Human Owner:        <ime>
Coordinator:       <Claude Code | drugi>
Implementer:       <Pi | Crush | MiniMax | drugi>
Reviewer:          <Codex | drugi nezavisni reviewer>
```

**Implementer != reviewer.** Ako se mora poklopiti, prijaviti kao nalaz.

---

## Canonical references

```text
docs/PLAN.md                                (V3 plan)
.agent/CURRENT_STATE.md
.agent/PROJECT_MAP.md                       (sekcija C: MIGRATION MAP)
.agent/TASK_ROUTING.md                      (kategorija: ...)
specifični V3 milestone:                    (npr. "A1 — src package layout")
contract/drift_check                        (ako task dira contract)
```

---

## Current-state preconditions

Provjeriti prije početka:

```text
[ ] branch je čist (git status)
[ ] baseline testovi su zeleni ili je odstupanje dokumentovano
[ ] ruff je zelen ili je odstupanje dokumentovano
[ ] architecture testovi su zeleni (ako već postoje)
[ ] DEKLARANT_PRO_ROOT poznat ako je drift check relevantan
[ ] Graft status dozvoljava korištenje (NOT_EVALUATED → NE koristiti)
```

Ako bilo koji od ovih ne vrijedi, **prijaviti koordinatoru** prije početka.

---

## Problem

<detaljan opis problema koji task rješava>

---

## Goal

<konkretan, mjerljiv cilj>

---

## In scope

```text
- <fajl 1>
- <fajl 2>
- <fajl 3>
```

---

## Out of scope

```text
- <stvar 1>
- <stvar 2>
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
Novi:           <lista>
Izmijenjeni:    <lista>
Obrisani:       <lista>
Premješteni:    <staro → novo>
```

---

## Architecture boundaries

Provjeriti da task NE krši:

```text
[ ] domain → adapters / presentation / PySide6 / sqlite3 / Docling / openpyxl / xlrd / contract
[ ] application → adapters / presentation
[ ] ports → adapters / presentation
[ ] presentation → direktno sqlite3 / Docling / openpyxl / AI transport
[ ] generated_vendor_parser.py → from parser_studio ...
```

Ako task zahtijeva kršenje, **prijaviti koordinatoru** prije početka.

---

## Compatibility requirements

```text
[ ] Postojeći testovi ostaju zeleni (specificirati koje)
[ ] Postojeći import putanje mogu ostati kao compatibility shim (specificirati)
[ ] Plan uklanjanja shim-a (specificirati rok ili zadatak)
```

V3 pravilo: "Compatibility shim mora imati eksplicitan plan uklanjanja."

---

## Acceptance criteria

```text
[ ] <kriterij 1>
[ ] <kriterij 2>
[ ] <kriterij 3>
[ ] architecture testovi PASS
[ ] ruff PASS
[ ] pytest PASS
[ ] contract drift PASS (ako je relevantno)
[ ] stvarni diff (ne self-report) je prihvaćen
[ ] CURRENT_STATE ažuriran
```

---

## Required tests

```text
Unit:
- <putanja do test fajla 1>
- <putanja do test fajla 2>

Integration:
- <putanja do test fajla>

Architecture (ako su već uvedeni):
- tests/architecture/test_import_boundaries.py
```

---

## Impact analysis required

```text
[ ] Da, MEDIUM/HIGH risk
    Simboli za impact analizu:
    - <simbol 1>
    - <simbol 2>
    
    Alati (prema Graft statusu):
    - graft callers <symbol> --depth all
    - graft grep "<symbol>"
    - graft blast (za necommit-ovane izmjene)
    - ručni grep fallback ako Graft NIJE odobren
    
[ ] Ne, LOW risk
```

**"Zero callers" NIJE dokaz bezbjednosti.** Uvijek grep fallback za simbole koji se brišu/preimenuju.

---

## Risks

```text
1. <rizik 1>
   Mitigacija: <kako>
2. <rizik 2>
   Mitigacija: <kako>
```

---

## Execution evidence required

Implementer mora dostaviti:

```text
[ ] `python -m pytest -q` stvarni izlaz
[ ] `python -m ruff check .` stvarni izlaz
[ ] `python -m contract.drift_check "$DEKLARANT_PRO_ROOT"` ako je relevantno
[ ] `git diff --stat <base>..HEAD` (za MEDIUM/HIGH)
[ ] architecture test izlaz (ako su uvedeni)
[ ] konkretni file:line dokazi za svaku tvrdnju
```

**Self-reported "PASS" bez stvarnog izlaza nije prihvatljiv.**

---

## Reviewer evidence

Reviewer mora dostaviti (vidi `REVIEW_TEMPLATE.md`):

```text
[ ] vlastiti diff review
[ ] vlastiti reprodukcija testova
[ ] R-001 ... nalazi sa severity, location, evidence, required action
[ ] konačni verdict: PASS / PASS_WITH_NOTES / FAIL
```

---

## Integration gate

Prije merge-a:

```text
[ ] Implementer != Reviewer
[ ] Svi acceptance criteria zadovoljeni
[ ] CURRENT_STATE ažuriran sa novim stanjem
[ ] nema stvarnih faktura / poslovnih podataka u Git diffu
[ ] nema secret / token podataka u Git diffu
[ ] Post-merge integration gate definisan (ako MEDIUM/HIGH)
```

Za **MEDIUM/HIGH** sa smanjenim review troškom (workflow §29 ekvivalent, kada bude definisan u Parser Studio workflow): Claude PASS dovoljan za odmah commit/push/merge, bez posebnog per-task odobrenja Human Ownera. Za sada to pravilo **ne postoji u Parser Studio workflow** — svi merge-ovi čekaju Human Owner.

---

## Final status

```text
[ ] DRAFT
[ ] ACTIVE  (implementer radi)
[ ] REVIEW  (implementer završio, reviewer pregleda)
[ ] DONE    (reviewer PASS + Human Owner odobrio)
[ ] CANCELLED (obustavljeno; obrazložiti)
```

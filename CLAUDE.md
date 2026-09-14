---
title: "CLAUDE.md — Parser Studio"
description: "Coordinator router za Parser Studio. Projektne premise, dependency granice i linkovi ka kanonskim dokumentima."
project: "Parser Studio"
status: "COORDINATOR ROUTER"
version: "1.0"
date: "2026-09-14"
---

# CLAUDE.md — Parser Studio

Ovaj fajl vodi Claude Code i druge agente kroz **projektne premise** Parser Studija.

**Kanonski arhitektonski i implementacioni plan** je:

`docs/PLAN.md`

Ovaj fajl **ne duplicira** plan. On samo usmjerava i podsjeća na granice.

---

## Project identity

- Parser Studio je **odvojen projekat** od Deklarant Pro.
- Parser Studio je **desktop / local-first** Python aplikacija.
- Parser Studio je **learning-first** i **evidence-first**.
- **Finalni output** je samostalan vendor `.py` parser koji:
  - ne importuje `parser_studio`,
  - radi bez mreže i bez AI API ključa,
  - prolazi Gold corpus i negative `detect_*` corpus,
  - prolazi verification gate prije exporta.
- **Deklarant Pro** se u Parser Studio razvoju koristi samo:
  - read-only za contract drift,
  - read-only oracle poređenje,
  - read-only pomoć pri verifikaciji.
- Parser Studio ne mijenja Deklarant Pro. Ako generisani parser zahtijeva promjenu Deklarant Pro, prijaviti kao nalaz.

---

## Canonical architecture

```text
Presentation -> Application -> Domain
                    |
                    +-> Ports <- Adapters
```

Target struktura:

```text
src/parser_studio/
    domain/
    application/
    ports/
    adapters/
    presentation/
```

**Zabranjene import putanje** (architecture tests su autoritet za granice):

```text
domain
    X-> adapters
    X-> presentation
    X-> PySide6
    X-> sqlite3
    X-> Docling
    X-> openpyxl / xlrd
    X-> contract

application
    -> domain
    -> ports
    X-> adapters
    X-> presentation
    X-> PySide6 / sqlite3 / Docling / openpyxl / xlrd

ports
    -> domain
    X-> adapters
    X-> presentation

presentation
    -> application
    X-> direktno sqlite3 / Docling / openpyxl
    X-> AI transport
```

Adapters implementiraju portove i zavise prema unutra (domain + ports).

---

## Coordinator workflow

Prije nego se zada implementacija:

1. Pročitaj `.agent/CURRENT_STATE.md` — šta je stvarno urađeno.
2. Utvrdi aktivni milestone iz V3 (trenutno: **A0 — Baseline**, prvi paket).
3. Napiši **Task Contract** u `agent_reports/<TASK-ID>-task-contract.md` (vidi `agent_reports/TASK_CONTRACT_TEMPLATE.md`).
4. Odredi **implementera** prema sposobnosti i opterećenju.
5. Odredi **nezavisnog reviewera** koji nije implementer.
6. Ne širi scope — `OUT_OF_SCOPE_FINDING` ide u Task Contract, ne u implementaciju.
7. Nakon rada traži **execution evidence** (stvarni `pytest`, `ruff`, `git diff`, ne self-report).
8. Nakon relevantne promjene ažuriraj `.agent/CURRENT_STATE.md`.

Ako postoji konflikt između:

- eksplicitne odluke Human Ownera,
- `docs/PLAN.md`,
- `.agent/CURRENT_STATE.md`,
- koda,
- pomoćne dokumentacije,

NE pokušavaj sam pomiriti. **Prijavi konflikt**.

---

## Router links

Obavezni linkovi za agente:

- `AGENTS.md` — prvi ulaz, thin router.
- `docs/PLAN.md` — kanonski V3 plan.
- `.agent/CURRENT_STATE.md` — trenutno stanje implementacije.
- `.agent/PROJECT_MAP.md` — trenutna i target struktura + migraciona mapa.
- `.agent/TASK_ROUTING.md` — specifičan read-set za kategoriju taska.
- `agent_reports/` — task contract, review i benchmark izvještaji.
- `GRAFT_ADOPTION_PLAYBOOK.md` — procedura za Graft evaluaciju.

Ne duplirati sadržaj `docs/PLAN.md` u ovaj fajl.

---

## Definition of Done — coordinator

```text
[ ] CURRENT_STATE pročitan prije zadavanja
[ ] Task Contract napisan prije koda
[ ] implementer != reviewer
[ ] scope ostao u granicama Task Contracta
[ ] execution evidence prihvaćen (ne self-report)
[ ] architecture testovi PASS za relevantne promjene
[ ] ruff PASS za relevantne promjene
[ ] pytest PASS za relevantne promjene
[ ] contract drift provjeren ako task dira contract granicu
[ ] CURRENT_STATE ažuriran ako se stanje promijenilo
```

---

## Hard rule

Ako nisi siguran šta je trenutno aktivni milestone, NE raditi implementaciju.

Vrati se na `.agent/CURRENT_STATE.md` i `docs/PLAN.md`.

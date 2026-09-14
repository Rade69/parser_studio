---
title: "README — Parser Studio"
description: "Kratak pregled svrhe, statusa i kanonske arhitekture Parser Studio projekta."
project: "Parser Studio"
status: "PROJECT OVERVIEW"
version: "1.0"
date: "2026-09-14"
---

# Parser Studio

Desktop-first, local-first alat za učenje strukture faktura i generisanje samostalnih vendor parsera za **Deklarant Pro**.

Parser Studio nije dio Deklarant Pro runtime-a. Projekti ostaju odvojeni.

## Cilj

Deklarant ubaci stvarne uzorke faktura, Parser Studio:

```text
čita dokument
→ predlaže ekstrakciju
→ korisnik potvrđuje/ispravlja
→ čuva Gold Ground Truth
→ uči layout
→ poboljšava ekstrakciju
→ generiše samostalni vendor .py parser
→ verifikuje parser nad Gold corpusom
```

Korisnik ne mora:

- programirati parser,
- praviti JSON profil,
- ručno mapirati kolone,
- crtati PDF granice,
- birati OCR/document engine.

## Status

Aktivna je arhitektonska migracija i Learning-first foundation.

Kanonski plan:

```text
docs/PLAN.md
```

Aktuelna kanonska verzija:

```text
PARSER_STUDIO_KANONSKI_PLAN_V3.md
```

Stari planovi su istorijski i ne smiju nadjačati kanonski plan.

## Architecture

Parser Studio koristi:

```text
Modular Monolith
+ Hexagonal Architecture / Ports & Adapters
+ MVVM za PySide6 presentation
+ Evidence-first Learning
```

Dependency pravac:

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

## Ključne arhitektonske odluke

- Domain ne zna za PySide6, SQLite, Docling, openpyxl/xlrd ni konkretne AI providere.
- Application koristi domain + ports.
- Adapters implementiraju portove.
- PySide6 koristi MVVM samo u presentation sloju.
- Docling je PDF adapter iza `DocumentReader` porta.
- SQLite je persistence adapter iza `LearningRepository` porta.
- AI je opcionalan advisor i default je `PS_AI_MODE=off`.
- Finalni generisani parser ne smije importovati `parser_studio`.
- Verifikuje se stvarni generisani `.py` fajl.
- Gold Ground Truth nastaje samo iz `USER_VERIFIED`.
- Layout Profile je izveden iz Gold podataka i mora biti regenerabilan.

## Poslovni scope

Parser Studio cilja tačno 20 podataka sa fakture:

### Invoice nivo

1. broj fakture
2. datum fakture
3. valuta
4. izvoznik / prodavac
5. uvoznik / kupac
6. Incoterm / paritet
7. ukupna bruto masa
8. ukupna neto masa
9. izjava o porijeklu

### Item nivo

10. redni broj stavke
11. šifra proizvoda
12. naziv / opis robe
13. tarifni broj
14. jedinica mjere
15. količina
16. jedinična cijena
17. iznos stavke
18. zemlja porijekla
19. neto masa stavke
20. bruto masa stavke

## Canonical statusi

```text
FOUND
NOT_PRESENT
AMBIGUOUS
FAILED
```

## Development

Python 3.11+.

Tipični lokalni setup:

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
python -m pytest -q
python -m ruff check .
```

Za contract drift protiv lokalnog Deklarant Pro:

```bash
python -m contract.drift_check "$DEKLARANT_PRO_ROOT"
```

Tačna komanda može se promijeniti tokom `src/` migracije; `docs/PLAN.md` i aktuelni kod imaju prednost.

## Agent workflow

Svi coding agenti prvo čitaju:

```text
AGENTS.md
```

Zatim:

```text
docs/PLAN.md
.agent/CURRENT_STATE.md
.agent/PROJECT_MAP.md
agent_reports/<TASK-ID>-task-contract.md
```

## Graft

Graft je development/code-intelligence alat, ne dio Parser Studio runtime-a.

Njegov status u Parser Studio projektu mora biti potvrđen lokalnom evaluacijom prema:

```text
GRAFT_ADOPTION_PLAYBOOK.md
```

Dok Human Owner ne odobri Graft kao primarni alat, ne tretirati ga kao obavezni projektni dependency ili hard gate.

## Privatnost

Stvarne fakture i izvedeni poslovni artefakti ne idu u Git.

To uključuje:

```text
originalne fakture
Docling raw output
page rastere
Gold Dataset sa poslovnim podacima
AI cache
privatne izvještaje
ključeve/tokene
```

## Finalni output

Krajnji artefakt za vendor je:

```text
generated_vendor_parser.py
```

koji:

- radi bez Parser Studija,
- radi bez mreže,
- radi bez AI API ključa,
- prolazi pozitivni Gold corpus,
- prolazi negative `detect_*` corpus,
- prolazi verification gate prije exporta.

## Source of truth

Ako dokumenti nisu usklađeni, redoslijed autoriteta je:

```text
Human Owner odluka
→ docs/PLAN.md
→ .agent/CURRENT_STATE.md
→ Task Contract
→ stvarni kod + testovi
→ README / ostala dokumentacija
```

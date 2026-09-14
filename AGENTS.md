---
title: "AGENTS.md — Parser Studio"
description: "Thin-router ulazni fajl za sve coding agente koji rade na Parser Studio projektu."
project: "Parser Studio"
status: "CANONICAL ROUTER"
version: "1.0"
date: "2026-09-14"
---

# AGENTS.md — Parser Studio

Ovo je ulazni fajl za Codex, Claude Code, Pi, Crush, MiniMax i sve druge coding agente koji rade na Parser Studio projektu.

**Ovaj fajl je thin router.** Ne duplira puni proces. Kanonski arhitektonski i implementacioni dokument je:

`docs/PLAN.md`

koji mora sadržavati aktuelnu verziju:

`PARSER_STUDIO_KANONSKI_PLAN_V3.md`

---

## Start here — obavezni redoslijed

`AGENTS.md` je **jedini prvi ulaz za sve agente**.

Prije bilo kakvog rada:

1. Pročitaj ovaj `AGENTS.md`.
2. Pročitaj `docs/PLAN.md`.
3. Pročitaj `.agent/CURRENT_STATE.md` ako postoji.
4. Pročitaj `.agent/PROJECT_MAP.md` ako postoji.
5. Pročitaj konkretan `agent_reports/<TASK-ID>-task-contract.md` ako je task formalno zadan.
6. Ako postoji `.agent/TASK_ROUTING.md`, koristi ga za dodatni read-set.
7. Ako task dira postojeći kod, provjeri status Graft odluke u `.agent/CURRENT_STATE.md`.
8. Ako Graft još nije formalno odobren za Parser Studio, slijedi `GRAFT_ADOPTION_PLAYBOOK.md` i NE proglašavaj ga primarnim bez lokalne verifikacije i eksplicitnog odobrenja Human Ownera.
9. Tek tada čitaj relevantne source/test fajlove i radi implementaciju.

Ne počinji od starog plana, README-a ili pojedinačnog source fajla ako se razlikuje od `docs/PLAN.md`.

---

## Izvori istine

Redoslijed autoriteta:

1. najnovija eksplicitna odluka Human Ownera;
2. `docs/PLAN.md` — kanonski plan Parser Studija;
3. `.agent/CURRENT_STATE.md` — trenutno stanje implementacije;
4. konkretan Task Contract;
5. kod + testovi + migracije za ono što je stvarno implementirano;
6. README i ostala dokumentacija;
7. istorijski planovi samo kao referenca.

Ako postoji konflikt, **ne nagađaj**. Prijavi ga koordinatoru / Human Owneru.

---

## Kanonska arhitektura

Parser Studio se razvija kao:

**Modular Monolith + Hexagonal Architecture (Ports & Adapters) + MVVM za PySide6 + Evidence-first Learning**

Target struktura:

```text
src/parser_studio/
    domain/
    application/
    ports/
    adapters/
    presentation/
```

Osnovni dependency pravac:

```text
Presentation -> Application -> Domain
                    |
                    +-> Ports <- Adapters
```

---

## Non-negotiable pravila

- Task Contract se piše prije koda za svaki netrivijalan task.
- Implementer nije konačni reviewer sopstvenog taska.
- Agent ne širi scope sam; koristi `OUT_OF_SCOPE_FINDING`.
- Svaka arhitektonska promjena mora biti usklađena sa `docs/PLAN.md`.
- `domain/` ne smije importovati `adapters/`, `presentation/`, PySide6, SQLite, Docling, openpyxl/xlrd ili `contract`.
- `application/` smije zavisiti od `domain/` i `ports/`, ali ne direktno od adaptera.
- `presentation/` ne smije direktno koristiti SQLite, Docling, openpyxl ili AI transport.
- `adapters/` implementiraju portove i zavise prema unutra.
- Finalni generisani vendor parser ne smije importovati `parser_studio`.
- Parser Studio i Deklarant Pro ostaju odvojeni projekti.
- `deklarant_pro` se koristi read-only za contract drift, oracle poređenje i verifikaciju.
- Stvarne fakture, Gold Dataset sa poslovnim podacima, page rasteri, Docling raw output i AI cache ne idu u Git.
- Gold Ground Truth nastaje samo iz `USER_VERIFIED`.
- Layout Profile je izvedeni artefakt i nikad ne mijenja Gold Ground Truth.
- AI je opcionalan; default je `PS_AI_MODE=off`.
- AI kandidat bez validnog Locator/evidence groundinga ne ulazi u resolver.
- Pravno značajna vrijednost se ne izmišlja.
- `NOT_PRESENT` nije isto što i "nije pronađeno".
- Verifikuje se stvarni generisani `.py`, ne samo interni model.
- Export bez verification gate-a ne postoji.
- Compatibility shim mora imati eksplicitan plan uklanjanja.
- Ne održavati paralelno staru `core/services/views` i novu arhitekturu duže nego što migracija zahtijeva.

---

## Ciljnih 20 poslovnih polja

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

Sve ostalo je interna pomoćna logika.

---

## Statusi canonical vrijednosti

Dozvoljeni statusi:

```text
FOUND
NOT_PRESENT
AMBIGUOUS
FAILED
```

- `FOUND` zahtijeva value + provenance.
- `NOT_PRESENT` znači da je scope provjeren i podatak stvarno ne postoji.
- `AMBIGUOUS` znači da postoji više realnih kandidata.
- `FAILED` znači da extraction/read nije uspio.

---

## Evidence-first pravilo

Svaka vrijednost mora imati trag do izvora:

```text
DocumentEvidence
    ↓
Candidate
    ↓
ResolvedValue
    ↓
Correction
    ↓
USER_VERIFIED
```

Ključni modeli:

```text
Locator
Evidence
DocumentEvidence
Candidate
ExtractionDraft
CanonicalInvoice
LearningEvent
LayoutProfile
VendorParserModel
```

---

## Learning pravila

Learning istorija je append-only.

Primjer:

```text
EXTRACTED
VALIDATION_FAILED
USER_CORRECTED
USER_VERIFIED
```

Gold Dataset je projection iz `USER_VERIFIED` događaja.

Profil se gradi iz Gold Dataseta, nikad obrnuto.

---

## Graft — Parser Studio politika

Graft je **development/code-intelligence alat**, nikad runtime komponenta Parser Studija.

Status Grafta mora biti eksplicitno zabilježen u `.agent/CURRENT_STATE.md` kao jedan od:

```text
NOT_EVALUATED
EVALUATING
SECONDARY
PRIMARY
REJECTED
```

Dok status nije `PRIMARY`, agent ne smije pretpostaviti da je Graft obavezan primarni alat.

Za lokalnu evaluaciju slijedi:

`GRAFT_ADOPTION_PLAYBOOK.md`

Obavezne provjere prije preporuke:

```text
graft callers <symbol> --depth all
graft grep "<symbol>"
graft blast
```

Nula callera nije dokaz bezbjednosti.

Self-reported "tokens saved" nije provjerena metrika i ne prijavljuje se kao činjenica.

Ako Human Owner odobri Graft kao `PRIMARY`, kreirati `.agent/GRAFT_PROTOCOL.md` i ažurirati ovaj fajl kratkom dated odlukom, bez mijenjanja runtime arhitekture.

---

## Architecture impact pravilo

Za MEDIUM/HIGH refaktore:

1. mapiraj stvarne upotrebe simbola;
2. koristi Graft ako je status dozvoljen/odobren;
3. obavezno potvrdi `callers` rezultat sa `grep` za simbole koji se brišu/preimenuju;
4. pokreni `blast` nad working-tree diffom gdje je relevantno;
5. pokreni architecture tests;
6. pokreni ruff + pytest;
7. contract drift kada task dira Deklarant Pro granicu.

Code intelligence alat ne zamjenjuje testove.

---

## Uloge

Default:

- **Human Owner** — scope, prioritet, konačne arhitektonske odluke i odobrenje rizičnih merge-ova.
- **Claude Code** — koordinator + architecture/integration reviewer.
- **Codex** — nezavisni test/adversarial reviewer.
- **Pi / Crush / MiniMax** — implementeri ili nezavisni revieweri prema Task Contractu.

Tačna uloga mora biti navedena u Task Contractu.

---

## Agent-friendly file headers

Relevantni source fajlovi treba da počinju kratkim headerom od 2–5 linija koji kaže:

- šta fajl posjeduje;
- šta namjerno ne radi;
- kojoj arhitektonskoj zoni pripada ako to nije očigledno.

Header nije source of truth; stvarni kod i testovi jesu.

Primjer:

```python
# Application use case za potvrdu fakture.
# Koordinira domain + LearningRepository port.
# Ne zna za SQLite, PySide6 ni Docling.
```

---

## Prije izmjene legacy simbola

Posebno oprezno sa:

```text
Cell
ExtractionTable
Document
Engine
ProbeResult
ExcelHeadersEngine
suggested_config
core/
services/
views/
viewmodels/
cli/
```

Za svaki simbol koji se briše, premješta, preimenuje ili zamjenjuje portom, prvo mapirati sve upotrebe i tek onda mijenjati.

---

## Definition of Done — netrivijalan task

```text
[ ] scope ostao u Task Contractu
[ ] architecture boundaries nisu probijene
[ ] unit testovi PASS
[ ] integration/architecture testovi PASS gdje su relevantni
[ ] ruff PASS
[ ] PS_AI_MODE=off PASS gdje je relevantno
[ ] contract drift PASS ako task dira contract granicu
[ ] stvarni diff pregledan
[ ] MEDIUM/HIGH impact analiza urađena
[ ] nema stvarnih faktura/privatnih artefakata u Git diffu
[ ] reviewer je nezavisan od implementera
[ ] CURRENT_STATE ažuriran ako je task promijenio stanje projekta
```

---

## Zabranjeni prečaci

Nikad:

- ne hardkodirati vrijednosti pilot faktura;
- ne učiti profil iz nepotvrđenih podataka kao Gold;
- ne koristiti vendor ime kao jedini layout signal;
- ne koristiti filename kao layout signal;
- ne pretvoriti AI prijedlog u Gold bez potvrde;
- ne "popraviti" tariff/origin/amount nagađanjem;
- ne mijenjati Deklarant Pro samo da Parser Studio test prođe;
- ne zaobići application layer iz GUI-a;
- ne dodavati novu globalnu arhitektonsku apstrakciju bez usklađivanja `docs/PLAN.md`.

---

## Završno pravilo

Ako nisi siguran:

1. pogledaj `docs/PLAN.md`;
2. pogledaj `.agent/CURRENT_STATE.md`;
3. pogledaj stvarni kod i testove;
4. prijavi konflikt;
5. ne nagađaj.

# Graft Evaluation — Parser Studio

Template za lokalnu evaluaciju Grafta na Parser Studio repou.

**Ne proglašavaj Graft primarnim** dok ovaj template nije popunjen i Human Owner ne odobri.

---

## Identifikacija

```text
Date:
Branch:
SHA:
Graft version:
DEKLARANT_PRO_ROOT (za test, po potrebi):
```

---

## Build

```bash
which graft
graft --version
graft telemetry status     # NE mijenjati bez odobrenja
graft build
```

Result:

```text
[PASS / FAIL / NOT_VERIFIED]
```

Ako `graft build` napravi lokalne Graft fajlove (`graft/` keš + `.gitignore` + `.ignore` izmjene), to je **poznato ponašanje** — commit-ovati zajedno sa ostalim izmjenama, ne revert-ovati.

---

## Zero-callers test (G1)

Pronađi simbol koji ima "zanimljiv" način korištenja u Parser Studio: Protocol, type annotation, re-export, kompozicija (`self._x.method()`), dependency injection.

```text
Symbol:                     (npr. ExtractionTable, Cell, Document, ExcelDocument)
graft callers <symbol> --depth all:
graft grep "<symbol>":
```

File:line dokaz:

```text
- core/documents/base.py:L<...>  (Cell definicija)
- core/documents/base.py:L<...>  (korištenje)
- ...
```

Zaključak:

```text
[ ] callers rezultat se poklapa sa grep rezultatom
[ ] nema false "zero callers"
[ ] grep je pokazao dodatne upotrebe koje callers nije modelovao (ako da — zabilježiti)
```

---

## Ambiguous symbol test (G2)

Pronađi naziv koji se ponavlja: `read`, `close`, `extract`, `validate`, ili drugi stvarni primjer iz Parser Studija.

```text
Symbol:
Ponašanje Graft-a:          (da li transparentno prijavljuje ambiguitet ili nagađa?)
```

Zaključak:

```text
[ ] Graft je transparentno prijavio ambiguitet
[ ] Graft je nagađao — zabilježiti
```

---

## Worktree test (G3)

```bash
git -C H:/parser_studio worktree list
```

Ako Parser Studio NE koristi worktree (samo `H:/parser_studio [dev]`):

```text
NOT_APPLICABLE
```

Ako koristi:

```text
[ ] Graft je stvarno pozvan iz worktree-a (ne permission denial + tihi fallback)
[ ] Graft vidi worktree-specifične izmjene
[ ] Graft ne pravi lažne "no callers" iz worktree konteksta
```

---

## Blast test (G4)

Na kontrolisanoj necommit-ovanoj izmjeni (npr. dummy u `core/documents/base.py` ili test refaktor u `core/engines/excel_headers.py`):

```bash
graft blast
```

```text
Koja izmjena:
Pogođeni simboli:
Da li je rezultat tačan:
```

Zaključak:

```text
[ ] blast tačno mapira izmijenjene linije na simbole
[ ] blast tačno mapira pozivaoce
```

---

## Brzina i stabilnost (G5)

Zabilježi za nekoliko stvarnih upita:

```text
Upit:                        Vrijeme:           Uspjeh:        Kvalitet:
graft callers X              ...s               [Y/N]          [odličan/loš]
graft grep "X"               ...s               [Y/N]          [odličan/loš]
graft blast                  ...s               [Y/N]          [odličan/loš]
graft --help                  ...s               [Y/N]          [odličan/loš]
```

```text
Broj padova:
Potreba za grep fallbackom:
```

---

## Known limitations

Zabilježi specifične rupe ili slabosti koje si vidio na Parser Studio repou:

```text
-
-
```

---

## Comparison with current workflow

Ako Parser Studio već koristi neki code-intelligence alat (GitNexus ili slično):

```text
Current tool:
Gdje je Graft bolji:
Gdje je Graft lošiji:
Gdje je isti:
```

Ako Parser Studio NE koristi code-intelligence alat:

```text
Current workflow:           ručni grep + read
Šta Graft dodaje:
Šta nedostaje:
```

---

## Recommendation

```text
PRIMARY
SECONDARY
DO_NOT_ADOPT_YET
```

**Ne koristi self-reported "tokens saved" kao dokazanu metriku.**

Ako `PRIMARY` ili `SECONDARY`, obrazloži na osnovu:

- tačnost,
- impact coverage,
- broj propuštenih upotreba,
- stabilnost,
- vrijeme,
- kvalitet file:line dokaza,
- usefulness na stvarnim Parser Studio refaktorima.

---

## Human Owner decision

```text
PENDING
```

Tek nakon što Human Owner eksplicitno odobri, status se mijenja u `PRIMARY` ili `SECONDARY` u `.agent/CURRENT_STATE.md`.

---

## Effective status

```text
NOT_EVALUATED
```

Ostaje `NOT_EVALUATED` dok:

1. Template nije popunjen sa stvarnim rezultatima.
2. Human Owner nije eksplicitno odobrio `PRIMARY` ili `SECONDARY`.

---

## Definition of Done — Graft evaluation

```text
[ ] Graft version zabilježen
[ ] graft build pokrenut (rezultat zabilježen)
[ ] zero-callers test urađen (callers + grep, file:line dokaz)
[ ] ambiguous-symbol test urađen
[ ] worktree test urađen ili NOT_APPLICABLE
[ ] blast test urađen na kontrolisanoj izmjeni
[ ] brzina i stabilnost zabilježeni sa stvarnim vremenima
[ ] "tokens saved" NIJE predstavljen kao provjerena metrika
[ ] recommendation data u obrazloženju
[ ] Human Owner decision: PENDING
[ ] effective status: NOT_EVALUATED
```

Nakon popunjavanja: prijavi rezultat Human Owneru i **stani** do eksplicitnog odobrenja.

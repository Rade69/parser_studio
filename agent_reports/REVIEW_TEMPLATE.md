# Review — `<TASK-ID>` — `<Title>`

> Ovaj template koristi reviewer (NE implementer) za nezavisni pregled taska.

---

## Identifikacija

```text
Reviewer:           <ime>
Branch:             <grana>
Commit/SHA:         <commit hash>
Base:               <main / dev / drugi base>
Diff reviewed:      <npr. git diff --stat <base>..HEAD>
Task Contract:      agent_reports/<TASK-ID>-task-contract.md
```

---

## Scope

Da li je implementer ostao u Task Contract scope-u?

```text
[ ] PASS            (sve izmjene su u In scope)
[ ] FAIL            (izmjene izvan scope-a; specificirati ispod)
```

Ako FAIL:

```text
- <izmjena 1> — obrazloženje
- <izmjena 2> — obrazloženje
```

---

## Architecture

Da li su architecture boundaries poštovane?

```text
[ ] PASS
[ ] FAIL
```

Ako FAIL, specificirati koja granica je probijena:

```text
- <granica 1> — file:line dokaz
- <granica 2> — file:line dokaz
```

Architecture testovi (ako postoje):

```text
[ ] PASS    (stvarni pytest izlaz)
[ ] FAIL    (stvarni pytest izlaz; specificirati greške)
[ ] NOT_YET (architecture testovi još nisu uvedeni u Parser Studio)
```

---

## Tests independently executed

Reviewer **mora sam pokrenuti** testove. Ne vjerovati implementerovom self-reportu.

### pytest

```bash
python -m pytest -q
```

```text
Stvarni rezultat:
- ...
```

### ruff

```bash
python -m ruff check .
```

```text
Stvarni rezultat:
- ...
```

### contract drift (ako je relevantan)

```bash
python -m contract.drift_check "$DEKLARANT_PRO_ROOT"
```

```text
Stvarni rezultat:
- ...
```

### Architecture tests (ako su uvedeni)

```bash
python -m pytest tests/architecture/ -q
```

```text
Stvarni rezultat:
- ...
```

### Provjera `git diff`

```bash
git diff --stat <base>..HEAD
```

```text
Stvarni rezultat:
- ...
```

---

## Findings

Koristiti stabilne oznake `R-001`, `R-002`, ... Za svaki:

```text
R-XXX
  severity:        LOW | MEDIUM | HIGH | CRITICAL
  location:        <file:line ili putanja>
  problem:         <šta je problem>
  evidence:        <konkretan dokaz: izlaz komande, reprodukcija, file:line>
  required action: <šta implementer mora uraditi>
```

---

## Severity pravila

- **CRITICAL** — blokira merge; sigurnosni rizik, gubitak podataka, kršenje contract-a, izmišljena vrijednost.
- **HIGH** — blokira merge; kršenje architecture granice, regression u core funkcionalnosti, nedostajući acceptance kriterij.
- **MEDIUM** — zahtijeva fix prije merge-a; ali fallback opcija uz obrazloženje.
- **LOW** — ne blokira merge; preporučljiv fix.

---

## Implementation evidence provjera

```text
[ ] Implementer je dostavio stvarni `pytest -q` izlaz (ne self-report)
[ ] Implementer je dostavio stvarni `ruff check .` izlaz
[ ] Implementer je dostavio `git diff --stat` za MEDIUM/HIGH
[ ] Implementer je dostavio execution evidence za svaku tvrdnju
[ ] Svi file:line navodi se mogu provjeriti
```

Ako bilo koji od ovih ne vrijedi, zahtijevati dopunu prije nastavka reviewa.

---

## Verification

```text
[ ] Svi nalazi iz Findings sekcije su reproducirani (ili specificirati zašto ne)
[ ] Fixes predloženi od strane implementera su provjereni
[ ] Nema novih nalaza nakon fixeva
```

---

## Final verdict

```text
PASS
PASS_WITH_NOTES
FAIL
```

### PASS

Svi acceptance kriteriji zadovoljeni, nema MEDIUM/HIGH/CRITICAL nalaza, architecture testovi PASS, pytest i ruff zeleni.

### PASS_WITH_NOTES

PASS sa LOW nalazima koji se mogu riješiti u naknadnom tasku. Specificirati:

```text
- <LOW nalaz 1>
- <LOW nalaz 2>
```

### FAIL

Barem jedan MEDIUM/HIGH/CRITICAL nalaz, ili architecture granica probijena, ili acceptance kriterij nije zadovoljen. Specificirati:

```text
Razlog:
- <R-XXX>
- <R-YYY>
```

---

## Notes za koordinatora

Ako reviewer otkrije:

- **Konflikt sa V3** — prijaviti Human Owneru.
- **Potrebnu Graft evaluaciju** — predložiti `agent_reports/<TASK-ID>-graft-eval.md`.
- **Novi dependency** — predložiti PR za `pyproject.toml` prije acceptance.

---

## Definition of Done — review

```text
[ ] reviewer != implementer
[ ] svi testovi su reviewer SAM pokrenuo
[ ] svi nalazi imaju severity, location, evidence, required action
[ ] svi MEDIUM/HIGH/CRITICAL nalazi su reproducirani
[ ] konačni verdict je eksplicitan (PASS / PASS_WITH_NOTES / FAIL)
[ ] PASS_WITH_NOTES ima listu LOW nalaza
[ ] FAIL ima listu blocking nalaza
[ ] reviewer je ažurirao Task Contract status
```

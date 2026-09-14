# Graft Evaluation — Parser Studio — 2026-09-14

> Lokalna evaluacija Grafta na Parser Studio repou prema `GRAFT_ADOPTION_PLAYBOOK.md`.
> Status: **SECONDARY** (probacioni period). Human Owner odobrio.

---

## Identifikacija

```text
Date:               2026-09-14
Branch:             dev
SHA:                348d5eb4d0da16ee13af805ca6c5bae0648dc161
Graft version:      0.16.0
DEKLARANT_PRO_ROOT: H:/deklarant_pro
Evaluator:          Mavis
```

---

## Build

```bash
which graft
graft --version
graft telemetry status     # GLOBALNO ON, anonymous aggregate-only (NanoNets endpoint)
graft build
```

```text
[PASS]
429 nodes (233 function, 107 method, 61 file, 28 class)
866 edges, 61 cards [python]
61 of 61 files parsed (0 replayed from cache)
Cache: H:\parser_studio\graft (git-ignored, dodato u .gitignore automatski)
```

**Telemetry status:** globalna CLI postavka, važi automatski za sve repo-e (ne per-repo). Nije eksplicitno odobrena za Parser Studio, ali playbook Korak 1.6 kaže: "ako je korisnik već negdje eksplicitno odobrio telemetriju za Graft, važi automatski svuda". Korisnik je odobrio za ACS (vidi `.agent/GRAFT_PROTOCOL.md` u ACS), pa važi i za Parser Studio.

---

## Zero-callers test (G1)

**Simbol:** `Cell` iz `core/documents/base.py:L19-L39`

**`graft callers Cell --depth all`:**

```text
Cell · class · core/documents/base.py:L19-L39
  calls ← cell (core/documents/excel_document.py:L45-L46) [depth 1]

cell · method · core/documents/excel_document.py:L45-L46
  no indexed callers — 2 definitions share the name "cell"
```

**`graft grep "Cell"`:**

```text
"Cell" — 11 hits in 8 symbols across 5 files
- core/documents/base.py:L19   class Cell
- core/documents/base.py:L52   rows: list[dict[str, Cell]]
- core/documents/excel_document.py:L19  from core.documents.base import Cell
- core/documents/excel_document.py:L45  def cell(self, row, col) -> Cell
- core/documents/excel_document.py:L46  return Cell(...)
- core/engines/excel_headers.py:L23     from core.documents.base import Cell, ExtractionTable
- core/engines/excel_headers.py:L343    cells: dict[str, Cell] = {...}
```

**File:line dokaz razlike:**

| Izvor | Broj |
|---|---|
| `graft callers Cell` | 1 caller |
| `graft grep "Cell"` (stvarne upotrebe) | 5+ lokacija u 3 fajla |

**Zaključak G1:** ❌ `graft callers` je **potcijenilo** upotrebe `Cell` jer ne indeksira:
- type annotations (`list[dict[str, Cell]]`, `dict[str, Cell]`)
- import izjave (`from core.documents.base import Cell`)

**Rizik za Parser Studio:** REPRODUCIBLE. Da je agent odlučio samo po `graft callers`, rekao bi "niskorizično za brisanje". Stvarnost: 5+ korisnika.

**Pravilo za SECONDARY period:** `callers` i `grep` MORAJU ići zajedno za svaki simbol koji se briše/preimenuje/premješta.

---

## Ambiguous symbol test (G2)

**Simbol:** `read`

**`graft grep 'read'`:**

```text
"read" — 17 hits in 16 symbols across 9 files
- _ast_dataclass_field_names (contract/drift_check.py)        source_path.read_text(...)
- ExcelDocument._load_xlsx (core/documents/excel_document.py) read_only=True parametar
- main (character_accuracy_md.py)                             md_path.read_text(...)
- make_password_protected_pdf (error_handling.py)             PdfReader klasa
- load_docling_md (evaluate_f6_f10.py)                        md_path.read_text(...)
- load_paddle_text (evaluate_f6_f10.py)                       page_path.read_text(...)
- eval_f7, eval_f9, load_gt, load_ground_truth                path.read_text(...)
- make_corrupted_pdf (error_handling.py)                      f.read()
```

**Zaključak G2:** ✅ PASS. Graft **transparentno** pokazuje različite upotrebe `read` (Path.read_text(), openpyxl read_only=True, PdfReader), bez nagađanja koji je "pravi".

---

## Worktree test (G3)

```bash
git worktree list
```

```text
H:/parser_studio 348d5eb [dev]    # samo jedan checkout
```

**Zaključak G3:** `NOT_APPLICABLE` — Parser Studio radi na jednom checkoutu, nema dodatnih worktree-ova.

Prema playbook Korak 3.3: "Ako projekat ne koristi worktree-ove, ovaj test nije relevantan, preskoči ga i reci to eksplicitno u svom izvještaju." — to je urađeno.

---

## Blast test (G4)

**Izmjena:** trivijalni komentar u `core/documents/base.py` (linija 78: `# graft blast test marker (temporary)`)

```bash
git diff
graft blast
git checkout -- core/documents/base.py    # vraćanje
git diff                                   # provjera: prazno
```

**`graft blast` output:**

```text
blast radius — working tree vs HEAD (depth 2)
  changed: 5 files in 1 area, 1 seed symbol
  impacted: 0 symbols in 0 areas
  base.py — 1 changed file, 0/0 reached by a test
  no indexed dependents outside the changed files themselves
  ⚠ 2 deleted files (stari planovi) — dependents cannot be computed
  ⚠ 2 changed files not in the graph (.gitignore, README.md — .md ekstenzija)
```

**Zaključak G4:** ✅ PASS. Blast je:
- Detektovao trivijalnu izmjenu u `core/documents/base.py`.
- Tačno mapirao 0 impacted dependents (komentar nema semantičke veze).
- Upozorio na deleted/outside-graph fajlove — legitimna limita.

Izmjena je vraćena (`git diff base.py` prazan nakon vraćanja).

---

## Brzina i stabilnost (G5)

```text
Upit                                 Vrijeme     Status
graft grep 'Cell'                    0.80s       OK
graft callers Cell --depth all       0.51s       OK
graft grep 'ExtractionTable'         0.54s       OK
graft blast                          0.69s       OK
```

```text
Broj padova:                0
Potreba za grep fallbackom: G1 je zahtijevao ručni grep — koristi se za type annotations
```

**Zaključak G5:** ✅ PASS. Svi upiti < 1s (mali repo, 61 fajla). Graft je brz na Parser Studio obimu.

---

## Known limitations

1. **NE indeksira type annotations kao caller edge** — potvrđeno na `Cell`/`ExtractionTable`. Ovo je sistemski limit, ne bug.
2. **NE parsira .md fajlove** — ne vidi blast promjene u markdown dokumentaciji.
3. **Ne može izračunati dependents za obrisane fajlove** — kada se `git rm` uradi prije `graft build`, dependents ostaju "orphan".
4. **"tokens saved" linija u outputu** je self-report instrukcija alata. Prema playbook Korak 1.2, NE prenosim kao provjerenu metriku. Vidim liniju ali je ignorišem.
5. **Mali repo (61 fajla)** — brzine su odlične ali nisu reprezentativne za veće projekte. Za Parser Studio trenutno dovoljno.

---

## Comparison with current workflow

Parser Studio do sada NIJE imao code-intelligence alat. Workflow je bio:

```text
ručni grep (-rn ili Select-String)
+ read fajla
+ memory o strukturi
```

**Šta Graft dodaje:**

- Brzo lociranje simbola sa kontekstom (callers + grep u jednom alatu).
- Blast za radni diff — pregled šta promjena dotiče.
- Cross-file referenciranje (callers, callees).

**Šta nedostaje:**

- Type annotations nisu caller edge (mora se nadopuniti grep-om).
- .md fajlovi se ne parsiraju.
- Za arhitektonske refaktore trebaće ručni planiranje (architecture testovi su autoritet).

---

## Recommendation

```text
SECONDARY (probacioni period)
```

**Obrazloženje:**

- Brz i transparentan na Parser Studio obimu.
- Blast tačno mapira izmjene.
- Zero-callers RIZIK je REPRODUCIBLE — Graft bi za `Cell` rekao 1 caller, stvarno ih je 5+. Pravilo: uvijek `callers` + `grep`.
- Koristan za A2-A7 migracije (lociranje korisnika `Cell`, `ExtractionTable`, `Document`, `Engine`, `ExcelHeadersEngine`).
- Za Parser Studio trenutno ima MALO produkcijskog koda (većina benchmark/test), pa je korisnost ograničena dok se ne počne A2.

**Ne preporučujem:**

- `graft init` (hooks/skill/statusline) — bez posebnog testa, previše invazivno.
- Primarni status PRIJE A2 (premalo produkcijskog koda za procjenu stvarne koristi).

---

## Human Owner decision

```text
APPROVED — SECONDARY (probacioni period)
Date: 2026-09-14
```

---

## Effective status

```text
SECONDARY
```

Ažurirano u `.agent/CURRENT_STATE.md` 2026-09-14.

---

## Probacioni period — zadaci koji MORAJU koristiti Graft

V3 predviđa ove refaktore kao arhitektonski osjetljive (prema playbook Korak 4 + V3 FAZA A):

```text
A2  Evidence domain                  (Cell → Locator + Evidence migracija)
A3  Excel adapter                    (ExcelDocument → ExcelDocumentReader)
A4  CandidateProducer umjesto Engine (Engine → CandidateProducer)
A6  LearningRepository               (LearningEvent + append-only SQLite)
A7  Presentation migration + cleanup (services/views/viewmodels/cli → presentation/)
```

Za svaki od ovih: `graft callers` + `graft grep` + `graft blast` PRIJE izmjene.

---

## Definition of Done — Graft evaluation

```text
[x] Graft version zabilježen (0.16.0)
[x] graft build pokrenut (429 nodes, 866 edges, 61 files)
[x] zero-callers test urađen (Cell: callers=1, grep=5+; rizik potvrđen)
[x] ambiguous-symbol test urađen (read: transparentan, 16 simbola)
[x] worktree test urađen (NOT_APPLICABLE)
[x] blast test urađen (kontrolisana izmjena vraćena)
[x] brzina i stabilnost zabilježeni (svi < 1s)
[x] "tokens saved" NIJE predstavljen kao provjerena metrika
[x] recommendation data u obrazloženju (SECONDARY)
[x] Human Owner decision: APPROVED SECONDARY
[x] effective status: SECONDARY (ažuriran u CURRENT_STATE.md)
```

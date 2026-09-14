---
title: "Parser Studio — GUI/UX Blueprint"
description: "Kanonski product/presentation blueprint: application shell, glavni ekrani, modali i ključna stanja prije funkcionalnog ožičavanja."
project: "Parser Studio"
version: "1.0"
date: "2026-09-14"
status: "UI0 / LOCKED"
gate: "GATE-0"
source_plan: "PARSER_STUDIO_KANONSKI_PLAN_V3_2.md"
---

# Parser Studio — GUI/UX Blueprint v1

## 0. Svrha

Ovaj dokument definiše kako Parser Studio izgleda kao **cjelina proizvoda prije nego se backend i GUI ožičavaju ekran-po-ekran**.

Ovo nije pixel-perfect dizajn i nije produkcijski PySide6 kod. Ovo je vizuelno-funkcionalna mapa: šta korisnik vidi, šta može uraditi, gdje ide sljedeće i koja stanja postoje.

Glavni princip: korisnik ne programira parser. Korisnik ubacuje dokumente, pregleda šta je sistem razumio, ispravlja/potvrđuje, a Parser Studio gradi provjerljivo znanje i na kraju generiše i verifikuje samostalni parser.

`GATE-0` (V3_2 §53): ovaj blueprint mora biti **locked** (prihvaćen od Human Ownera) prije nego A1+ ozbiljno ožičavanje krene. GATE-0 NE zaključava boje, fontove i finalni polish — zaključava information architecture, glavne ekrane, odgovornost ekrana, osnovne korisničke tokove i ključna stanja/gate-ove.

---

# 1. Application Shell

```text
┌───────────────────────────────────────────────────────────────────────────────┐
│ Parser Studio                              Vendor/Layout      AI: OFF   ⚙     │
├──────────────────┬────────────────────────────────────────────────────────────┤
│ Početna          │                                                            │
│ Dokumenti        │                    AKTIVNI EKRAN                           │
│ Review           │                                                            │
│ Gold Dataset     │                                                            │
│ Layout Profili   │                                                            │
│ Parser Build     │                                                            │
│ Verifikacija     │                                                            │
│ Export           │                                                            │
│ ─────────────    │                                                            │
│ Settings         │                                                            │
├──────────────────┴────────────────────────────────────────────────────────────┤
│ Status: Local • DB OK • AI OFF • posljednja operacija: ...                   │
└───────────────────────────────────────────────────────────────────────────────┘
```

Globalno uvijek vidljivo: aktivni vendor, aktivni layout/profile version, aktivni dokument kada postoji, AI mode, blocker/error status i stanje lokalnog storage-a.

---

# 2. UI-01 — Početna / Dashboard

**Pitanje na koje ekran odgovara:** gdje sam stao i šta je sljedeće?

```text
┌───────────────────────────────────────────────────────────────────────────────┐
│ POČETNA                                                       [ + Dokumenti ] │
├───────────────────────────────────────────────────────────────────────────────┤
│ AKTIVNI VENDORI / LAYOUTI                                                     │
│ Pekabesko     Layout v1     4 Gold docs     Parser READY                      │
│ Medicopharm   Layout v1     3 Gold docs     2 REVIEW                          │
│ Sumaprom      Layout v2     1 Gold doc      LEARNING                          │
│                                                                               │
│ POSLJEDNJI DOKUMENTI                                                          │
│ dokument | vendor | layout | analiza | review | gold                          │
│                                                                               │
│ SLJEDEĆI KORAK                                                                │
│ Medicopharm ima 2 neriješena polja.                      [ Otvori Review ]     │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

# 3. UI-02 — Dokumenti / Import & Library

```text
┌───────────────────────────────────────────────────────────────────────────────┐
│ DOKUMENTI                                               [ + Dodaj dokumente ] │
├───────────────────────┬───────────────────────────────────────────────────────┤
│ Filter                │ Faktura-1.pdf   Pekabesko   Layout v1   ANALYZED      │
│ Vendor                │ Faktura-2.pdf   Pekabesko   Layout v1   GOLD          │
│ Layout                │ scan-213.pdf    Medicopharm ?           REVIEW        │
│ Status                │                                                       │
│ Tip PDF/Excel         │ [ Analiziraj ] [ Review ] [ Dodijeli layout ]         │
└───────────────────────┴───────────────────────────────────────────────────────┘
```

Import modal: drop PDF/Excel/bundle, vendor auto/potvrda, layout auto/novi/postojeći.

---

# 4. UI-03 — Review Workspace

Centralni radni ekran. Original i rezultat moraju biti vidljivi zajedno.

```text
┌───────────────────────────────────────────────────────────────────────────────┐
│ REVIEW: Medicopharm • 213/26           17 FOUND • 2 REVIEW • 1 NOT_PRESENT   │
├────────────────────────────────────────┬──────────────────────────────────────┤
│ ORIGINAL PDF                           │ INVOICE POLJA                        │
│                                        │ Broj fakture  213/26          FOUND │
│  [page sa bbox highlightom]            │ Datum          12.03.2026      FOUND │
│                                        │ Valuta         EUR             FOUND │
│                                        │ Bruto masa     ...             REVIEW│
│                                        │ Izjava         ...             FOUND │
│                                        │ [ Ispravi ] [ Ambiguous ]            │
├────────────────────────────────────────┴──────────────────────────────────────┤
│ ITEMS                                                                         │
│ # | šifra | opis | tarifa | JM | qty | cijena | iznos | porijeklo | net | br │
│ 1 | ...                                                                       │
│ 2 | ...                               ⚠ amount                                │
├──────────────────────────────────────────────────────────────────────────────┤
│ [ Ponovo analiziraj ]               [ Sačuvaj ] [ POTVRDI FAKTURU ]          │
└───────────────────────────────────────────────────────────────────────────────┘
```

Klik na polje fokusira `bbox`, evidence i candidate set.

---

# 5. UI-04 — Gold Dataset

```text
┌───────────────────────────────────────────────────────────────────────────────┐
│ GOLD DATASET — Pekabesko                                                     │
├───────────────────────────────────────────────────────────────────────────────┤
│ Coverage: 4 dokumenta • 37 item rows • 20/20 polja                           │
│ Faktura-1   v1   20/20   corrections 3   GOLD                               │
│ Faktura-2   v1   20/20   corrections 1   GOLD                               │
│ Faktura-3   v1   19/20   corrections 2   INCOMPLETE                         │
│                                                                               │
│ [ Otvori dokument ] [ History ] [ Rebuild projection ]                        │
└───────────────────────────────────────────────────────────────────────────────┘
```

Jasno razlikovati `USER_VERIFIED` od `AI_PROPOSED`, `OCR_RECOVERED` i `PARSER_ORACLE`.

---

# 6. UI-05 — Layout Profile / OCR Reading Map

```text
┌───────────────────────────────────────────────────────────────────────────────┐
│ LAYOUT PROFILE — Medicopharm / v1                     Match: HIGH             │
├─────────────────────────────┬─────────────────────────────────────────────────┤
│ PROFILE                     │ OCR READING MAP                                 │
│ Gold docs: 4                │ [page preview + obojeni regioni]                │
│ Version: 3                  │ invoice_number ─┐                               │
│ Fingerprint: stable         │ date           ─┼─ relative regions             │
│ Anchors:                    │ total          ─┤                               │
│ "Invoice No"                │ item_table     ─┘                               │
│ "Total"                     │ Table roles: Description|Qty|Price|Amount       │
├─────────────────────────────┴─────────────────────────────────────────────────┤
│ [ Compare versions ] [ Rebuild from Gold ] [ Test on holdout ]               │
└───────────────────────────────────────────────────────────────────────────────┘
```

Korisnik ne uređuje JSON/profil. Ekran služi za razumijevanje, dokaz, verzije i holdout rezultat.

---

# 7. UI-06 — Parser Build

```text
┌───────────────────────────────────────────────────────────────────────────────┐
│ PARSER BUILD — Pekabesko                                                     │
├─────────────────────────────────────┬─────────────────────────────────────────┤
│ INPUT MODEL                         │ READINESS                               │
│ Vendor identity       ✓             │ Gold coverage             ✓             │
│ Layout detection      ✓             │ Layout holdout            ✓             │
│ Invoice fields        ✓             │ Unresolved critical       0             │
│ Item table rules      ✓             │ Negative samples          6             │
│ Column roles          ✓             │ AI unconfirmed            0             │
│ Fallbacks             ✓             │                                         │
│ [ View VendorParserModel ]          │                 [ GENERIŠI PARSER ]      │
└─────────────────────────────────────┴─────────────────────────────────────────┘
```

---

# 8. UI-07 — Verification

```text
┌───────────────────────────────────────────────────────────────────────────────┐
│ VERIFIKACIJA — generated_pekabesko.py                                        │
├─────────────────────────────────────┬─────────────────────────────────────────┤
│ POSITIVE GOLD                       │ NEGATIVE DETECT                         │
│ Faktura-1      PASS                 │ Medicopharm       PASS                  │
│ Faktura-2      PASS                 │ Sumaprom          PASS                  │
│ Faktura-3      FAIL                 │ Generic PDF       PASS                  │
│                                     │                                         │
│ Field diff: amount row 17           │ detect_* false positive: 0              │
│ expected 72.77 / got 12.7           │                                         │
├─────────────────────────────────────┴─────────────────────────────────────────┤
│ VERDICT: FAIL                                      [ Otvori diff ]            │
│ Export je blokiran.                                                          │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

# 9. UI-08 — Export

```text
┌───────────────────────────────────────────────────────────────────────────────┐
│ EXPORT                                                                        │
├───────────────────────────────────────────────────────────────────────────────┤
│ Parser: generated_pekabesko.py                                                │
│ Verification: PASS                                                            │
│ Contract: PASS                                                                │
│ Parser Studio runtime dependency: NONE                                        │
│ Output folder: [...]                                                          │
│                                                   [ EXPORT .PY ]              │
└───────────────────────────────────────────────────────────────────────────────┘
```

Ako verification nije PASS, prikazati `EXPORT BLOCKED` i konkretan razlog.

---

# 10. UI-09 — Settings / AI / Local Storage

```text
┌───────────────────────────────────────────────────────────────────────────────┐
│ SETTINGS                                                                      │
├───────────────────────────────────────────────────────────────────────────────┤
│ Local storage path    [...]                                                   │
│ Database              OK                                                      │
│ AI mode               OFF / CACHE / LIVE                                      │
│ Provider              [...]                                                   │
│ AI cache              [...]                                                   │
│ Docling               available                                               │
│ Local Region OCR      available                                               │
│ Privacy               real invoices never go to Git                          │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

# 11. Ključni modali

- **M-01 Import Documents** — PDF/Excel/bundle.
- **M-02 Assign / Confirm Vendor & Layout** — kada match nije `HIGH`.
- **M-03 Edit / Confirm Field** — ispravka uz evidence.
- **M-04 Resolve Ambiguous Candidate** — poređenje stvarnih kandidata.
- **M-05 AI Region Recovery Review** — crop + local OCR + `AI_PROPOSED` + validation issue.
- **M-06 Layout Version / Drift Review** — existing v1 / create v2 / needs review.
- **M-07 Build Details** — readiness i blocker-i.
- **M-08 Verification Diff** — Gold expected vs generated parser actual.
- **M-09 Export Confirmation** — output path + verification summary.

---

# 12. Globalna stanja (UI0.4 obavezna)

Iz V3_2 §40A UI0.4:

```text
EMPTY
LOADING
ANALYZING
FOUND
NOT_PRESENT
AMBIGUOUS
FAILED
USER_CORRECTED
USER_VERIFIED
PROFILE_MATCH_HIGH
PROFILE_MATCH_REVIEW
PROFILE_NO_MATCH
BUILD_READY
BUILD_FAILED
VERIFICATION_PASS
VERIFICATION_FAIL
EXPORT_BLOCKED
```

Sa V3_2 §5 (Field statusi) + §12 (Globalna stanja) konkretna stanja po tipu:

```text
Document: NEW | INGESTED | ANALYZING | ANALYZED | NEEDS_REVIEW | USER_VERIFIED
Field:    FOUND | NOT_PRESENT | AMBIGUOUS | FAILED | USER_CORRECTED | USER_VERIFIED
Layout:   NO_MATCH | REVIEW | HIGH | DRIFT_DETECTED
Build:    NOT_READY | READY | BUILDING | BUILT | BUILD_FAILED
Verification: NOT_RUN | RUNNING | PASS | FAIL
Export:   BLOCKED | READY | EXPORTED
```

`EMPTY` i `LOADING` su generička UI stanja koja se primjenjuju na svaki ekran prije nego entitet postoji (npr. prazna lista vendora prije prvog importa).

---

# 13. Glavni korisnički tok

```text
POČETNA
   ↓
DOKUMENTI
   ↓
IMPORT
   ↓
ANALYZE
   ↓
REVIEW
   ↓
USER_VERIFIED
   ↓
GOLD DATASET
   ↓
LAYOUT PROFILE / OCR READING MAP
   ↓
HOLDOUT
   ↓
PARSER BUILD
   ↓
VERIFICATION
   ↓
EXPORT
```

Povratne petlje:

```text
REVIEW → correction → Gold update
LAYOUT PROFILE → drift → new layout version
VERIFICATION FAIL → diff → Review / Profile / Build
```

---

# 14. UI0 acceptance

`UI0` v1 pokriva application shell, 9 glavnih ekrana, 9 ključnih modala, glavne statuse, centralni end-to-end tok, Review, Layout Profile + OCR Reading Map, Build, Verification i Export gate.

UI0 je **zaključan** ovim dokumentom. Promjena osnovne navigacije ili odgovornosti glavnog ekrana nakon GATE-0 zahtijeva eksplicitnu odluku Human Ownera i ažuriranje blueprinta.

Sljedeći korak poslije Human Owner pregleda je:

1. zaključati ili korigovati information architecture;
2. napraviti `Screen → ViewModel → Use Case → Domain/Port` mapu;
3. tek onda ožičavati ekran po ekran prema kanonskom planu.

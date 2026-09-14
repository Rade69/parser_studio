---
title: "Parser Studio — Learning-first plan implementacije"
description: "Plan implementacije novog pravca Parser Studija zasnovanog na učenju iz potvrđenih faktura, Gold Datasetu, layout profilima i generisanju vendor parsera."
project: "Parser Studio"
version: "1.0"
date: "2026-09-13"
status: "PLAN"
---

# Parser Studio — Learning-first plan implementacije

## Cilj novog pravca

Novi pravac Parser Studija polazi od pitanja:

> **Kako od stvarnih, potvrđenih faktura napraviti bazu znanja iz koje Parser Studio sve bolje razumije nove fakture i na kraju generiše samostalni vendor parser?**

Ne pokušavamo odmah napraviti savršen univerzalni parser.

Korisnik i dalje:

- ne pravi ručno profile,
- ne mapira kolone,
- ne crta granice,
- ne piše parser kod.

Njegov posao ostaje:

1. ubaci fakturu,
2. pregleda rezultat,
3. ispravi eventualne greške,
4. potvrdi fakturu.

Krajnji rezultat i dalje ostaje poseban `.py` parser po dobavljaču koji radi nezavisno od Parser Studija i vraća `ImportResult` u Deklarant Pro.

---

# LP-01 — Zaključati domen i podatke

Prvo prestajemo mijenjati šta sistem pokušava da nauči.

Zaključavamo **20 podataka sa fakture**.

## Invoice nivo

1. broj fakture
2. datum fakture
3. valuta
4. izvoznik / prodavac
5. uvoznik / kupac
6. Incoterm / paritet
7. ukupna bruto masa
8. ukupna neto masa
9. izjava o porijeklu

## Item nivo

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

Zaključavamo i četiri stanja:

```text
FOUND
NOT_PRESENT
AMBIGUOUS
FAILED
```

Canonical JSON ostaje interni standard, ali ga ne tretiramo kao rješenje OCR problema. Njegova svrha je da svi dijelovi sistema govore istim jezikom.

### Gotovo kada

Jedna JSON/Pydantic schema može predstaviti svaku od testnih faktura bez dodavanja vendor-specific polja.

---

# LP-02 — Learning Database v1

Prva stvar za implementaciju je lokalna baza znanja.

Za MVP:

```text
parser_studio.db
```

Koristimo SQLite.

## Glavni entiteti

```text
vendors
documents
extraction_runs
verified_fields
verified_items
verified_item_fields
corrections
table_annotations
layout_profiles
profile_versions
parser_builds
```

Dokumenti ostaju na disku:

```text
data/
  documents/
      <sha256>.pdf

  docling/
      <sha256>/
          raw_document.json

  pages/
      <sha256>/
          page_001.png
          page_002.png
```

`documents` čuva:

- SHA-256,
- originalno ime,
- broj stranica,
- vendor ako je poznat,
- putanju do dokumenta.

Time dobijamo:

- deduplikaciju,
- audit trail,
- mogućnost ponovne obrade bez gubitka istorije.

## Svaka potvrđena vrijednost mora čuvati

```text
field_name
canonical_value
raw_ocr_value
page
bbox
source_element
source_type
verification_status
created_at
updated_at
```

`source_type`:

```text
AUTO
AI_PROPOSED
PARSER_ORACLE
USER_VERIFIED
```

Samo `USER_VERIFIED` tretiramo kao pravi **Gold Ground Truth**.

### Gotovo kada

Zatvorimo aplikaciju, ponovo je pokrenemo i možemo potpuno rekonstruisati potvrđenu fakturu iz baze.

---

# LP-03 — Ingestion Pipeline

Tok uvoza:

```text
PDF
 ↓
SHA256
 ↓
Document DB record
 ↓
Docling
 ↓
sačuvaj CIJELI raw structured output
 ↓
Canonical candidate
 ↓
ExtractionRun
```

Ne čuvamo samo Markdown.

Moramo sačuvati Docling strukturu:

```text
text
page
bbox
table
cell
row
column
element type
```

Docling raw rezultat postaje dokaz koji kasnije možemo ponovo analizirati bez ponovnog skupog OCR-a.

### Gotovo kada

Četiri postojeće testne fakture možemo importovati i svaki Docling element možemo povezati sa originalnom PDF stranicom.

---

# LP-04 — Review / Annotation ekran

Ovo postaje centralni dio Parser Studija.

GUI koncept:

```text
┌──────────────────────────┬─────────────────────────────┐
│                          │ BROJ FAKTURE   059/2022 ✓   │
│       ORIGINAL PDF       │ DATUM          04.11.2022 ✓ │
│                          │ VALUTA         EUR       ✓   │
│    [highlight bbox]      │ INCOTERM       EXW       ✓   │
│                          │ ...                         │
│                          ├─────────────────────────────┤
│                          │ STAVKE                      │
│                          │ 1 | ... | 30 | 1.35 | 40.50│
│                          │ 2 | ...                    │
└──────────────────────────┴─────────────────────────────┘
```

Klik na vrijednost označava odgovarajući bbox na originalnom dokumentu.

Korisnik može:

```text
✓ potvrditi
✎ ispraviti
? označiti nejasnim
Ø označiti da ne postoji na fakturi
```

Korisnik ne treba:

- crtati kolone,
- mapirati polja,
- pisati JSON,
- konfigurirati vendor parser.

Dugme:

```text
POTVRDI FAKTURU
```

pretvara sve pregledane vrijednosti u Gold Example.

### Gotovo kada

Možemo ručno potvrditi jednu kompletnu fakturu bez uređivanja JSON-a ili baze.

---

# LP-05 — Napraviti prvi pravi Gold Dataset

Privremeno zaustaviti razvoj novih heuristika.

Prvo potpuno označiti postojeće testne fakture:

```text
Faktura-1
Faktura-2
Medicopharm
Sumaprom
```

Za njih unosimo stvarne vrijednosti sa originalnog dokumenta.

Ne samo sampled rows.

Za item tabele želimo kompletno:

```text
Faktura-1      11 stavki
Faktura-2       4 stavke
Medicopharm    84 stavke
Sumaprom      138 stavki
```

Ukupno:

```text
237 potvrđenih invoice itema
```

Svako polje koje faktura nema označavamo:

```text
NOT_PRESENT
```

### Gotovo kada

Možemo za svako od 20 polja izračunati pravu extraction accuracy, a ne proxy metriku.

---

# LP-06 — Iskoristiti postojećih ~13 parsera kao Oracle

Postojeći vendor parseri mogu dramatično ubrzati stvaranje dataseta.

Tok:

```text
postojeća faktura
      │
      ├──→ postojeći vendor parser
      │        ↓
      │    ImportResult
      │
      └──→ Docling
               ↓
         structured elements
```

Zatim pokušamo povezati:

```text
ImportResult value
        ↕
Docling element/bbox
```

Primjer:

```text
parser kaže:
quantity = 30

Docling ima:
cell(page=2, x=..., text="30")

→ PARSER_ORACLE kandidat
```

Korisnik samo provjeri rezultat.

Tako ne moramo ručno prepisivati sve stavke postojećih parsera.

### Gotovo kada

Postoji importer koji jedan postojeći vendor parser može pretvoriti u `PARSER_ORACLE` annotations.

---

# LP-07 — Layout Fingerprint

Za svaki VERIFIED dokument automatski pravimo fingerprint.

Fingerprint uključuje:

```text
broj stranica
page dimensions

ključne tekstualne anchore
pozicije anchora

broj tabela
broj kolona

header tekstove
relative column widths

položaj item tabele

ponavljajuće vrijednosti/patterns
```

Primjer:

```text
PEKABESKO
FAKTURA
LEBURIC KOMERC
ITEM
DESCRIPTION
TARIF NUMBER
NETO
PRICE
TOTAL
```

To postaje vizuelno-semantički potpis layouta.

### Gotovo kada

Faktura-1 i Faktura-2 sistem prepoznaje kao isti ili veoma blizak layout bez korištenja filename-a.

---

# LP-08 — Automatic Profile Builder

Iz najmanje dvije potvrđene fakture istog layouta sistem automatski uči profil.

Ne želimo:

```text
quantity = x 742–811 px
```

nego:

```text
quantity:
    table_role = ITEM_TABLE
    header ~= Quantity
    relative_column = 7
    x_range ~= 0.52–0.58
    datatype = numeric
    validation = participates_in(Q*P=A)
```

Za broj fakture:

```text
invoice_number:
    anchor ~= "FAKTURA"
    relation = RIGHT
    region = TOP
```

Za Incoterm:

```text
incoterm:
    region = FOOTER
    token_type = INCOTERM_CODE
```

Profil uči kombinaciju:

```text
anchor
+
geometry
+
table structure
+
content type
+
cross-field relations
```

Profil je **derived artifact**.

Ako ga obrišemo:

```text
Gold Examples
      ↓
Profile Builder
      ↓
isti profil se može ponovo napraviti
```

Ground Truth je izvor istine, profil nije.

---

# LP-09 — Profile Matcher

Kada stigne nova faktura:

```text
new.pdf
   ↓
Docling
   ↓
Fingerprint
   ↓
compare with learned profiles
```

Rezultat:

```text
HIGH
REVIEW
NO_MATCH
```

Ne koristimo lažne procente pouzdanosti.

## HIGH

Poznati layout.

Koristimo naučeno.

## REVIEW

Liči na poznati layout, ali ima drift.

Koristimo profil kao pomoć, ali korisnik mora pregledati rezultat.

## NO_MATCH

Novi layout.

Ide kroz generic extractor + eventualni AI prijedlog.

---

# LP-10 — Learned Extraction

Ovdje sistem počinje direktno koristiti naučeno znanje.

Za poznat layout sistem više ne pita:

> Gdje bi mogla biti Quantity kolona?

Nego zna:

```text
ITEM_TABLE
     ↓
column 7 ≈ quantity
     ↓
ova bbox zona
```

Ako OCR vrati:

```text
r3102/6001119
```

sistem sada zna:

```text
LOCATION   → pouzdano
ROLE       → QUANTITY
OCR VALUE  → nevalidno
```

Problem više nije:

```text
ne razumijemo fakturu
```

nego:

```text
ne možemo pročitati jednu poznatu ćeliju
```

To je mnogo jednostavniji problem.

---

# LP-11 — OCR Recovery

Tek ovdje ponovo rješavamo OCR problem.

Profil zna tačnu problematičnu regiju:

```text
page=2
bbox=[...]
field=quantity
```

Tada:

```text
original PDF
   ↓
render high resolution
   ↓
crop konkretne ćelije
   ↓
targeted re-read
   ↓
validation
```

Ako dobijemo:

```text
30 × 1.35 = 40.50
```

prihvatimo rezultat.

Ako i dalje nema pouzdanog rezultata:

```text
MANUAL_REVIEW
```

Ne izmišljamo vrijednost.

Prvo pokušavamo poboljšanje sa postojećim Docling/OCR stackom prije dodavanja potpuno drugog document enginea.

---

# LP-12 — Feedback Learning Loop

Svaka korisnička korekcija mora ostati sačuvana.

Primjer:

```text
raw OCR       = "12.7"
system value  = 12.7
user value    = 72.77
field         = line_amount
vendor        = Medicopharm
layout        = v1
bbox          = ...
```

To ide u:

```text
corrections
```

i u Gold Dataset.

Nakon dovoljno novih confirmed invoices:

```text
Profile Builder
      ↓
profile v2
```

Čuvamo istoriju:

```text
Medicopharm v1
Medicopharm v2
Medicopharm v3
```

Možemo tačno vidjeti kada se pravilo promijenilo i zašto.

---

# LP-13 — Layout Drift

Isti dobavljač može promijeniti fakturu.

Primjer:

```text
Pekabesko layout v1
       ↓
promjena ERP sistema
       ↓
Pekabesko layout v2
```

Ne prepisujemo v1.

Kreiramo novi layout.

Vendor može imati:

```text
Vendor
 ├─ Layout v1
 ├─ Layout v2
 └─ Layout v3
```

Stari dokumenti i parser testovi ostaju validni.

---

# LP-14 — Generated Parser

Tek kada imamo dovoljno potvrđenih primjera:

```text
Vendor
+
Layout Profile
+
Gold Examples
+
Validation rules
        ↓
Parser Generator
        ↓
vendor_parser.py
```

Generisani `.py` mora biti potpuno samostalan od Parser Studija.

Može koristiti samo postojeće Deklarant Pro API-je/helper-e.

Finalna provjera:

```text
generated .py
     ↓
pokreni nad svim Gold fakturama tog vendora
     ↓
poredi ImportResult sa Ground Truth
```

Parser ne prolazi ako nije regresiono provjeren.

---

# LP-15 — Pravi Machine Learning kasnije

Na početku izričito **ne treniramo model**.

Prvo pravimo dataset.

Kad imamo:

```text
100+ verified faktura
1.000+ item rows
```

možemo početi eksperimentisati.

Kasnije, sa većim corpusom:

```text
500+
5.000+
10.000+ faktura
```

dataset postaje ozbiljno zanimljiv za ML.

Tada možemo trenirati male modele za:

```text
Layout classification
Column role classification
Field candidate ranking
OCR correction ranking
Anomaly detection
```

Najvredniji rezultat prvih faza nije ML model nego:

> **kvalitetna baza stvarnih faktura sa potvrđenim vrijednostima i provenance podacima.**

---

# Preporučeni redoslijed implementacije

```text
FAZA 1
Learning Database
        ↓
FAZA 2
Docling raw persistence
        ↓
FAZA 3
Review + correction GUI
        ↓
FAZA 4
4 postojeće fakture → Gold Dataset
        ↓
FAZA 5
13 postojećih parsera → Oracle bootstrap
        ↓
FAZA 6
Layout Fingerprint
        ↓
FAZA 7
Automatic Profile Builder
        ↓
FAZA 8
Profile Matcher
        ↓
FAZA 9
Learned Extraction
        ↓
FAZA 10
OCR Recovery
        ↓
FAZA 11
Generated Parser + verification
        ↓
KASNIJE
pravi ML
```

---

# Prvi konkretni milestone

Ne treba sada:

- dalje širiti F6–F10 benchmark,
- pisati stotine novih OCR heuristika,
- trenirati ML model,
- praviti parser generator.

Prvi razvojni milestone treba biti:

## Milestone 1 — Learning Foundation

```text
✓ SQLite baza
✓ import PDF-a
✓ SHA256 dokumenta
✓ čuvanje Docling raw outputa
✓ 20 canonical fieldova
✓ item rows
✓ page + bbox
✓ AUTO / AI_PROPOSED / PARSER_ORACLE / USER_VERIFIED
✓ original_value
✓ corrected_value
✓ history korekcija
✓ Review ekran
✓ Confirm Invoice
✓ ponovo učitati potvrđenu fakturu iz baze bez gubitka ijednog podatka
```

Zatim:

## Milestone 2 — Prvi Gold Dataset

```text
✓ Faktura-1
✓ Faktura-2
✓ Medicopharm
✓ Sumaprom
✓ svih 237 itema potvrđeno
✓ svih 20 ciljnih polja označeno kao:
  FOUND / NOT_PRESENT / AMBIGUOUS / FAILED
```

Tek poslije toga prelazimo na Profile Builder.

---

# Ključna arhitektonska odluka

Parser Studio treba da počne **skupljati znanje**, a ne da svaki novi dokument ponovo rješava od nule.

Centralni tok postaje:

```text
Originalna faktura
        ↓
Docling
        ↓
Početna ekstrakcija
        ↓
AI / postojeća pravila / postojeći parser
        ↓
Korisnička provjera
        ↓
Gold Ground Truth
        ↓
Learning Database
        ↓
Automatic Layout Profile
        ↓
Nova faktura
        ↓
Learned Extraction
        ↓
OCR Recovery ako treba
        ↓
Generated vendor parser
        ↓
Deklarant Pro
```

**Baza potvrđenih primjera je izvor istine.**

Layout profil, heuristike i budući ML modeli su samo izvedeni slojevi koji se mogu ponovo izgraditi iz potvrđenih podataka.

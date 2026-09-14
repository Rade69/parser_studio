---
title: "Parser Studio — kanonski plan realizacije"
description: "Jedini važeći plan za nastavak razvoja Parser Studija: Modular Monolith + Hexagonal Architecture + MVVM + Evidence-first Learning, sa Gold Ground Truthom, automatskim layout profilima, determinističkim codegenom i verifikacijom generisanog parsera."
project: "Parser Studio"
version: "3.0"
date: "2026-09-14"
status: "CANONICAL / JEDINI VAŽEĆI PLAN"
source_repo: "https://github.com/Rade69/parser_studio"
supersedes:
  - "PARSER_STUDIO_KONSOLIDOVANI_IMPLEMENTACIONI_PLAN_V2"
  - "PARSER_STUDIO_PLAN_ARHITEKTONSKOG_REFAKTORA"
  - "PARSER_STUDIO_IMPLEMENTACIONI_PLAN_ZA_AGENTA v1"
  - "PARSER_STUDIO_KONSOLIDOVANI_PLAN_I_PREPORUKE"
  - "PLAN.md v2"
---

# Parser Studio — kanonski plan realizacije v3

## 0. Status ovog dokumenta

Ovo je **jedini važeći plan** prema kojem se nastavlja realizacija Parser Studija.

Ako se ovaj dokument razlikuje od:

- starog `PLAN.md`,
- `PARSER_STUDIO_KONSOLIDOVANI_PLAN_I_PREPORUKE.md`,
- `PARSER_STUDIO_IMPLEMENTACIONI_PLAN_ZA_AGENTA.md`,
- `PARSER_STUDIO_KONSOLIDOVANI_IMPLEMENTACIONI_PLAN_V2`,
- `PARSER_STUDIO_PLAN_ARHITEKTONSKOG_REFAKTORA.md`,
- README-a,
- komentara/docstringova iz starog pravca,

**ovaj dokument ima prednost.**

Stari planovi se čuvaju samo kao istorija odluka.

Agent ne smije iz njih vraćati odbačene koncepte u aktivnu arhitekturu.

---

# 1. Suština proizvoda

Parser Studio nije običan OCR alat i nije samo generator parsera.

Njegova uloga je:

> **od stvarnih faktura izgraditi provjerljivo i trajno znanje o tome kako se dokumenti čitaju, koristiti to znanje za sve bolju ekstrakciju novih faktura i na kraju generisati samostalan vendor parser za Deklarant Pro.**

Centralni tok:

```text
ORIGINALNI DOKUMENT
        ↓
Document Adapter
        ↓
DocumentEvidence
        ↓
Candidate Producers
        ↓
Candidates
        ↓
Resolver + Validators
        ↓
ExtractionDraft
        ↓
Review / Correction
        ↓
USER_VERIFIED
        ↓
Learning Events
        ↓
Gold Ground Truth
        ↓
Layout Fingerprint
        ↓
Automatic Layout Profile
        ↓
Learned Extraction
        ↓
OCR Recovery po potrebi
        ↓
VendorParserModel
        ↓
Deterministički Code Generator
        ↓
generated_vendor_parser.py
        ↓
Verifier / Export Gate
        ↓
DEKLARANT PRO
```

---

# 2. Arhitektura je zaključana

Parser Studio koristi:

> **Modular Monolith**
>
> + **Hexagonal Architecture / Ports & Adapters**
>
> + **MVVM samo za PySide6 presentation sloj**
>
> + **Evidence-first domain**
>
> + **append-only Learning history**
>
> + **SQLite projections**
>
> + **derived Layout Profiles**
>
> + **deterministički VendorParserModel → Codegen → Verification**

Ne uvoditi:

- mikroservise,
- distribuirani sistem,
- full Event Sourcing framework,
- CQRS framework,
- enterprise DDD ceremoniju,
- generičke `services/`, `utils/`, `managers/` catch-all foldere.

---

# 3. Nepromjenjive odluke

## ARCH-001 — Samostalan finalni parser

Krajnji proizvod je `.py` parser koji:

- ne uvozi ništa iz `parser_studio`,
- ne zavisi od Parser Studio runtime-a,
- ne zahtijeva mrežu,
- ne zahtijeva AI API ključ,
- koristi samo dozvoljene Deklarant Pro/Python helper-e i biblioteke koje klijentska aplikacija već distribuira.

---

## ARCH-002 — Parser Studio i Deklarant Pro ostaju odvojeni

`deklarant_pro` je za Parser Studio:

- contract izvor,
- read-only oracle,
- read-only pomoć pri razvoju/verifikaciji.

Parser Studio ne mijenja Deklarant Pro.

Ako generisani parser zahtijeva izmjenu Deklarant Pro aplikacije, to se prijavljuje kao nalaz.

---

## ARCH-003 — Gold Ground Truth je jedini stabilni autoritet

Samo korisnički potvrđena vrijednost dobija status:

```text
USER_VERIFIED
```

i može ući u Gold Ground Truth.

Sljedeće NISU automatski Gold:

```text
AUTO
AI_PROPOSED
PARSER_ORACLE
PROFILE_PREDICTED
OCR_RECOVERED
```

Sve mora biti provjerljivo.

---

## ARCH-004 — Layout Profile je izvedeni artefakt

Profil se gradi iz Gold podataka.

```text
Gold Ground Truth
       ↓
Profile Builder
       ↓
Layout Profile
```

Nikada:

```text
Layout Profile
       ↓
   Gold Ground Truth
```

Profil se mora moći obrisati i ponovo izgraditi.

---

## ARCH-005 — Korisnik ne programira parser

Korisnik NE:

- bira engine,
- mapira kolone,
- crta PDF granice,
- pravi JSON profil,
- piše regex,
- pravi boolean detection tree,
- uređuje `VendorParserModel`.

Korisnik:

- ubaci dokument,
- pregleda rezultat,
- ispravi grešku,
- potvrdi vrijednost/fakturu.

---

## ARCH-006 — AI je opcionalan savjetnik

Default:

```text
PS_AI_MODE=off
```

Sistem mora raditi bez AI-a.

AI:

- predlaže Candidate,
- mora imati Locator,
- mora proći grounding,
- nije automatski autoritet,
- ne piše finalni Python kod,
- ne mijenja Gold Ground Truth.

---

## ARCH-007 — Docling je PDF adapter, ne domain

Docling je primarni PDF document engine.

Ali domain ne smije znati da Docling postoji.

Docling je adapter iza:

```text
DocumentReader
```

porta.

PP-StructureV3/Paddle nije dio arhitekture.

---

## ARCH-008 — Verifikuje se stvarni generisani `.py`

Interni model nije dovoljan.

Izvoz je dozvoljen tek kada se pokrene i prođe verifikaciju:

```text
generated_vendor_parser.py
```

---

## ARCH-009 — Pravno značajne vrijednosti se ne izmišljaju

Zabranjeno:

- tarifni broj iz opisa robe,
- vrijednost bez dokaza,
- tiho razrješenje konflikta,
- korekcija OCR-a samo na osnovu formule,
- zaokruživanje masa na dvije decimale.

Ako nema dovoljno dokaza:

```text
AMBIGUOUS
```

ili:

```text
FAILED
```

---

## ARCH-010 — Stvarne fakture ne idu u Git

Nikad u Git:

- stvarne fakture,
- page rasteri,
- Docling raw output stvarnih faktura,
- AI cache sa poslovnim podacima,
- Gold Dataset sa stvarnim poslovnim sadržajem,
- izvještaji sa poslovnim podacima.

---

# 4. Ciljnih 20 poslovnih podataka

Ovo je zaključan poslovni scope ekstrakcije.

## 4.1 Invoice nivo — 9 polja

1. broj fakture
2. datum fakture
3. valuta
4. izvoznik / prodavac
5. uvoznik / kupac
6. Incoterm / paritet
7. ukupna bruto masa
8. ukupna neto masa
9. izjava o porijeklu

## 4.2 Item nivo — 11 polja

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

Interni podaci poput:

- confidence,
- evidence,
- source,
- diagnostics,
- issue list,
- profile version,
- extractor id

nisu dodatna poslovna polja.

---

# 5. Statusi vrijednosti

Svako canonical polje mora imati jedan od statusa:

```text
FOUND
NOT_PRESENT
AMBIGUOUS
FAILED
```

## FOUND

Vrijednost postoji i ima dokaz/provenance.

## NOT_PRESENT

Provjeren je odgovarajući scope dokumenta i podatak stvarno ne postoji.

`NOT_PRESENT` nije isto što i "nismo našli".

## AMBIGUOUS

Postoje dva ili više realnih kandidata bez dovoljno dokaza za jednoznačan izbor.

## FAILED

Podatak vjerovatno postoji, ali extraction/reading nije uspio.

---

# 6. Konačna package struktura

```text
parser_studio/
│
├── src/
│   └── parser_studio/
│
│       ├── domain/
│       │   ├── invoice/
│       │   │   ├── models.py
│       │   │   ├── fields.py
│       │   │   └── status.py
│       │   │
│       │   ├── evidence/
│       │   │   ├── locator.py
│       │   │   ├── models.py
│       │   │   └── tables.py
│       │   │
│       │   ├── extraction/
│       │   │   ├── candidate.py
│       │   │   ├── context.py
│       │   │   ├── header_matching.py
│       │   │   └── validation.py
│       │   │
│       │   ├── learning/
│       │   │   ├── events.py
│       │   │   ├── models.py
│       │   │   └── projections.py
│       │   │
│       │   ├── profiles/
│       │   │   ├── models.py
│       │   │   ├── fingerprint.py
│       │   │   └── rules.py
│       │   │
│       │   └── parser_model/
│       │       └── vendor_parser_model.py
│       │
│       ├── application/
│       │   ├── ingest/
│       │   ├── extraction/
│       │   │   ├── analyze_invoice.py
│       │   │   ├── resolver.py
│       │   │   ├── validators/
│       │   │   └── producers/
│       │   │
│       │   ├── review/
│       │   │   ├── review_invoice.py
│       │   │   └── confirm_invoice.py
│       │   │
│       │   ├── learning/
│       │   ├── profiles/
│       │   │   ├── build_profile.py
│       │   │   └── match_profile.py
│       │   │
│       │   ├── generation/
│       │   └── verification/
│       │
│       ├── ports/
│       │   ├── document_reader.py
│       │   ├── candidate_producer.py
│       │   ├── learning_repository.py
│       │   ├── advisor.py
│       │   ├── parser_oracle.py
│       │   ├── parser_generator.py
│       │   └── parser_verifier.py
│       │
│       ├── adapters/
│       │   ├── documents/
│       │   │   ├── excel_reader.py
│       │   │   ├── docling_reader.py
│       │   │   └── rasterizer.py
│       │   │
│       │   ├── persistence/
│       │   │   └── sqlite/
│       │   │       ├── connection.py
│       │   │       ├── migrations.py
│       │   │       ├── learning_repository.py
│       │   │       └── projections.py
│       │   │
│       │   ├── ai/
│       │   ├── declarant_pro/
│       │   ├── codegen/
│       │   │   ├── generator.py
│       │   │   ├── guards.py
│       │   │   └── templates/
│       │   └── verification/
│       │
│       ├── presentation/
│       │   ├── qt/
│       │   │   ├── views/
│       │   │   ├── viewmodels/
│       │   │   └── widgets/
│       │   └── cli/
│       │       └── psbuild.py
│       │
│       └── bootstrap.py
│
├── contract/
│   └── ... privremeno ostaje na root nivou tokom migracije
│
├── tests/
│   ├── unit/
│   │   ├── domain/
│   │   ├── application/
│   │   └── adapters/
│   ├── integration/
│   ├── architecture/
│   └── fixtures/
│
├── docs/
│   ├── PLAN.md
│   └── istorija/
│
└── pyproject.toml
```

---

# 7. Pravila zavisnosti

## DEP-001 — Domain je čist

`domain/` ne smije importovati:

```text
PySide6
sqlite3
openpyxl
xlrd
docling
requests
httpx
adapters
presentation
contract
```

Dozvoljeno:

- Python stdlib,
- domain moduli,
- eventualno Pydantic samo ako je stvarno potreban za stabilan domain schema contract.

Preferirati dataclasses/value objects za čisti domain gdje nema potrebe za Pydanticom.

---

## DEP-002 — Application zavisi od domain + ports

`application/` smije koristiti:

```text
domain
ports
```

Ne smije importovati:

```text
adapters
presentation
PySide6
sqlite3
docling
openpyxl
xlrd
```

---

## DEP-003 — Ports su apstrakcije

`ports/` ne smije zavisiti od adaptera/presentation sloja.

---

## DEP-004 — Adapters zavise prema unutra

Adapter implementira port i može koristiti konkretnu tehnologiju.

Primjeri:

```text
DoclingDocumentReader → DocumentReader
SQLiteLearningRepository → LearningRepository
HttpVisionAdvisor → Advisor
DeklarantProOracle → ParserOracle
JinjaParserGenerator → ParserGenerator
SubprocessParserVerifier → ParserVerifier
```

---

## DEP-005 — Presentation koristi application use-caseove

View i ViewModel ne smiju direktno zvati:

```text
SQLite
Docling
openpyxl
AI HTTP transport
codegen template
subprocess verifier
```

---

# 8. Centralni domain modeli

## 8.1 Locator

```python
@dataclass(frozen=True, slots=True)
class Locator:
    source_path: str
    kind: Literal["pdf", "excel", "text"]

    page: int | None = None
    bbox: tuple[float, float, float, float] | None = None

    sheet: str | None = None
    row: int | None = None
    col: int | None = None

    char_span: tuple[int, int] | None = None
```

PDF bbox:

```text
x0, y0, x1, y1
```

Koordinate se u canonical evidence sloju normalizuju na `[0,1]`, origin top-left, osim ako adapter ima razlog da privremeno čuva native koordinate.

---

## 8.2 Evidence

```python
@dataclass(frozen=True, slots=True)
class Evidence:
    raw_value: Any
    raw_text: str
    locator: Locator
    element_type: str
    source_id: str | None = None
```

Evidence predstavlja nešto što je stvarno viđeno u dokumentu.

---

## 8.3 DocumentEvidence

Standardizovan document model nezavisan od Doclinga/Excela.

Minimalno može sadržati:

```text
document_id
source files
pages
text elements
tables
cells
page dimensions
metadata
```

Ostatak sistema ne koristi Docling objekte direktno.

---

## 8.4 Candidate

```python
@dataclass(frozen=True, slots=True)
class Candidate:
    field: str
    raw_value: Any
    normalized_value: Any
    locator: Locator
    evidence: str
    producer_id: str
    ai_assisted: bool = False
    issues: tuple[str, ...] = ()
```

Candidate nije istina.

---

## 8.5 ExtractionDraft

Sadrži:

```text
resolved fields
item rows
candidate sets
conflicts
unresolved fields
validation results
```

---

## 8.6 CanonicalInvoice

Mora predstaviti svih 20 ciljnih poslovnih polja.

Svako polje ima:

```text
value
status
provenance/evidence
```

---

# 9. CandidateProducer umjesto Engine

Stari centralni koncept:

```text
Engine
probe()
extract(config)
```

je ukinut.

Novi port:

```python
class CandidateProducer(Protocol):
    producer_id: str

    def propose(
        self,
        evidence: DocumentEvidence,
        context: ExtractionContext,
    ) -> list[Candidate]:
        ...
```

Planirane implementacije:

```text
ExcelHeaderProducer
LabelRightProducer
LabelBelowProducer
TableHeaderProducer
ColumnContentProducer
ValueShapeProducer
KnownLayoutProducer
OcrRecoveryProducer
AiAdvisorProducer
ParserOracleProducer
```

Resolver ne smije imati posebne grane tipa:

```text
if ai...
if excel...
if profile...
```

Sve su Candidates.

---

# 10. Šta se radi sa postojećim `ExcelHeadersEngine`

Ne baca se.

Razdvaja se.

## `COLUMN_ALIASES`

Ide u:

```text
domain/invoice/fields.py
```

## `normalize_header()`, `_match_score()`, `identify_columns()`

Ide u:

```text
domain/extraction/header_matching.py
```

## `find_header_row()`, footer logika i interpretacija redova

Ide u:

```text
application/extraction/producers/excel_header.py
```

## `ExcelDocument`

Ide u:

```text
adapters/documents/excel_reader.py
```

Postojeći regression testovi moraju ostati zeleni tokom migracije.

---

# 11. Learning arhitektura

Learning sloj je evidence-first i append-only.

Ne želimo da ispravka samo prepiše prethodnu vrijednost.

Primjer istorije:

```text
EXTRACTED
raw = "12.7"

VALIDATION_FAILED
reason = "Q × P != A"

USER_CORRECTED
old = "12.7"
new = "72.77"

USER_VERIFIED
value = "72.77"
```

---

# 12. LearningEvent

Minimalno:

```text
id
document_id
item_id
field_name
event_type
old_value
new_value
locator
source
producer_id
profile_version
created_at
```

Događaji su append-only.

Ne brišu se zbog obične korekcije.

---

# 13. LearningRepository port

```python
class LearningRepository(Protocol):
    def append_event(self, event: LearningEvent) -> None:
        ...

    def get_document_state(
        self,
        document_id: str
    ) -> VerifiedDocument:
        ...

    def list_gold_documents(
        self,
        vendor_id: str | None = None
    ) -> list[VerifiedDocument]:
        ...
```

SQLite je samo jedna implementacija.

---

# 14. SQLite adapter

```text
adapters/persistence/sqlite/
    connection.py
    migrations.py
    learning_repository.py
    projections.py
```

Predložene storage strukture:

```text
documents
document_files
extraction_runs
field_candidates
learning_events

vendors
layout_fingerprints
layout_profiles
profile_versions

parser_builds
verification_runs
```

Brze projekcije mogu sadržati:

```text
current_verified_fields
current_verified_items
gold_documents
```

ali nisu glavni izvor istorije.

---

# 15. Gold Dataset je projection

Gold Dataset se izvodi iz `USER_VERIFIED` eventova.

```text
Learning Events
      ↓
Gold Projection
```

Ne postoji drugi paralelni "tajni" ground truth.

Ako se projection obriše, mora se moći ponovo izgraditi.

---

# 16. Document adapteri

## 16.1 Excel

```text
DocumentReader
      ↑
ExcelDocumentReader
```

`openpyxl` i `xlrd` ostaju isključivo u adapteru.

---

## 16.2 PDF / Docling

```text
DocumentReader
      ↑
DoclingDocumentReader
```

Docling raw rezultat se kešira/persistira lokalno radi reproducibilnosti.

Sačuvati:

```text
text
page
bbox
element type
table id
row
column
header information
```

Markdown nije autoritativni interni format.

---

## 16.3 Rasterizer

Poseban adapter:

```text
PageRasterizer
```

koristi se za:

- Review GUI,
- bbox overlay,
- OCR Recovery,
- vision AI.

---

# 17. Review / Annotation

Centralni korisnički workspace:

```text
┌────────────────────────────┬──────────────────────────────┐
│                            │ INVOICE FIELDS               │
│       ORIGINAL PDF         │ broj: ...               ✓   │
│                            │ datum: ...              ✓   │
│       bbox highlight       │ valuta: ...             ✎   │
│                            │ ...                          │
│                            ├──────────────────────────────┤
│                            │ ITEMS                        │
│                            │ 1 | ...                      │
│                            │ 2 | ...                      │
└────────────────────────────┴──────────────────────────────┘
```

Akcije:

```text
POTVRDI
ISPRAVI
AMBIGUOUS
NOT_PRESENT
```

`POTVRDI FAKTURU` stvara `USER_VERIFIED` learning događaje.

---

# 18. MVVM pravila

```text
View
 ↓
ViewModel
 ↓
Application Use Case
```

ViewModel smije znati UI stanje.

Ne smije sadržavati:

```text
OCR
SQL
Docling
profile learning
business validation
codegen
```

---

# 19. Application use-caseovi

Planirani use-caseovi:

```text
ImportDocument
AnalyzeInvoice
ReviewInvoice
ConfirmInvoice

BuildLayoutFingerprint
BuildLayoutProfile
MatchLayoutProfile

RecoverFieldOCR

GenerateVendorParser
VerifyVendorParser
ExportVendorParser
```

CLI i Qt pozivaju iste use-caseove.

---

# 20. Deterministički resolver

Resolver kombinuje Candidates.

Primjer quantity:

```text
header ~= Quantity
+
numeric values
+
susjedna poznata JM kolona
+
Q × P ≈ A
```

Rezultat:

```text
FOUND
AMBIGUOUS
FAILED
```

Ne koristi "najveći score uvijek pobjeđuje" ako postoje realni konflikti.

---

# 21. Concept library

Za poslovni koncept čuvati:

```text
aliases
language
expected value type
spatial relation
priority
negative context
```

Reuse postojećih Deklarant Pro ideja/helpera gdje je smisleno:

```text
_ITEM_TAGS
parse_eu_number
normalize_tariff_number
KNOWN_JM
infer_origin_column
detect_incoterm
OriginStatementDetector
```

Ali finalni parser ne smije zavisiti od Parser Studio koda.

---

# 22. Prvi Gold Dataset

Obavezni pilot:

```text
Faktura-1       11 stavki
Faktura-2        4 stavke
Medicopharm     84 stavke
Sumaprom       138 stavki
-------------------------
UKUPNO         237 stavki
```

Za svaki dokument:

- svih 9 invoice polja,
- svih 11 item polja,
- sve stavke,
- statusi,
- evidence/locator gdje je moguće.

Originalni dokument je autoritet.

---

# 23. Oracle bootstrap iz postojećih parsera

Tok:

```text
sample
 ├── postojeći vendor parser → ImportResult
 └── Document Adapter → Evidence

ImportResult value
       ↓
PARSER_ORACLE Candidate
       ↓
povezivanje sa Evidence
       ↓
korisnička potvrda
       ↓
USER_VERIFIED
```

Stari parser nije automatski istina.

---

# 24. Layout Fingerprint

Iz potvrđenih dokumenata izvoditi:

```text
page count
page dimensions
anchor tokens
table count
table header signatures
column count
relative column widths
item table region
footer/header patterns
repeated structure
```

Ne koristiti:

- filename,
- vendor naziv kao jedini signal,
- samo apsolutne koordinate.

Pilot:

```text
Faktura-1
Faktura-2
```

moraju biti prepoznate kao isti ili vrlo blizak layout.

---

# 25. Automatic Layout Profile

Profil se automatski gradi iz više Gold primjera istog layouta.

Može sadržati:

```text
stable anchors
anchor → field relations
item table signature
semantic column roles
relative column positions
expected value shapes
cross-field validations
header/footer regions
known optional fields
document-scope rules
```

Primjer:

```text
quantity:
  source = ITEM_TABLE
  header aliases = [...]
  relative column = 7
  datatype = numeric
  validation = Q*P≈A
```

Korisnik ne uređuje profil.

---

# 26. Layout Profile Matcher

Rezultat:

```text
HIGH
REVIEW
NO_MATCH
```

Bez lažnih procenata dok sistem nije kalibrisan.

Isti vendor može imati više layouta:

```text
Vendor
 ├── Layout v1
 ├── Layout v2
 └── Layout v3
```

Novi layout ne prepisuje stari.

---

# 27. Learned Extraction

Za poznati layout:

```text
generic Candidates
+
profile-guided Candidates
        ↓
Resolver
```

Cilj:

- manje unresolved vrijednosti,
- bolja lokalizacija OCR greške,
- stabilnija ekstrakcija,
- bez rasta false-positive rezultata.

---

# 28. OCR Recovery

Aktivira se kada:

- zna se semantička uloga,
- postoji bbox,
- OCR vrijednost je sumnjiva/nevalidna,
- status je `FAILED` ili `AMBIGUOUS`.

Tok:

```text
originalni PDF
    ↓
high-res page render
    ↓
crop bbox
    ↓
targeted reread
    ↓
Candidate
    ↓
validation
```

Formula može detektovati problem.

Ne smije sama izmisliti novu pravno značajnu vrijednost.

---

# 29. AI Advisor

Port:

```text
Advisor
```

Adapter:

```text
HttpVisionAdvisor
```

Režimi:

```text
off
cache-only
live
```

Default:

```text
off
```

AI Candidate mora imati:

```text
field
raw_value
locator
evidence
```

Kod postavlja:

```text
ai_assisted=True
```

---

# 30. Grounding gate

AI kandidat mora biti potvrdiv u dokumentu.

Dozvoljena minimalna normalizacija:

```text
Unicode NFKC
collapsed whitespace
case-insensitive
```

Bez fuzzy grounding-a.

Odbačeni kandidat se loguje.

---

# 31. AI cache

Key:

```text
model_id
prompt_id
prompt_version
payload_sha256
```

`payload_sha256` hashira stvarni input modelu.

AI cache stvarnih dokumenata je lokalni privatni podatak i ne ide u Git.

---

# 32. VendorParserModel

Domain model:

```text
domain/parser_model/vendor_parser_model.py
```

Sadrži:

```text
vendor identity rules
layout detection rules
invoice extraction rules
item table rules
column roles
normalization rules
validation rules
fallbacks
required source files
consumed_paths behavior
```

Ne sadrži:

- slobodan AI Python,
- hardcoded output konkretne fakture,
- Parser Studio runtime pozive.

---

# 33. Codegen adapter

```text
adapters/codegen/
    generator.py
    guards.py
    templates/
```

Tok:

```text
VendorParserModel
       ↓
Jinja2 templates
       ↓
generated_vendor_parser.py
```

---

# 34. Codegen guards

Obavezno:

```text
ast.parse()
compile()
import allowlist
ruff
```

Zabranjeno u generisanom kodu:

```text
eval
exec
__import__
nedozvoljeni dinamički import
from parser_studio ...
```

---

# 35. Verification arhitektura

Application sloj definiše šta znači "parser prolazi".

Adapter sloj implementira subprocess pokretanje.

```text
application/verification/
        ↓
ParserVerifier PORT
        ↓
adapters/verification/
```

Verifier pokreće stvarni `.py`.

---

# 36. Verification gate

Izvoz je dozvoljen samo ako:

- pozitivni Gold testovi PASS,
- negative detect testovi PASS,
- sva obavezna polja odgovaraju,
- nema neriješenog pravno značajnog konflikta,
- korišteni AI-assisted elementi su potvrđeni,
- nema Parser Studio runtime importa.

---

# 37. Negative detect corpus

`detect_*` mora odbiti:

- fakture drugih vendora,
- slične dokumente koji ne pripadaju parseru,
- generičke PDF/Excel dokumente.

Generator se ne smatra spremnim bez negative detection testova.

---

# 38. Contract sa Deklarant Pro

Postojeći `contract/` se zadržava tokom arhitektonske migracije.

Sadrži vendorovanu kopiju Deklarant Pro ugovora i drift check.

Ne smije postati Parser Studio domain.

Dugoročni target:

```text
adapters/declarant_pro/contract/
```

ali se contract migracija radi odvojeno od prvog arhitektonskog refaktora.

Pravilo:

```text
domain       X→ contract
application  X→ contract

declarant_pro adapter → contract
codegen adapter       → contract
verification adapter  → contract
```

---

# 39. Architecture tests

Obavezno napraviti:

```text
tests/architecture/test_import_boundaries.py
```

Automatski provjerava zabranjene import pravce.

Minimalna pravila:

```text
domain → NO adapters
domain → NO presentation
domain → NO PySide6
domain → NO sqlite3
domain → NO Docling

application → NO adapters
application → NO presentation

presentation → NO direct sqlite3
presentation → NO direct Docling
presentation → NO direct openpyxl
```

---

# 40. `pyproject.toml`

Preći na `src/` layout.

Target:

```toml
[project]
name = "parser-studio"
version = "0.3.0"
description = "Learning-first alat za izradu i verifikaciju parsera faktura za Deklarant Pro"
requires-python = ">=3.11"

[project.scripts]
psbuild = "parser_studio.presentation.cli.psbuild:main"

[tool.setuptools.packages.find]
where = ["src"]
```

Zadržati kada se koriste:

```text
PySide6
openpyxl
xlrd
rapidfuzz
pydantic
jinja2
```

`cryptography` ukloniti ili premjestiti u optional `signing` dok potpisivanje nije implementirano.

Docling dodati kada se implementira Docling adapter.

---

# 41. FAZA A — Arhitektonski refaktor postojećeg repoa

Ova faza se radi PRIJE novih Learning-first funkcija.

---

## A0 — Baseline i sigurnosna mreža

### Cilj

Tačno zabilježiti stanje prije refaktora.

### Zadaci

- pokrenuti sve postojeće testove;
- pokrenuti contract drift check prema živom Deklarant Pro;
- zapisati baseline broj PASS/SKIP;
- potvrditi da su stvarne fakture ignorisane u Git-u;
- arhivirati stare planove;
- ovaj dokument postaviti kao `docs/PLAN.md`.

### Acceptance

- baseline test rezultat dokumentovan;
- contract drift stvarno pokrenut;
- v3 je jedini aktivni plan.

---

## A1 — `src/` package layout

### Cilj

Napraviti novu fizičku strukturu bez funkcionalne promjene.

### Kreirati

```text
src/parser_studio/
    domain/
    application/
    ports/
    adapters/
    presentation/
```

### Zadaci

- podesiti `pyproject.toml`;
- dodati minimalni bootstrap;
- testovi moraju raditi iz novog package layouta.

### Acceptance

Postojeće ponašanje nije promijenjeno.

---

## A2 — Evidence domain

### Cilj

Uvesti:

```text
Locator
Evidence
DocumentEvidence
Candidate
ExtractionContext
```

### Zadaci

- definisati immutable value objects;
- napisati unit testove;
- napraviti compatibility adapter za postojeći `Cell` gdje je potrebno.

### Acceptance

Postojeći Excel provenance može se predstaviti novim modelom bez gubitka informacije.

---

## A3 — Excel document adapter

### Cilj

Premjestiti postojeći Excel I/O u adapter.

### Target

```text
adapters/documents/excel_reader.py
```

### Zadaci

- zadržati `.xlsx/.xls`;
- zadržati keširanje;
- zadržati sve sheetove;
- implementirati `DocumentReader`;
- prilagoditi testove.

### Acceptance

Svi postojeći ExcelDocument testovi PASS.

---

## A4 — Ukinuti Engine

### Cilj

Ukloniti stari:

```text
Engine
ProbeResult
suggested_config
```

### Zadaci

- uvesti `CandidateProducer`;
- rastaviti `ExcelHeadersEngine`;
- `COLUMN_ALIASES` u domain;
- matching logiku u domain;
- orchestration u application producer.

### Acceptance

Postojeći testovi za:

- dijakritike,
- kratke aliase,
- column matching,
- header detection,
- footer detection,
- provenance

ostaju zeleni.

---

## A5 — Application use-case osnova

### Implementirati skeleton:

```text
ImportDocument
AnalyzeInvoice
ReviewInvoice
ConfirmInvoice
```

Bez GUI zavisnosti.

### Acceptance

Use-caseovi se testiraju headless.

---

## A6 — LearningRepository + events

### Cilj

Postaviti Learning-first temelj.

### Uvesti

```text
LearningEvent
LearningRepository
SQLiteLearningRepository
```

### Acceptance

Može se:

1. appendovati event,
2. restartovati repo/session,
3. rekonstruisati document state.

---

## A7 — Presentation migracija i cleanup

### Zadaci

Premjestiti:

```text
views → presentation/qt/views
viewmodels → presentation/qt/viewmodels
cli → presentation/cli
```

Ukloniti zastarjelo:

```text
views/wizard
core/engines
core/synth
generic services/
generic mapping/
generic transforms/
```

Tek nakon što compatibility nije više potrebna.

### Acceptance

Na root nivou nema dvije paralelne arhitekture.

---

# 42. FAZA B — Learning Foundation

---

## B1 — CanonicalInvoice

Implementirati svih 20 poslovnih polja + statuse + provenance.

### Acceptance

Može predstaviti:

```text
Faktura-1
Faktura-2
Medicopharm
Sumaprom
```

bez vendor-specific poslovnih polja.

---

## B2 — DoclingDocumentReader

### Cilj

PDF → DocumentEvidence.

### Persistirati

```text
original
raw Docling structured output
page metadata
tables
cells
bbox
```

### Acceptance

Svaki korišteni element može biti mapiran na originalnu stranicu.

---

## B3 — Rasterizer

Implementirati page render i bbox crop.

### Acceptance

Iz `Locator(page,bbox)` može se dobiti vizuelni crop izvora.

---

## B4 — Review workspace

PySide6 MVVM.

### Acceptance

Jedna kompletna faktura se može:

- otvoriti,
- pregledati,
- ispraviti,
- potvrditi,
- ponovo učitati.

---

## B5 — Prvi Gold corpus

Potvrditi sve četiri pilot fakture.

### Acceptance

```text
237 itema
+
20 ciljnih polja
```

imaju referentne Gold podatke/status.

---

# 43. FAZA C — Generic extraction

---

## C1 — Concept library

Implementirati sinonime i kontekst za svih 20 polja.

---

## C2 — Candidate producers

Minimalni set:

```text
LabelRightProducer
LabelBelowProducer
TableHeaderProducer
ColumnContentProducer
ValueShapeProducer
ExcelHeaderProducer
```

---

## C3 — Resolver

Determinističko kombinovanje kandidata.

---

## C4 — Validators

Minimalno:

```text
syntax
structure
arithmetic
domain
cross-field
cross-document
```

---

## C5 — Real Gold evaluation

Mjeriti stvarnu accuracy nad Gold corpusom.

Ne koristiti F10 ili sampled rows kao zamjenu za full extraction accuracy.

---

# 44. FAZA D — Oracle bootstrap

---

## D1 — DeklarantProOracle adapter

Čita postojeći vendor parser read-only.

---

## D2 — Oracle → Candidate

Svaka oracle vrijednost se pokušava povezati sa Evidence.

---

## D3 — Human verification

Oracle postaje Gold tek nakon potvrde.

---

# 45. FAZA E — Layout Learning

---

## E1 — Fingerprint

Implementirati LayoutFingerprint.

---

## E2 — Profile Builder

Gold primjeri → LayoutProfile.

---

## E3 — Profile Matcher

Rezultat:

```text
HIGH
REVIEW
NO_MATCH
```

---

## E4 — Drift

Novi layout iste firme dobija novu verziju.

---

## E5 — Holdout dokaz

Obavezni eksperiment:

```text
F1 + F2
   ↓
Pekabesko profile
   ↓
treća faktura istog layouta
```

Porediti:

```text
generic-only
vs
profile-guided
```

Profil se smatra korisnim samo ako poboljšava kvalitet bez rasta false-positive rezultata.

---

# 46. FAZA F — Learned Extraction i OCR Recovery

---

## F1 — KnownLayoutProducer

LayoutProfile daje profile-guided Candidates.

---

## F2 — Combined resolver

Generic + learned Candidates.

---

## F3 — OCR Recovery trigger

Samo kada postoji jasan field/region kontekst.

---

## F4 — Targeted reread

BBox → crop → reread → Candidate → validation.

---

## F5 — Recovery metrics

Pratiti:

```text
recovery_attempts
recovered_correctly
still_failed
wrong_recovery
```

---

# 47. FAZA G — AI Advisor

AI dolazi tek kada postoje:

```text
Candidate
Locator
Evidence
Review
Ground Truth
LearningRepository
```

---

## G1 — Advisor port

---

## G2 — NullAdvisor

Za `off`.

---

## G3 — HttpVisionAdvisor

Provider iza transport apstrakcije.

---

## G4 — Grounding

Halucinirani kandidati padaju.

---

## G5 — Cache

`cache-only` mora reprodukovati snimljeni rezultat.

---

# 48. FAZA H — VendorParserModel i Codegen

---

## H1 — VendorParserModel

Domain schema.

---

## H2 — Model Builder

Iz potvrđenog profila i pravila napraviti model.

---

## H3 — Jinja codegen

---

## H4 — Guards

AST + compile + allowlist + ruff.

---

# 49. FAZA I — Verifier

---

## I1 — Runner

Pokretanje generisanog parsera u zasebnom procesu.

Napomena:

To je stabilnost/izolacija, ne sigurnosni sandbox.

---

## I2 — Compare

Svih 20 ciljnih polja.

---

## I3 — Negative detect corpus

---

## I4 — Export gate

Jedan obavezni fail blokira export.

---

# 50. FAZA J — CLI i reports

CLI:

```text
psbuild ingest
psbuild analyze
psbuild gold
psbuild profile
psbuild generate
psbuild verify
psbuild export
```

CLI i GUI koriste iste application use-caseove.

HTML report prikazuje:

```text
original
extracted
Gold
locator
evidence
conflicts
rejected AI
verification diff
```

---

# 51. Tek poslije toga — pravi ML

Ne trenirati model prije kvalitetnog dataseta.

Prvi prag za eksperiment:

```text
100+ verified faktura
1000+ verified item rows
```

Ozbiljniji prag:

```text
500+ faktura
5000+ item rows
```

Mogući zadaci:

```text
layout classification
column role classification
candidate ranking
OCR correction ranking
anomaly detection
```

ML nikad ne mijenja Gold Ground Truth.

---

# 52. Redoslijed realizacije

```text
A0  Baseline
 ↓
A1  src package layout
 ↓
A2  Evidence domain
 ↓
A3  Excel adapter
 ↓
A4  CandidateProducer umjesto Engine
 ↓
A5  Application use-case skeleton
 ↓
A6  LearningRepository + append-only events
 ↓
A7  Presentation migration + cleanup
 ↓
B1  CanonicalInvoice
 ↓
B2  Docling adapter
 ↓
B3  Rasterizer
 ↓
B4  Review workspace
 ↓
B5  Full Gold corpus
 ↓
C1-C5 Generic extraction + resolver + real evaluation
 ↓
D1-D3 Oracle bootstrap
 ↓
E1-E5 Layout learning
 ↓
F1-F5 Learned extraction + OCR recovery
 ↓
G1-G5 AI advisor
 ↓
H1-H4 VendorParserModel + codegen
 ↓
I1-I4 Verifier + export gate
 ↓
J   CLI + reports
 ↓
KASNIJE
ML eksperimenti
```

---

# 53. Glavni razvojni gate-ovi

## GATE-1 — Architecture Locked

Mora biti završeno:

```text
A0-A7
```

Prije novih većih funkcija.

---

## GATE-2 — Learning Foundation

Mora biti završeno:

```text
B1-B4
```

prije ozbiljnog layout learninga.

---

## GATE-3 — Gold Ready

Mora biti završen:

```text
B5
```

prije ocjenjivanja "tačnosti" novog sistema.

---

## GATE-4 — Layout Learning Proven

Mora biti dokazano holdout testom iz E5.

---

## GATE-5 — Parser Exportable

Generisani `.py` mora proći I1-I4.

---

# 54. Metrike

## Invoice-level

Za 9 polja:

```text
correct
wrong
missed
correct_not_present
ambiguous
failed
```

## Item-level

Isto za svih 11 item polja.

## Structure

```text
item count
table detection
table stitching
column role accuracy
layout match correctness
```

## Learning

```text
correction count
repeated correction rate
profile version changes
generic vs profile-guided delta
```

## OCR Recovery

```text
attempts
correct recoveries
wrong recoveries
still unresolved
```

## Generated parser

```text
positive Gold PASS/FAIL
negative detect PASS/FAIL
field diffs
runtime
```

---

# 55. Pravila rada za agente

1. Ne tvrditi da je nešto pokrenuto ako nije.
2. Svaki novi modul dolazi sa testom.
3. `PS_AI_MODE=off` mora ostati zelen.
4. Ne dodavati dependency bez obrazloženja.
5. Ne hardkodirati vrijednosti iz pilot faktura.
6. Ne koristiti filename kao layout signal.
7. Ne koristiti vendor ime kao jedini layout signal.
8. Originalni dokument je autoritet.
9. Ako nešto nije provjereno, napisati `NOT VERIFIED`.
10. `NOT_PRESENT` nije sinonim za "nisam našao".
11. Profile se regenerišu iz Gold podataka.
12. Profile ne mijenja Gold.
13. AI bez groundinga ne ulazi u resolver.
14. Deklarant Pro se ne mijenja.
15. Contract se ne "krpi" da test prođe.
16. Stvarne fakture i izvedeni privatni podaci ne idu u Git.
17. Ne uvoditi novu globalnu arhitektonsku apstrakciju bez ažuriranja ovog plana.
18. Ne održavati paralelno staru `core/services/views` i novu arhitekturu duže nego što migration zahtijeva.
19. Svaki compatibility shim mora imati plan uklanjanja.
20. Export bez verification gate-a ne postoji.

---

# 56. Šta se trenutno NE radi

Do GATE-3 ne raditi:

- pravi ML trening,
- generativni AI codegen,
- novi document engine,
- Paddle/PP-Structure,
- cloud storage stvarnih faktura,
- plugin signing,
- skaliranje na mnogo novih vendora,
- performance optimizacije koje komplikuju correctness,
- veliki UI polishing.

---

# 57. Konkretna mapa staro → novo

```text
core/documents/base.py
  → domain/evidence/*
  → ports/document_reader.py

core/documents/excel_document.py
  → adapters/documents/excel_reader.py

core/engines/base.py
  → UKLONITI
  → ports/candidate_producer.py

core/engines/excel_headers.py
  → domain/invoice/fields.py
  → domain/extraction/header_matching.py
  → application/extraction/producers/excel_header.py

core/profile/
  → domain/profiles/
  → application/profiles/

core/library/
  → domain/invoice/fields.py

core/mapping/
  → ukloniti kao generic layer

core/synth/
  → ukloniti

core/transforms/
  → ukloniti kao catch-all

core/codegen/
  → adapters/codegen/

core/verify/
  → application/verification/
  → adapters/verification/

services/
  → application/

views/
  → presentation/qt/views/

viewmodels/
  → presentation/qt/viewmodels/

cli/
  → presentation/cli/
```

---

# 58. Prvi naredni radni paket

**Ne počinjati Doclingom.**

Prvi paket je:

```text
A0 + A1 + A2
```

odnosno:

1. baseline testovi + contract drift,
2. novi `src/parser_studio/` layout,
3. `Locator`, `Evidence`, `DocumentEvidence`, `Candidate`.

Tek kada je to stabilno:

```text
A3 + A4
```

odnosno:

4. Excel adapter,
5. `CandidateProducer` umjesto `Engine`.

To je prvi stvarni arhitektonski gate.

---

# 59. Kriterijum uspjeha cijelog projekta

Parser Studio je uspješan kada:

1. iz stvarnih uzoraka pravi provjeren Gold Dataset;
2. za svaku ključnu vrijednost zna izvor;
3. korisnik ne programira parser;
4. sistem uči layout iz potvrđenih primjera;
5. known-layout extraction poboljšava novi dokument;
6. OCR failure može lokalizovati;
7. korisničke korekcije ostaju trajno znanje;
8. AI je opcionalan, grounded i auditovan;
9. generisani `.py` nema Parser Studio runtime dependency;
10. generisani parser prolazi sve pozitivne Gold testove;
11. `detect_*` ne presreće druge vendore;
12. isti input + ista verzija sistema daju reproducibilan rezultat;
13. novi vendor parser nastaje znatno brže nego ručnim programiranjem bez povećanja rizika.

---

# 60. Konačna arhitektonska slika

```text
                       PRESENTATION
              ┌────────────────────────┐
              │ PySide6 MVVM / CLI     │
              └───────────┬────────────┘
                          │
                    APPLICATION
              ┌───────────▼────────────┐
              │ Use Cases              │
              │ Resolver / Validators  │
              │ Profile workflows      │
              └───────────┬────────────┘
                          │
                        PORTS
       ┌──────────────────┼───────────────────┐
       │                  │                   │
       ▼                  ▼                   ▼
DocumentReader    LearningRepository      Advisor
       │                  │                   │
       ▼                  ▼                   ▼
    ADAPTERS           ADAPTERS            ADAPTERS
 Docling/Excel          SQLite                AI
       │
       └──────────────┐
                      │
                DOMAIN CORE
       ┌─────────────────────────────────────┐
       │ Invoice                             │
       │ Evidence / Locator                  │
       │ Candidate                           │
       │ Learning Events                     │
       │ Gold State                          │
       │ Layout Profile                      │
       │ VendorParserModel                   │
       └─────────────────────────────────────┘
                      │
                      ▼
                  CODEGEN
                      │
                      ▼
             generated_vendor.py
                      │
                      ▼
                VERIFICATION
                      │
                      ▼
                   EXPORT
```

---

# 61. Završna odluka

Parser Studio se od ovog trenutka razvija kao:

> **Learning-first, Evidence-first modularni monolit sa Hexagonal granicama.**

Centralna vrijednost nije pojedinačna heuristika, OCR engine niti trenutno generisani parser.

Centralna vrijednost je:

> **provjerljivo, trajno i regenerabilno znanje o stvarnim dokumentima.**

Sve ostalo — Docling, heuristike, AI, layout profili, OCR recovery, codegen i budući ML — jesu zamjenjivi mehanizmi oko tog znanja.

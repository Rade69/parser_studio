---
task_id: M6
title: "FAZA C — Generic extraction (V3_2 §43: C1 Concept library + C2 Producers + C3 Resolver + C4 Validators + C5 Real Gold evaluation)"
status: ACTIVE
risk: HIGH
date: 2026-09-14
branch: task/faza-c
worktree: H:/parser-studio-worktrees/faza-c
base: dev @ 5fdac03
implementer: Mavis
---

# M6 — FAZA C — Generic Extraction (V3_2 §43)

> Implementirati 5 podzadataka za generičku ekstrakciju: C1 sinonimi/kontekst, C2 kandidatski producenti, C3 Resolver, C4 Validatori, C5 Real Gold evaluation.

**Mavis radi serijski (default po User Memory).** Paralelizam moguć za C2+C4 ako korisnik kaže.

---

## Canonical references

```text
docs/PLAN.md       V3_2 §43 (FAZA C — Generic extraction), §43.1-§43.5 (C1-C5)
.agent/CURRENT_STATE.md   Snapshot nakon M5 (commit 5fdac03)
V3 ARCH-009        Pravno značajne vrijednosti se ne izmišljaju (Validatori)
V3 ARCH-003        Gold Ground Truth jedini stabilni autoritet (C5 evaluation)
V3 milestone:      C1-C5 (Generic extraction)
```

---

## Scope (IN) — 5 podzadataka, serijski

### C1 — Concept library (domain)

```text
src/parser_studio/domain/concepts/__init__.py
src/parser_studio/domain/concepts/concept.py
src/parser_studio/domain/concepts/concept_library.py
```

`Concept` dataclass (frozen=True, slots=True):
- `field: str` (canonical field name, npr. "invoice_number")
- `synonyms: tuple[str, ...]` (aliasi: "broj fakture", "Broj računa", "Invoice No", "Inv No", ...)
- `context_phrases: tuple[str, ...]` (fraze koje ukazuju na polje: "ukupno za plaćanje", "total invoice amount")
- `language: str` (ISO 639-1, npr. "bs", "hr", "en", "sr")

`ConceptLibrary`:
- 20 polja × 3-5 jezika × 5-10 sinonima × 3-5 kontekstualnih fraza
- Lookup: `library.get(field, language) -> Concept | None`
- Index po alias + frazi za brzu pretragu

**Coverage:** Sva 20 ciljnih polja (9 invoice + 11 item) pokrivena sa sinonimima u bs/hr/sr/en.

### C2 — Candidate producers (application/extraction/producers)

```text
src/parser_studio/application/extraction/producers/label_right.py
src/parser_studio/application/extraction/producers/label_below.py
src/parser_studio/application/extraction/producers/table_header.py
src/parser_studio/application/extraction/producers/column_content.py
src/parser_studio/application/extraction/producers/value_shape.py
# excel_header.py — VEC POSTOJI (A4)
```

5 novih Producer-a:

**LabelRightProducer:** Nalazi vrijednost DESNO od labele u istom redu.
- Input: DocumentEvidence + FieldContext (field, language)
- Algoritam: za svaki text element, ako normalized_text match-a concept.synonyms (iz library), vrati Candidate sa vrijednošću iz elementa DESNO.

**LabelBelowProducer:** Vrijednost ISPOD labele u susjednom redu (Excel/tabele).

**TableHeaderProducer:** Identificira header red tabele i mapira kolone na canonical polja koristeći concept.synonyms.

**ColumnContentProducer:** Za zadano polje, vrati SVE vrijednosti u identificiranoj koloni.

**ValueShapeProducer:** Regex/shape match (npr. invoice_number = `^[A-Z]{2,4}[-/]\d{4}[-/]\d+$`, datum = `\d{4}-\d{2}-\d{2}`).

### C3 — Resolver (application/extraction)

```text
src/parser_studio/application/extraction/resolve_candidates.py
```

`ResolveRequest`, `ResolveResult`, `ResolveCandidates` use case:
- Input: ExtractionDraft + ResolutionStrategy
- Algorithm: za svako polje, izaberi "best" Candidate iz kandidata
- Determinizam: prioritet po producer_id (deterministički redoslijed), pa po confidence

```python
@dataclass(frozen=True, slots=True)
class ResolveRequest:
    draft: ExtractionDraft
    strategy: ResolutionStrategy  # FIRST_MATCH | HIGHEST_CONFIDENCE | CONSENSUS

@dataclass(frozen=True, slots=True)
class ResolveResult:
    resolved_by_field: dict[str, Candidate]
    conflicts: tuple[ConflictInfo, ...]  # polja gdje produceri ne setuju
    unresolved: tuple[str, ...]
```

### C4 — Validators (application/extraction/validators)

```text
src/parser_studio/application/extraction/validators/__init__.py
src/parser_studio/application/extraction/validators/base.py
src/parser_studio/application/extraction/validators/syntax.py
src/parser_studio/application/extraction/validators/structure.py
src/parser_studio/application/extraction/validators/arithmetic.py
src/parser_studio/application/extraction/validators/domain.py
src/parser_studio/application/extraction/validators/cross_field.py
src/parser_studio/application/extraction/validators/cross_document.py
```

`Validator` Protocol:
```python
class Validator(Protocol):
    name: str
    def validate(self, draft: ExtractionDraft) -> tuple[Issue, ...]: ...
```

6 Validator-a:
- **SyntaxValidator:** format polja (datum ISO 8601, količina > 0, iznos ≠ null)
- **StructureValidator:** 9 invoice polja prisutna, items.count > 0
- **ArithmeticValidator:** subtotal + tax = total; item.sum(kolicina * cijena) ≈ total
- **DomainValidator:** seller_tax_id validan format (npr. 13 cifara za BiH PIB)
- **CrossFieldValidator:** invoice_number unique, due_date >= invoice_date
- **CrossDocumentValidator:** (FAZA D+) NO_MATCH provjera sa drugim dokumentima

### C5 — Real Gold evaluation (tests/integration)

```text
tests/integration/test_real_gold_evaluation.py
tests/integration/real_gold/__init__.py
tests/integration/real_gold/evaluator.py
tests/integration/real_gold/report.py
```

`RealGoldEvaluator`:
- Input: 4 sintetičke fakture (vec postoje iz M5) + ExtractionPipeline
- Output: EvaluationReport (per-document + aggregate accuracy)

```python
@dataclass(frozen=True, slots=True)
class EvaluationReport:
    per_document: dict[str, DocumentEvaluation]  # document_id -> result
    aggregate_accuracy: float  # 0.0 - 1.0
    field_accuracy: dict[str, float]  # "invoice_number": 0.95, ...
    issues_by_field: dict[str, tuple[Issue, ...]]
```

**Acceptance:** Aggregate accuracy >= 0.70 (threshold za GATE-3), mjereno nad svim 4 fakture × 20 ciljnih polja.

---

## Scope (OUT — ne radim u FAZA C)

- ❌ Layout Learning (FAZA E — E3 Matcher, E4 Drift, E5 Holdout)
- ❌ VendorParserModel generation (FAZA H)
- ❌ Parser Build (FAZA H)
- ❌ Verifier subprocess (FAZA I)
- ❌ AI Advisor HttpVisionAdvisor (FAZA G)
- ❌ DoclingDocumentReader (FAZA B2)
- ❌ Layout Profile Matcher (FAZA E3)

---

## Disjunktni ownership (M6 je serijski, nema paralelnog rada)

M6 SMIJE kreirati/mijenjati:
- `src/parser_studio/domain/concepts/`
- `src/parser_studio/application/extraction/producers/label_*.py`, `table_header.py`, `column_content.py`, `value_shape.py`
- `src/parser_studio/application/extraction/resolve_candidates.py`
- `src/parser_studio/application/extraction/validators/`
- `tests/integration/test_real_gold_evaluation.py`
- `tests/integration/real_gold/`
- `agent_reports/M6-FazaC-task-contract.md` (vec kreiran)
- `agent_reports/2026-09-14-M6-FazaC-evidence.md`

M6 NE SMIJE dodirivati (FAZA A0-A7, M1-M5 output):
- `src/parser_studio/domain/evidence/*`
- `src/parser_studio/domain/invoice/*` (M1)
- `src/parser_studio/domain/profiles/*` (M2)
- `src/parser_studio/ports/*` (M1+M2+M3)
- `src/parser_studio/adapters/*` (M1+M2+M3)
- `src/parser_studio/application/{ingest,review,learning}/*` (M1+M3+M5)
- `src/parser_studio/presentation/*` (M4)
- `src/parser_studio/bootstrap.py`

---

## Acceptance criteria (po podzadatku)

### C1 acceptance
```text
[ ] src/parser_studio/domain/concepts/concept.py — Concept + ConceptLibrary
[ ] Koncepti za SVA 20 ciljnih polja (9 invoice + 11 item)
[ ] Svaki koncept ima 3-10 sinonima u bs/hr/sr/en
[ ] Svaki koncept ima 2-5 context_phrases
[ ] Lookup API: library.get(field, language) -> Concept
[ ] 15-20 unit testova
```

### C2 acceptance
```text
[ ] LabelRightProducer, LabelBelowProducer, TableHeaderProducer, ColumnContentProducer, ValueShapeProducer
[ ] Svaki implementira CandidateProducer Protocol (supports + propose)
[ ] Producer-i koriste ConceptLibrary za match labela
[ ] 25-35 unit testova (5-7 po producer-u)
[ ] Architecture: producer-i importuju domain/concepts/ (dopušteno u application layer)
```

### C3 acceptance
```text
[ ] ResolveRequest + ResolveResult + ResolutionStrategy
[ ] ResolveCandidates use case
[ ] FIRST_MATCH, HIGHEST_CONFIDENCE, CONSENSUS strategije
[ ] ConflictInfo za polja gdje produceri ne setuju
[ ] 10-15 unit testova
```

### C4 acceptance
```text
[ ] Validator Protocol
[ ] SyntaxValidator, StructureValidator, ArithmeticValidator, DomainValidator, CrossFieldValidator, CrossDocumentValidator
[ ] Issue dataclass (severity, field, message)
[ ] 30-40 unit testova (5-7 po validatoru)
[ ] Rule: arithmetic NE SMIJE izmisliti vrijednost (V3 ARCH-009)
```

### C5 acceptance
```text
[ ] RealGoldEvaluator + EvaluationReport
[ ] Test sa 4 sintetičke fakture (iz M5) + ExtractionPipeline
[ ] Aggregate accuracy >= 0.70 (threshold za GATE-3)
[ ] Per-document + per-field breakdown
[ ] 5-10 integration testova
```

### Aggregate
```text
[ ] pytest tests/unit/domain/concepts/ — svi PASS (C1)
[ ] pytest tests/unit/application/extraction/producers/ — svi PASS (C2)
[ ] pytest tests/unit/application/extraction/test_resolve_candidates.py — svi PASS (C3)
[ ] pytest tests/unit/application/extraction/validators/ — svi PASS (C4)
[ ] pytest tests/integration/test_real_gold_evaluation.py — svi PASS (C5)
[ ] pytest cijeli suite — NEMA novih regression-a
[ ] pytest tests/architecture/ — 4/4 PASS (FAZA C NE SMIJE break-ati V3 DEP-001..DEP-004)
[ ] ruff check — All checks passed
[ ] Commit na task/faza-c (5 commit-a, jedan po C1-C5 + 1 evidence commit)
[ ] Push na origin/task/faza-c
[ ] Evidence fajl sa stvarnim pytest izlazom + git diff --stat
```

---

## V3 architecture compliance

```text
domain/concepts/:
  - frozen=True, slots=True
  - NE importuje ports, adapters, presentation
  - Importuje samo stdlib (dataclasses, collections)

application/extraction/producers/* (novi):
  - Implementira CandidateProducer Protocol
  - Importuje domain (concepts, evidence, invoice/fields)
  - NE importuje adapters, presentation
  - Koristi ConceptLibrary za label match

application/extraction/resolve_candidates.py:
  - Importuje ports.candidate_producer, domain.extraction.extraction_draft
  - NE importuje adapters
  - Deterministicki (isti input = isti output)

application/extraction/validators/*:
  - Importuje domain.extraction.extraction_draft + domain.evidence
  - NE importuje adapters
  - NE izmislja vrijednosti (V3 ARCH-009)

tests/integration/real_gold/:
  - NE dirati src/parser_studio/ production kod
  - Koristi vec postojece sintetičke fakture iz M5
```

---

## Risk

**HIGH** — FAZA C je velika (5 podzadataka, 5-7 commit-a, 80-120 novih testova). Greška u:
- C1 ConceptLibrary → svi Producer-i dependent, teško popraviti kasnije
- C3 Resolver → netačan determinizam može pokvariti test reproduktivnost
- C4 Validator → V3 ARCH-009 zahtijeva da arithmetic NE IZMIŠLJA, samo FLAGGIRA

Mitigacija:
- C1 unit testovi sa mock ConceptLibrary (testiranje izolirano)
- C2 producer-i sa determinističkim input fixture-ima
- C3 Resolver test sa poznatim Candidate setovima i očekivanim output
- C4 Validatori test sa sintetičkim ExtractionDraft (NE stvarni dokument)
- C5 RealGoldEvaluator sa SINTETIČKIM podacima (NE stvarne fakture, V3 ARCH-010)

Ako M6 utvrdi da je scope prevelik za jedan session, fallback:
- M6a: C1 + C2 (Concepts + Producers) — jedan task
- M6b: C3 + C4 (Resolver + Validators) — drugi task
- M6c: C5 (Real Gold evaluation) — treći task

---

## Definition of Done

```text
[ ] Svi acceptance kriteriji za C1, C2, C3, C4, C5 zadovoljeni
[ ] Svi testovi PASS (acceptance + regression + architecture)
[ ] Ruff clean za FAZA C fajlove
[ ] Commit na task/faza-c (5 commit-a: C1, C2, C3, C4, C5 + 1 evidence)
[ ] Push na origin/task/faza-c
[ ] Evidence fajl sa stvarnim pytest izlazom + git diff --stat
[ ] Merge u dev (Mavis kao koordinator)
[ ] CURRENT_STATE.md ažuriran sa FAZA C status
```

---

**Status:** ACTIVE — Mavis implementira na `task/faza-c` u `H:/parser-studio-worktrees/faza-c`.
**Paralelan rad:** NEMA (Mavis serijski po default). C2 + C4 paralelno moguć ako korisnik kaže.

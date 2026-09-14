# M7 — FAZA D Task Contract (Oracle bootstrap, V3_2 §44)

**Date:** 2026-09-14
**Milestone:** M7 (FAZA D)
**V3 ref:** §44 — Oracle bootstrap; §23 — Oracle tok (pozadina)
**Owner:** Mavis
**Implementer:** Mavis (serijski default po user pref)
**Reviewer:** Mavis evidence + korisnik final approval
**Worktree:** `H:/parser-studio-worktrees/faza-d/`
**Branch:** `task/faza-d`
**Base:** `dev@51bf1b2` (FAZA C merge)
**Implementer ≠ Reviewer:** NE (Mavis je oba). Korisnik imenuje paralelnog
reviewera ako želi dodatni nivo (per CLAUDE.md default = serijski Mavis).

---

## Scope (V3_2 §44)

3 podzadatka, ~24-30 novih testova:

```text
D1 DeklarantProOracle adapter
   ├─ ports/parser_oracle.py         (Protocol)
   ├─ adapters/declarant_pro/oracle.py          (DeklarantProOracle)
   └─ adapters/declarant_pro/strategy_loader.py (helper)

D2 Oracle → Candidate
   ├─ domain/oracle/oracle_mapping.py           (ImportResult → Candidate mapping)
   ├─ application/extraction/producers/oracle.py (OracleCandidateProducer)
   └─ event type dodatak: ORACLE_CONFIRMED, ORACLE_REJECTED (D3 input)

D3 Human verification
   ├─ application/oracle_bootstrap/bootstrap.py  (use case)
   ├─ application/oracle_bootstrap/confirm_oracle.py (use case)
   └─ application/verification/oracle_vs_gold.py (CrossDocumentValidator-style compare Oracle vs Gold)
```

**NOVA FAZA UI odluka (korišnikov odgovor):** D3 Python API samo — bez Qt widgeta.
Qt UI dolazi u FAZA UI paralelno (UI-04 Gold Dataset review UI već ima coverage
od M5; D3 confirm UI planirana u UI-04 proširenju).

---

## V3 DEP granice (architecture test autoritet)

```text
ports
   -> domain
   X-> adapters, presentation

adapters/declarant_pro
   -> domain, ports
   -> contract  (čita vendorovane tipove: ImportResult, InvoiceLine, Party)
   -> deklarant_pro (read-only, runtime — dodaje sys.path u __init__)
   X-> presentation, sqlite3 (bez vlastitog storage)

application
   -> domain, ports
   X-> adapters (osim import-and-provide u bootstrap.py)
   X-> presentation, contract
   X-> deklarant_pro (aplikacija NE importuje deklarant_pro direktno)
```

**Ključno ograničenje:** Parser Studio `application/` NE importuje `deklarant_pro/`.
Adapter u `adapters/declarant_pro/` JE jedini most.

---

## Disjunktni ownership

Mavis serijski — svi fajlovi u jednom vlasništvu (bez paralelizma). Ali
svaki podzadatak (D1, D2, D3) ima svoj `__init__.py` i svoj commit kako
bi se task tracking i review mogli razdvojiti.

```text
D1 scope (commit "arch(FAZA D/D1): DeklarantProOracle"):
   src/parser_studio/ports/parser_oracle.py
   src/parser_studio/adapters/declarant_pro/__init__.py
   src/parser_studio/adapters/declarant_pro/oracle.py
   src/parser_studio/adapters/declarant_pro/strategy_loader.py
   tests/unit/ports/test_parser_oracle.py
   tests/unit/adapters/declarant_pro/test_oracle.py

D2 scope (commit "arch(FAZA D/D2): Oracle → Candidate"):
   src/parser_studio/domain/oracle/__init__.py
   src/parser_studio/domain/oracle/oracle_mapping.py
   src/parser_studio/application/extraction/producers/oracle.py
   src/parser_studio/domain/learning/learning_event.py  (EventType proširenje)
   tests/unit/domain/oracle/test_oracle_mapping.py
   tests/unit/application/extraction/producers/test_oracle.py

D3 scope (commit "arch(FAZA D/D3): Oracle verification"):
   src/parser_studio/application/oracle_bootstrap/__init__.py
   src/parser_studio/application/oracle_bootstrap/bootstrap.py
   src/parser_studio/application/oracle_bootstrap/confirm_oracle.py
   src/parser_studio/application/verification/__init__.py
   src/parser_studio/application/verification/oracle_vs_gold.py
   tests/unit/application/oracle_bootstrap/test_bootstrap.py
   tests/unit/application/oracle_bootstrap/test_confirm.py
   tests/integration/test_oracle_bootstrap.py
```

---

## D1 — DeklarantProOracle adapter

**Goal:** čita Deklarant Pro ImportStrategy read-only i vraća vendor
`ImportResult` kroz Parser Studio `ParserOracle` Protocol.

**Fajlovi:**

1. `src/parser_studio/ports/parser_oracle.py` — Protocol:
   ```python
   class ParserOracle(Protocol):
       def oracle_name(self) -> str: ...
       def can_handle(self, path: Path) -> bool: ...
       def import_file(self, path: Path, progress=None) -> ImportResult: ...
   ```
   `ImportResult` iz `contract.import_result` (vendorovana kopija).

2. `src/parser_studio/adapters/declarant_pro/oracle.py`:
   - `DeklarantProOracle` implementira `ParserOracle`
   - `__init__(deklarant_pro_root: Path | None = None)` — None = default
     `H:/deklarant_pro`
   - Na `__init__`, dodaje `deklarant_pro_root` u `sys.path` ako već nije
   - `import_file()` poziva `StrategyRegistry.get_registry().import_file(path)`
   - Ako deklarant_pro nije importable → `OracleUnavailableError`
   - Ako nema strategije za format → `OracleUnsupportedFormatError`
   - Loguje `strategy_name` i `priority` u outcome

3. `src/parser_studio/adapters/declarant_pro/strategy_loader.py`:
   - Helper `list_available_strategies() -> list[tuple[str, int]]`
   - Čita `StrategyRegistry` i vraća `(strategy_name, priority)` parove
   - Test-friendly: prima opcionalni `registry` argument

**V3 pravila poštovana:**
- Parser Studio NE mijenja deklarant_pro (read-only)
- `adapters/declarant_pro/` zavisi prema unutra (domain + ports + contract)
- `contract/` je vendorovana kopija, ne original

---

## D2 — Oracle → Candidate

**Goal:** za svaku `ImportResult` vrijednost proizvesti `Candidate` (Producer
pattern iz C2) povezan sa `Evidence`.

**Fajlovi:**

1. `src/parser_studio/domain/oracle/oracle_mapping.py`:
   - `ORACLE_FIELD_MAP: dict[str, str]` — statička mapa
     Deklarant Pro polja → Parser Studio polja (CanonicalInvoice):
     ```python
     {
         "invoice_number": "invoice_number",
         "bruto_kg": "gross_weight_kg",
         "neto_kg": "net_weight_kg",
         "currency": "currency",
         "incoterm_code": "incoterm",
         # ... items[] mapiraju na CanonicalInvoice.lines[i].*
     }
     ```
   - `InvoiceLine` Deklarant Pro polja (naziv_robe, kolicina, cijena_jed,
     iznos, tarifni_broj, zemlja_porijekla, jm, bruto_kg, neto_kg) →
     `CanonicalInvoice.lines[i]` (description, quantity, unit_price,
     line_amount, hs_code, origin_country, uom, gross_weight_kg,
     net_weight_kg)
   - `oracle_to_candidate(oracle_value, target_field) -> Candidate` —
     pretvara oracle vrijednost u Candidate bez Evidence (samo raw)

2. `src/parser_studio/application/extraction/producers/oracle.py`:
   - `OracleCandidateProducer` nasljeđuje `CandidateProducer` Protocol
   - `confidence = 0.95` (visok, jer Oracle je "stari parser koji zna")
   - `produces(field_name, context) -> list[Candidate]`
     - Dohvata ImportResult preko ParserOracle porta (iz konteksta)
     - Mapira oracle vrijednost na target field
     - Povezuje sa Evidence (ako je `context.evidence` dat) preko
       cell_value == oracle_value (exact match) — Locator prosljeđen
     - Vraća listu sa 1 candidate (ako match) ili [] (ako ne)
   - `producer_id = "oracle"`

3. `src/parser_studio/domain/learning/learning_event.py` — proširenje:
   ```python
   class EventType(str, enum.Enum):
       ...
       ORACLE_CONFIRMED = "ORACLE_CONFIRMED"   # korisnik potvrdio oracle vrijednost
       ORACLE_REJECTED = "ORACLE_REJECTED"     # korisnik odbacio oracle vrijednost
   ```

**V3 pravila:**
- `application/` NE importuje deklarant_pro — Oracle se dohvata kroz port
- `domain/oracle/` NE importuje contract (Vendor-agnostički mapping živi u
  adapteru `adapters/declarant_pro/oracle_mapping_runtime.py` AKO treba
  pristup tipovima; inače statička mapa dovoljna)

---

## D3 — Human verification (Python API only)

**Goal:** korisnik potvrđuje/odbacuje Oracle kandidate; potvrda postaje
USER_CONFIRMED event u GoldDataset projection.

**Fajlovi:**

1. `src/parser_studio/application/oracle_bootstrap/bootstrap.py`:
   - `BootstrapOracle` use case
   - `BootstrapRequest(document_id, path_or_evidence, field_filter=None)`
   - `BootstrapResult(draft, oracle_candidates, oracle_metadata)`
   - Tok:
     1. Pozovi `ParserOracle.import_file(path)` → ImportResult
     2. Pozovi `OracleCandidateProducer.produces()` za svaki target field
     3. Vrati `ExtractionDraft` sa oracle kandidatima + metapodacima
        (strategy_name, priority, oracle_version)

2. `src/parser_studio/application/oracle_bootstrap/confirm_oracle.py`:
   - `ConfirmOracle` use case
   - `ConfirmRequest(document_id, field_name, item_id, decision, oracle_value, locator, evidence, actor)`
   - `decision` ∈ {"accept", "reject"}
   - Tok:
     - Ako `accept` → emit `ORACLE_CONFIRMED` event (LearningRepository.append)
       + `USER_CONFIRMED` event sa oracle_value kao confirmed value
     - Ako `reject` → emit `ORACLE_REJECTED` event (bez confirmed value)
   - Vraća `ConfirmResult(accepted: bool, gold_dataset_entry_id: str | None)`

3. `src/parser_studio/application/verification/oracle_vs_gold.py`:
   - `OracleVsGoldComparison` use case (FAZA I preview)
   - `compare(oracle_candidates, gold_dataset_entries) -> ComparisonReport`
   - Za svako polje: status ∈ {MATCH, MISMATCH, MISSING_ORACLE, MISSING_GOLD}
   - Ne piše u storage; samo vraća read-only izvještaj
   - Korisno za evaluaciju tačnosti Oracle-a FAZA I input

4. `src/parser_studio/application/verification/__init__.py` (prazan sada,
   ostaje za FAZA I).

**NEMA Qt UI u D3.** Python API + dataclass. Qt dolazi u FAZA UI paralelno
(koristeći M4 InvoiceReviewView pattern za diff prikaz Oracle vs Evidence).

---

## Acceptance criteria

| # | Kriterij | Status dokaz |
|---|---|---|
| 1 | D1: `DeklarantProOracle.import_file()` vraća ImportResult za test fajl | 8+ testova |
| 2 | D1: `OracleUnavailableError` ako deklarant_pro nije dostupan | 2+ testa |
| 3 | D1: `OracleUnsupportedFormatError` za nepodržan format | 2+ testa |
| 4 | D1: Architecture 4/4 PASS (adapter zavisi od domain+ports, ne od application) | ruff + arch test |
| 5 | D2: `ORACLE_FIELD_MAP` pokriva sva Deklarant Pro polja relevantna za 20 ciljnih polja | unit test |
| 6 | D2: `OracleCandidateProducer.produces()` vraća 1 candidate sa confidence 0.95 za oracle vrijednost | 3+ testa |
| 7 | D2: Producer povezuje oracle vrijednost sa Evidence (Locator) kad je cell_value == oracle_value | 2+ testa |
| 8 | D2: EventType proširen sa ORACLE_CONFIRMED + ORACLE_REJECTED | enum test |
| 9 | D3: `BootstrapOracle` vraća ExtractionDraft sa oracle kandidatima | 3+ testa |
| 10 | D3: `ConfirmOracle(decision="accept")` emit-uje USER_CONFIRMED event | 2+ testa |
| 11 | D3: `ConfirmOracle(decision="reject")` NE emit-uje USER_CONFIRMED event | 2+ testa |
| 12 | D3: `OracleVsGoldComparison` tačno klasificira MATCH/MISMATCH/MISSING_* | 3+ testa |
| 13 | Full pytest: 730 PASS + FAZA D delta (24-30 novih) — ukupno ~754-760 PASS | regression run |
| 14 | Architecture 4/4 PASS (FAZA D NE smije break-ati V3 DEP-001..DEP-004) | arch test |
| 15 | Ruff FAZA D scope: All checks passed! | ruff check |
| 16 | Contract drift: PASS (FAZA D koristi contract/, ali read-only kroz importere) | drift_check |

---

## OUT_OF_SCOPE (prijavi kao nalaz, NE implementiraj u D1-D3)

- **Qt UI za D3** — korisnik odlučio: Python API samo. UI u FAZA UI.
- **Deklarant Pro read-only enforcement** — D1 koristi sys.path hack.
  Dugoročno: subprocess wrapper za punu izolaciju. FAZA I / FAZA H.
- **OCR Reading Map (E3)** — vezan za FAZA E, ne FAZA D.
- **Cache layer za Oracle** — ako isti fajl Oracle-uje 2x, cache. Ali D1
  prolazi oracle kroz Deklarant Pro svaki put (čita read-only, jeftino).
- **AI Oracle fallback** — Oracle je "stari parser", NE AI. AI Advisor
  odvojeno.
- **D2 import direktno contract u application/** — V3 DEP pravilo:
  application NE importuje contract. Adapter dostavlja ImportResult kao
  `dict[str, Any]` ili kao frozen dataclass koji NE potiče iz contract.

---

## Validation (per Definition of Done)

```text
[ ] CURRENT_STATE pročitan prije zadavanja  ✅ (M7 contract)
[ ] Task Contract napisan prije koda       ✅ (ovaj fajl)
[ ] implementer != reviewer                ⚠️ (Mavis oba; korisnik imenuje ako želi)
[ ] scope ostao u granicama Task Contracta (tokom implementacije provjeravam)
[ ] execution evidence prihvaćen          (pytest + ruff + git diff --stat na kraju)
[ ] architecture testovi PASS             (4/4)
[ ] ruff PASS                             (FAZA D scope)
[ ] pytest PASS                           (FAZA D scope + full regression)
[ ] contract drift provjeren              (D1 dodaje novu upotrebu contract/, ALI
                                           read-only; drift_check PASS jer contract
                                           vendor se NE mijenja)
[ ] CURRENT_STATE ažuriran                (FAZA D COMPLETE entry)
```

---

## Risk assessment

**LOW.**
- Sve komponente imaju jasan V3_2 §44 scope.
- D1 DTO (ImportResult) je vendorovana kopija — nema rizika od breaking change
  u Deklarant Pro.
- D2 mapping je statička mapa, ne dinamičan kod.
- D3 je čist Python use case, bez UI complexity.

**MEDIUM rizici:**
- Deklarant Pro `StrategyRegistry` može zahtijevati import dodatnih
  strategija (PDF, XML) koje zahtijevaju PDF/XML biblioteke koje možda
  nisu u venv-u. **Mitigacija:** D1 testovi koriste samo ExcelImportConfig
  + StrategyRegistry registration check; ne pozivaju import_file() u testu
  na .pdf/.xml.
- `import_file()` može baciti deklarant_pro specifične exceptions koje
  treba adapter da prevede u Parser Studio domenske greške. **Mitigacija:**
  try/except wrapper sa mapiranjem na `OracleError` hijerarhiju.

**HIGH:** nema.

---

## Commit i merge plan

```text
D1 commit:  arch(FAZA D/D1): DeklarantProOracle adapter
D2 commit:  arch(FAZA D/D2): Oracle → Candidate + EventType proširenje
D3 commit:  arch(FAZA D/D3): Oracle verification use cases
Merge:      merge(FAZA D): Oracle bootstrap — D1-D3 (V3_2 §44)
Evidence:   agent_reports/2026-09-14-M7-FazaD-evidence.md
CURRENT_STATE update + push origin/dev
Worktree cleanup
```

---

## Reference: tok iz V3_2 §23

```text
sample
 ├── postojeći vendor parser → ImportResult       ← D1
 └── Document Adapter → Evidence                   ← već M3/A3

ImportResult value
       ↓
PARSER_ORACLE Candidate                            ← D2
       ↓
povezivanje sa Evidence                            ← D2
       ↓
korisnička potvrda                                 ← D3
       ↓
USER_VERIFIED                                      ← D3 event
```

Stari parser NIJE automatski istina — D3 to garantuje.
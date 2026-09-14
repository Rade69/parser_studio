---
task_id: M5
title: "Gold Corpus — 4 sintetičke fakture sa 237 itema + USER_VERIFIED projection (V3 B5)"
status: ACTIVE
risk: MEDIUM
date: 2026-09-14
branch: task/m5-gold-corpus
worktree: H:/parser-studio-worktrees/m5-gold-corpus
base: dev @ 508d465
implementer: Mavis
---

# M5 — Prvi Gold Corpus (V3 B5)

> Potvrditi sve četiri pilot fakture. Acceptance: **237 itema + 20 ciljnih polja** imaju referentne Gold podatke/status.

**V3_2 B5 specifikacija:**
- Faktura-1: 11 stavki
- Faktura-2: 4 stavke
- Medicopharm: 84 stavke
- Sumaprom: 138 stavke
- UKUPNO: 237 stavki
- Svaka faktura: 9 invoice polja + 11 item polja = 20 ciljnih polja
- Svaki dokument mora imati USER_VERIFIED status za sva polja

---

## Canonical references

```text
docs/PLAN.md                  V3.2 §42 (FAZA B — Learning Foundation), §22 (Prvi Gold Dataset)
docs/GUI_BLUEPRINT.md         UI-04 Gold Dataset (coverage + history + rebuild projection)
.agent/CURRENT_STATE.md       Snapshot nakon UI0/GATE-0 LOCKED
V3_2 ARCH-003                 Gold Ground Truth je jedini stabilni autoritet (USER_VERIFIED)
V3_2 ARCH-010                 Stvarne fakture ne idu u Git (M5 koristi SINTETICKE)
V3 milestone:                 B5 (Prvi Gold corpus)
```

---

## Scope (IN)

### 1. Fixture generator (SINTETICKE fakture, ne stvarne)

```text
tests/fixtures/gold/__init__.py
tests/fixtures/gold/generator.py        # generators za 4 fakture
```

V3_2 ARCH-010 zabranjuje stvarne fakture u Git. Generator kreira **sintetičke** .xlsx fajlove u `tests/fixtures/gold/` sa poznatom strukturom:

```python
# Sintetičke fakture (NE stvarne poslovne podatke):
SYNTHETIC_FACTORIES = {
    "faktura-1": {"vendor": "FACT-A", "item_count": 11, "currency": "EUR"},
    "faktura-2": {"vendor": "FACT-B", "item_count": 4,  "currency": "EUR"},
    "medicopharm": {"vendor": "MED-1", "item_count": 84, "currency": "EUR"},
    "sumaprom":   {"vendor": "SUM-1", "item_count": 138, "currency": "EUR"},
}
```

Generator funkcija `generate_synthetic_factory(vendor_id, item_count, currency) -> Path`:
- Koristi openpyxl (vec u dependencies)
- Sheet "Header" sa 9 invoice polja
- Sheet "Items" sa N redova × 11 item polja
- Deterministički podaci (seed po vendor_id) za reproducible testove

### 2. Gold Corpus integration test

```text
tests/integration/__init__.py
tests/integration/test_gold_corpus.py
```

`pytest -q tests/integration/` pokreće:

1. `test_gold_corpus_imports_all_four_factories`: import svake od 4 fakture kroz `ImportDocument` + `AnalyzeInvoice` use case
2. `test_gold_corpus_verifies_all_invoice_fields`: za svaku fakturu, USER_VERIFIED kroz `ConfirmInvoice` za svih 9 invoice polja
3. `test_gold_corpus_verifies_all_item_fields`: za svaku fakturu, USER_VERIFIED za svaki item (11 polja × 237 itema = 2607 verifikacija)
4. `test_gold_dataset_projection_count`: GoldDataset projection sadrži 4 dokumenta
5. `test_gold_dataset_projection_items`: 237 stavki ukupno u projection
6. `test_learning_events_user_verified_count`: minimum 4 × 9 + 237 × 11 = 2643 USER_VERIFIED events

### 3. Test infrastructure

```text
tests/integration/conftest.py
```

Pytest fixtures:
- `temp_sqlite_db`: in-memory SQLite repo (vec koristimo u CLI testovima)
- `gold_factory_files`: tmp_path sa 4 generirane sintetičke fakture
- `gold_repo`: SQLiteLearningRepository sa temp DB

---

## Scope (OUT — ne radim u M5)

- ❌ UI-04 Gold Dataset ekran (post-M5, nakon GATE-3)
- ❌ Profile Builder UI integration (FAZA E)
- ❌ Apply Learning use case (FAZA C)
- ❌ VendorParserModel generation (FAZA H)
- ❌ Verifier (FAZA I)
- ❌ Export (FAZA J)
- ❌ Migracija stvarnih faktura (M5 koristi SINTETICKE zbog ARCH-010)
- ❌ AI Advisor integration (FAZA G)

---

## Disjunktni ownership (M5 je serijski, nema paralelnog rada)

M5 SMIJE kreirati/mijenjati:
- `tests/fixtures/gold/`
- `tests/integration/`
- `agent_reports/M5-task-contract.md`
- `agent_reports/2026-09-14-M5-evidence.md`

M5 NE SMIJE dodirivati (FAZA A0-A7, M1-M4 output):
- `src/parser_studio/**` (production code)
- `pyproject.toml`
- `.agent/CURRENT_STATE.md` (osim finalnog update-a)

---

## Acceptance criteria

```text
[ ] tests/fixtures/gold/__init__.py + generator.py kreirani
[ ] Generator kreira 4 sintetičke .xlsx fajla u tests/fixtures/gold/
[ ] Svaka faktura ima Sheet "Header" (9 polja) + Sheet "Items" (N redova × 11 polja)
[ ] tests/integration/__init__.py + conftest.py + test_gold_corpus.py kreirani
[ ] pytest tests/integration/test_gold_corpus.py — svi PASS (6 testova)
[ ] pytest cijeli suite — NEMA novih regression-a
[ ] ruff check tests/integration/ tests/fixtures/gold/ — All checks passed
[ ] architecture testovi i dalje PASS (M5 NE SMIJE break-ati V3 DEP-001..DEP-004)
[ ] GoldDataset projection sadrži 4 dokumenta
[ ] GoldDataset projection sadrži 237 itema ukupno
[ ] Minimum 2643 USER_VERIFIED events u learning_events tabeli
[ ] Svi testovi koriste SINTETICKE podatke (ne stvarne fakture)
[ ] Commit na task/m5-gold-corpus grani sa selektivnim git add
[ ] Push na origin/task/m5-gold-corpus
[ ] Evidence fajl sa stvarnim pytest izlazom + git diff --stat
```

---

## V3 architecture compliance

```text
tests/fixtures/gold/:
  - SAMO sintetički podaci (V3 ARCH-010)
  - NE sadrži stvarne fakture
  - NE commit-uje se u Git (samo generator skripte; output se kreira u tmp_path tokom testa)

tests/integration/test_gold_corpus.py:
  - NE importuje adapters direktno (kroz application layer)
  - Koristi ConfirmInvoice use case (kroz application/review/)
  - Koristi SQLiteLearningRepository (kroz adapter)
  - Koristi GoldDataset projection (vec implementiran u A6)
```

---

## Testiranje

```powershell
cd H:/parser-studio-worktrees/m5-gold-corpus

# 1. M5 testovi
python -m pytest tests/integration/test_gold_corpus.py -v

# 2. Cijeli suite
python -m pytest -q

# 3. Ruff
python -m ruff check tests/integration/ tests/fixtures/gold/

# 4. Architecture
python -m pytest tests/architecture/ -v
```

---

## Risk

**MEDIUM** — fixture generator mora proizvesti 237 itema tačno (acceptance kriterij). Deterministički seed osigurava reproducible testove.

Mitigacija:
- Seed po vendor_id u generatoru (deterministički)
- assert assert == 237 (strogi broj)
- assert == 4 dokumenta u projection
- assert >= 2643 USER_VERIFIED events

Ako M5 utvrdi da test runtime postane predugačak (>30s za 237 itema), fallback: koristiti batch insert za ConfirmInvoice.

---

## Definition of Done

```text
[ ] Fixture generator + 4 sintetičke fakture kreirane (runtime u tmp_path)
[ ] tests/integration/test_gold_corpus.py — 6 testova, svi PASS
[ ] pytest cijeli suite — bez novih regression-a
[ ] ruff clean za M5 fajlove
[ ] Commit na task/m5-gold-corpus sa selektivnim git add
[ ] Push na origin/task/m5-gold-corpus
[ ] Evidence fajl: agent_reports/2026-09-14-M5-evidence.md sa stvarnim pytest izlazom + git diff --stat
[ ] Merge u dev (Mavis radi kao koordinator)
[ ] CURRENT_STATE.md ažuriran sa M5 statusom DONE
```

---

**Status:** ACTIVE — Mavis implementira na `task/m5-gold-corpus` u `H:/parser-studio-worktrees/m5-gold-corpus`.
**Paralelan rad:** NEMA — M5 je serijski (zavisi od M1 CanonicalInvoice + M2 LayoutProfile).

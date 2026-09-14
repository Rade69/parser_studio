---
task_id: M3
title: "AI Advisor port + NullAdvisor + ConsultAdvisor use case (FAZA B / G1+G2)"
status: ACTIVE
risk: MEDIUM
date: 2026-09-14
branch: m3-ai-advisor
worktree: H:/parser_studio
---

# M3 — AI Advisor infrastructure (V3 G1 + G2)

> Uvesti `Advisor` port + `NullAdvisor` adapter + `ConsultAdvisor` use case.
> Provider implementacije (HttpVisionAdvisor, OpenAI, Anthropic) NISU u M3 scope-u — dolaze u G3+.

---

## Metadata

```text
task_id:        M3
title:          AI Advisor port + NullAdvisor + ConsultAdvisor use case
status:         ACTIVE
risk:           MEDIUM
date:           2026-09-14
branch:         m3-ai-advisor
worktree:       H:/parser_studio
parallel_with:  M1 (Pi agent) — disjunktni ownership, vidi § Disjunktni ownership
```

---

## Roles

```text
Human Owner:    Radovan (Rade69)
Coordinator:    Mavis (root sesija)
Implementer:    Mavis (ova sesija)
Reviewer:       Pi agent ili nezavisni reviewer (TBD naknadno)
```

**Implementer (Mavis) != Reviewer.** Recenzent će biti određen nakon implementacije.

---

## Canonical references

```text
docs/PLAN.md              V3 sekcija 29 (AI Advisor port) + sekcija 30 (Grounding gate) + sekcija 31 (AI cache)
.agent/CURRENT_STATE.md   Snapshot nakon A7 (commit b0c111e)
.agent/PROJECT_MAP.md     Sekcija C — MIGRATION MAP (FAZA B slotovi)
.agent/TASK_ROUTING.md    Kategorija: domain-port + adapter + use-case
V3 milestone:             G1 (Advisor port) + G2 (NullAdvisor)
```

---

## Scope (IN)

### 1. Port

```text
src/parser_studio/ports/advisor.py
```

`Advisor` Protocol:

```python
class Advisor(Protocol):
    mode: AdvisorMode  # off | cache-only | live

    def consult(
        self,
        *,
        field: str,
        candidates: tuple[Candidate, ...],
        context: ExtractionContext,
    ) -> tuple[AIAdvice, ...]: ...
```

- `AdvisorMode` enum: `OFF`, `CACHE_ONLY`, `LIVE`
- `AIAdvice` dataclass (u `ports/advisor.py`): `field`, `suggested_value`, `locator_evidence`, `confidence` (0.0..1.0), `reasoning` (kratko objašnjenje ili None)
- `Advisor` je `runtime_checkable`

### 2. NullAdvisor adapter

```text
src/parser_studio/adapters/ai/__init__.py
src/parser_studio/adapters/ai/null_advisor.py
```

`NullAdvisor` za `mode=off`:

- `consult(...)` uvijek vraća `()` (prazan tuple)
- Bez mrežnih poziva, bez LLM-a, bez import-a openai/anthropic
- Jedini dependency: `parser_studio.domain.evidence`, `parser_studio.ports.advisor`

### 3. Use case

```text
src/parser_studio/application/learning/__init__.py
src/parser_studio/application/learning/consult_advisor.py
```

`ConsultAdvisor` use case:

```python
class ConsultAdvisor:
    def __init__(self, advisor: Advisor) -> None: ...
    def execute(
        self,
        request: ConsultRequest,
    ) -> ConsultResult: ...
```

- `ConsultRequest`: `field: str`, `candidates: tuple[Candidate, ...]`, `context: ExtractionContext`
- `ConsultResult`: `field: str`, `advice: tuple[AIAdvice, ...]`, `mode: AdvisorMode`, `advisor_id: str` (za traceability)
- Use case NE SMIJE importovati `parser_studio.adapters.*` (samo `ports`)

### 4. Testovi

```text
tests/unit/ports/test_advisor.py                    (Protocol runtime_checkable, typing)
tests/unit/adapters/ai/test_null_advisor.py         (5-7 testova: mode=off, prazan output, nema mrežnih poziva)
tests/unit/application/learning/test_consult_advisor.py  (8-10 testova: use case wiring, kandidat ordering, error handling)
```

### 5. Wiring (bez bootstrap.py izmjene)

M3 NE SMIJE mijenjati `bootstrap.py`. Advisor se instancira eksplicitno u:

```text
# primjer korištenja (NE commitovati, samo u testovima):
advisor = NullAdvisor()  # mode=off po defaultu
consult_uc = ConsultAdvisor(advisor=advisor)
result = consult_uc.execute(ConsultRequest(field="kolicina", candidates=..., context=...))
```

---

## Scope (OUT — ne radim u M3)

- ❌ `HttpVisionAdvisor` (G3) — provider implementacija
- ❌ OpenAI / Anthropic / Google / DeepSeek adapteri
- ❌ AI cache (G5) — dolazi nakon G3
- ❌ Grounding gate enforcement (sekcija 30) — primjenjuje se u application layer (ConfirmInvoice), NE u M3
- ❌ Migracija `ConfirmInvoice` da koristi ConsultAdvisor
- ❌ Izmjene `bootstrap.py` (M3 ne smije dirati)
- ❌ Qt UI binding za AI advice display (FAZA B / M4)
- ❌ AI cache key schema (model_id, prompt_id, prompt_version, payload_sha256) — G5

---

## Disjunktni ownership (paralelan rad sa M1)

```text
M3 SMIJE kreirati/mijenjati:
  src/parser_studio/ports/advisor.py
  src/parser_studio/adapters/ai/__init__.py
  src/parser_studio/adapters/ai/null_advisor.py
  src/parser_studio/application/learning/__init__.py
  src/parser_studio/application/learning/consult_advisor.py
  tests/unit/ports/__init__.py
  tests/unit/ports/test_advisor.py
  tests/unit/adapters/__init__.py
  tests/unit/adapters/ai/__init__.py
  tests/unit/adapters/ai/test_null_advisor.py
  tests/unit/application/learning/__init__.py
  tests/unit/application/learning/test_consult_advisor.py
  agent_reports/M3-task-contract.md
  agent_reports/2026-09-14-M3-evidence.md

M3 NE SMIJE dodirivati (M1 ownership):
  src/parser_studio/domain/invoice/* (osim ako M3 NE kreira canonical_invoice — NE KREIRA)
  src/parser_studio/ports/parser_generator.py
  src/parser_studio/application/generation/*
  src/parser_studio/adapters/codegen/*
  bootstrap.py   (oba taska mogu extendati, ali koordinator rešava merge)
```

**Merge procedura za bootstrap.py:** Ako M1 extend-a `build_default_application` da doda `parser_generator`, a M3 NE SMIJE dodati `advisor` u bootstrap, merge je trivialan — `bootstrap.py` je linearno append. Koordiantor (Mavis) izvršava merge na kraju oba taska.

**Ako M3 tokom rada utvrdi da MORA izmijeniti `bootstrap.py`** (npr. za test fixture), to je signal da M3 scope raste — prijaviti koordinatoru prije izmjene.

---

## Acceptance criteria

```text
[ ] src/parser_studio/ports/advisor.py postoji, Advisor Protocol + AdvisorMode + AIAdvice
[ ] src/parser_studio/adapters/ai/null_advisor.py postoji, NullAdvisor klasa, mode=off
[ ] src/parser_studio/application/learning/consult_advisor.py postoji, ConsultAdvisor use case
[ ] pytest tests/unit/ports/ tests/unit/adapters/ai/ tests/unit/application/learning/ — svi PASS
[ ] pytest cijeli suite — NEMA novih regression-a (broj testova raste, ne pada)
[ ] ruff check src/parser_studio/ports/advisor.py src/parser_studio/adapters/ai/ src/parser_studio/application/learning/ — All checks passed
[ ] architecture testovi i dalje PASS (M3 ne smije break-ati V3 DEP-001..DEP-004)
[ ] domain/ NE importuje ports/advisor.py (Advisor ide application layer, ne domain)
[ ] NullAdvisor NE importuje openai/anthropic/httpx/bilo koji LLM library
[ ] import parser_studio.adapters.ai.null_advisor OK (bez KeyError, ImportError)
[ ] import parser_studio.application.learning.consult_advisor OK
```

---

## V3 architecture compliance

```text
domain:        NE SMIJE importovati ports/advisor (M3 NE dodiruje domain)
application:   SMIJE importovati ports (consult_advisor.py: from parser_studio.ports.advisor import Advisor)
ports:         NE SMIJE importovati adapters (advisor.py NE importuje NullAdvisor)
adapters:      SMIJE importovati domain + ports (null_advisor.py: from parser_studio.ports.advisor import Advisor, AIAdvice)
presentation:  NE SMIJE importovati direktno adapters/ai (kroz application/learning/consult_advisor)
```

Architecture test u `tests/architecture/test_import_boundaries.py` automatski provjerava — ne zahtijeva izmjenu.

---

## Testiranje

```text
# 1. Unit testovi
cd H:/parser_studio
python -m pytest tests/unit/ports/ tests/unit/adapters/ai/ tests/unit/application/learning/ -v

# 2. Regression check
python -m pytest -q --ignore=tests/integration

# 3. Ruff
python -m ruff check src/parser_studio/ports/advisor.py src/parser_studio/adapters/ai/ src/parser_studio/application/learning/

# 4. Architecture tests
python -m pytest tests/architecture/ -v
```

---

## Risk

**MEDIUM** — uvodimo novi cross-cutting port koji nije korišten ni u jednom postojećem use case-u.
Mitigacija:
- Advisor je opcioni dependency (ConfirmInvoice ga NE koristi u M3)
- NullAdvisor je zero-cost (nema mrežnih poziva, nema LLM)
- M3 NE SMIJE breakati ConfirmInvoice ponašanje (ConfirmInvoice ne ovisi o Advisor-u)

Ako ConsultAdvisor test padne na race condition ili circular import — odmah prijaviti.

---

## Definition of Done

```text
[ ] Kod u gore navedenim fajlovima napisan po acceptance kriterijima
[ ] Svi test PASS (acceptance + regression + architecture)
[ ] ruff clean za M3 fajlove
[ ] Commit na m3-ai-advisor grani sa selektivnim git add (NE git add --all)
[ ] Commit message u formatu: arch(M3): AI Advisor port + NullAdvisor + ConsultAdvisor use case
[ ] Push na origin/m3-ai-advisor
[ ] Evidence fajl: agent_reports/2026-09-14-M3-evidence.md sa stvarnim pytest izlazom i git diff --stat
[ ] CURRENT_STATE.md ažuriran sa M3 statusom (Mavis radi na kraju, koordinator)
```

---

## Napomene za M3 implementera (Mavis)

- Već imaš iskustva sa LLM providerima (vidi Agent Memory: AI Campaign Studio, fact-first content, provider-agnostic).
- NullAdvisor je trivijalan; fokus je na Protocol dizajnu (AdvisorMode enum + AIAdvice dataclass) i use case ergonomiji (ConsultRequest/ConsultResult).
- Ako M3 utvrdi da Consultant treba i `context` kao locator-aware objekt, koristiti `parser_studio.domain.evidence.ExtractionContext` (već postoji iz A2).
- `Locator` iz A2 (domain.evidence) koristi se u `AIAdvice.locator_evidence`.

---

**Status:** ACTIVE — Mavis implementira na `m3-ai-advisor` grani u `H:/parser_studio`.
**Parallel partner:** Pi agent na `m1-canonical-invoice` grani u `H:/parser_studio-m1`.

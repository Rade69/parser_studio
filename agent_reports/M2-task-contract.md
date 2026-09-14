---
task_id: M2
title: "LayoutFingerprint + LayoutProfile + BuildLayoutProfile use case (FAZA B / V3 E1+E2)"
status: ACTIVE
risk: MEDIUM
date: 2026-09-14
branch: task/m2-profile-builder
worktree: H:/parser_studio-m2
base: dev @ cc61f56 (HEAD nakon M1+M3 merge-a)
implementer: Mavis (root sesija)
---

# M2 — Profile Builder (V3 E1 + E2)

> Uvesti `LayoutFingerprint` (hash vrijednost layout detection pravila) + `LayoutProfile` (izvedeni artefakt sa pravilima extraction-a za jednog vendora) + `BuildLayoutProfile` use case (Gold primjeri → LayoutProfile).

**Mavis implementira u `H:/parser_studio-m2` (worktree), grana `task/m2-profile-builder`.**

---

## Canonical references

```text
docs/PLAN.md    V3 sekcija 45 (FAZA E — Layout Learning): E1 Fingerprint, E2 Profile Builder
                V3 sekcija ARCH-004 (Layout Profile je izvedeni artefakt, NE source-of-truth)
.agent/CURRENT_STATE.md   Snapshot nakon M1+M3 merge (commit cc61f56)
.agent/PROJECT_MAP.md     Sekcija C — MIGRATION MAP
.agent/TASK_ROUTING.md    Kategorija: domain-deepening + derived-artifact
V3 milestone:             E1 (Fingerprint) + E2 (Profile Builder)
```

---

## Scope (IN)

### 1. LayoutFingerprint (domain)

```text
src/parser_studio/domain/profiles/__init__.py
src/parser_studio/domain/profiles/layout_fingerprint.py
```

`LayoutFingerprint` je hash vrijednost layout detection pravila jednog dokumenta.

```python
@dataclass(frozen=True, slots=True)
class LayoutFingerprint:
    """Hash vrijednost layout detection pravila. Immutable."""
    hash: str  # 64-char SHA-256 hex
    components: tuple[FingerprintComponent, ...]

    def __post_init__(self) -> None:
        if not self.hash or len(self.hash) != 64:
            raise ValueError("hash mora biti 64-char SHA-256 hex")
        if not all(isinstance(c, FingerprintComponent) for c in self.components):
            raise TypeError("components moraju biti FingerprintComponent instances")

@dataclass(frozen=True, slots=True)
class FingerprintComponent:
    """Jedna komponenta fingerprint-a (npr. header_row_count, column_signature, ...)."""
    name: str  # npr. "header_row_count"
    value: str  # normalizirana vrijednost

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name ne moze biti prazan")
        if not self.value:
            raise ValueError("value ne moze biti prazan")
```

Algoritam za računanje hash-a:
- Sortiraj `components` po `name` (deterministički)
- Konkateniraj `name:value|name:value|...`
- SHA-256 hex digest

### 2. LayoutProfile (domain)

```text
src/parser_studio/domain/profiles/layout_profile.py
```

`LayoutProfile` je izvedeni artefakt (po V3 ARCH-004) — NE source-of-truth.

```python
@dataclass(frozen=True, slots=True)
class LayoutProfile:
    """Izvedeni profil iz Gold primjera. Versiran, deletable, re-buildable."""
    vendor_id: str  # npr. "faktura-1"
    version: int  # 1, 2, 3, ... (bumped on drift)
    fingerprint: LayoutFingerprint
    rules: tuple[ProfileRule, ...]
    source_documents: tuple[str, ...]  # paths to gold documents
    built_at: datetime
    sample_count: int  # koliko gold primjera je koristeno

@dataclass(frozen=True, slots=True)
class ProfileRule:
    """Jedno pravilo u profilu (npr. header_row=1, total_cell_pattern=RXX)."""
    rule_type: str  # npr. "header_row", "column_match", "fallback"
    parameters: tuple[RuleParameter, ...]  # key=value parovi

@dataclass(frozen=True, slots=True)
class RuleParameter:
    key: str
    value: str
```

### 3. ProfileRepository port

```text
src/parser_studio/ports/profile_repository.py
```

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class ProfileRepository(Protocol):
    """Port za čuvanje LayoutProfile-a."""

    def save(self, profile: LayoutProfile) -> None: ...
    def find(self, vendor_id: str, version: int | None = None) -> LayoutProfile | None: ...
    def list_versions(self, vendor_id: str) -> tuple[int, ...]: ...
    def delete(self, vendor_id: str, version: int) -> None: ...
```

`find` bez `version` vraća najnoviju verziju.

### 4. InMemoryProfileRepository (adapter)

```text
src/parser_studio/adapters/profiles/__init__.py
src/parser_studio/adapters/profiles/in_memory_repository.py
```

In-memory implementacija za testiranje (kasnije FAZA E dodaje SQLite).

### 5. BuildLayoutProfile use case

```text
src/parser_studio/application/profiles/__init__.py
src/parser_studio/application/profiles/build_layout_profile.py
```

```python
@dataclass(frozen=True, slots=True)
class BuildRequest:
    vendor_id: str
    gold_samples: tuple[GoldSample, ...]  # input
    repo: ProfileRepository  # output destination

@dataclass(frozen=True, slots=True)
class GoldSample:
    """Jedan gold primjer (source path + extracted LayoutFingerprint)."""
    source_path: str
    fingerprint: LayoutFingerprint
    sample_metadata: tuple[RuleParameter, ...] = ()  # npr. invoice_count=10

@dataclass(frozen=True, slots=True)
class BuildResult:
    profile: LayoutProfile
    warnings: tuple[str, ...]  # npr. "samples have different fingerprints, version bumped"

class BuildLayoutProfile:
    """Use case: gold primjeri → LayoutProfile."""

    def execute(self, request: BuildRequest) -> BuildResult: ...
```

Algoritam:
1. Ažuriraj `repo.list_versions(vendor_id)` — ako postoji profil za vendor_id, inkrementiraj version
2. Izračunaj zajedničke `ProfileRule`-ove iz svih `gold_samples`
3. Ako se fingerprints razlikuju među samples → bump version, dodaj warning
4. Kreiraj `LayoutProfile` sa pravilima
5. `repo.save(profile)`
6. Vrati `BuildResult`

### 6. Testovi

```text
tests/unit/domain/profiles/test_layout_fingerprint.py       (8-10 testova: hash determinizam, validacija, komponente)
tests/unit/domain/profiles/test_layout_profile.py          (6-8 testova: vendor_id, version, rules, source_documents)
tests/unit/ports/test_profile_repository.py                (5-7 testova: Protocol runtime_checkable)
tests/unit/adapters/profiles/test_in_memory_repository.py  (8-10 testova: save/find/list_versions/delete)
tests/unit/application/profiles/test_build_layout_profile.py  (10-15 testova: zlatni put, drift, version bump, warnings)
```

---

## Scope (OUT — ne radim u M2)

- ❌ E3 Profile Matcher (HIGH/REVIEW/NO_MATCH) — zaseban milestone
- ❌ E4 Drift detection automatika — samo ručno version bumping kroz use case
- ❌ E5 Holdout dokaz
- ❌ SQLiteProfileRepository — samo InMemory za sada (FAZA E kasnije)
- ❌ Profile Builder UI (M4 + Qt)
- ❌ Integracija sa ConfirmInvoice use case-om
- ❌ AI Advisor (ConsultAdvisor) integracija za profile suggestion
- ❌ Migracija starih gold podataka

---

## Disjunktni ownership (paralelan rad sa M4)

```text
M2 SMIJE kreirati/mijenjati:
  src/parser_studio/domain/profiles/__init__.py
  src/parser_studio/domain/profiles/layout_fingerprint.py
  src/parser_studio/domain/profiles/layout_profile.py
  src/parser_studio/ports/profile_repository.py
  src/parser_studio/adapters/profiles/__init__.py
  src/parser_studio/adapters/profiles/in_memory_repository.py
  src/parser_studio/application/profiles/__init__.py
  src/parser_studio/application/profiles/build_layout_profile.py
  tests/unit/domain/profiles/__init__.py
  tests/unit/domain/profiles/test_layout_fingerprint.py
  tests/unit/domain/profiles/test_layout_profile.py
  tests/unit/ports/test_profile_repository.py
  tests/unit/adapters/__init__.py                  (oprez: mozda vec postoji)
  tests/unit/adapters/profiles/__init__.py
  tests/unit/adapters/profiles/test_in_memory_repository.py
  tests/unit/application/__init__.py               (oprez: mozda vec postoji)
  tests/unit/application/profiles/__init__.py
  tests/unit/application/profiles/test_build_layout_profile.py
  agent_reports/M2-task-contract.md
  agent_reports/2026-09-14-M2-evidence.md

M2 NE SMIJE dodirivati (M4 ownership):
  src/parser_studio/presentation/qt/widgets/*
  tests/unit/presentation/qt/widgets/*

M2 NE SMIJE dodirivati (M3 ownership):
  src/parser_studio/ports/advisor.py
  src/parser_studio/adapters/ai/
  src/parser_studio/application/learning/

M2 NE SMIJE dodirivati (M1 ownership):
  src/parser_studio/domain/invoice/*
```

**Merge procedura:** M2 je append-only u `domain/profiles/`, `ports/`, `adapters/profiles/`, `application/profiles/`. M4 je append-only u `presentation/qt/widgets/`. Trivijalan rebase + merge.

---

## Acceptance criteria

```text
[ ] src/parser_studio/domain/profiles/layout_fingerprint.py — LayoutFingerprint + FingerprintComponent
[ ] src/parser_studio/domain/profiles/layout_profile.py — LayoutProfile + ProfileRule + RuleParameter
[ ] src/parser_studio/ports/profile_repository.py — ProfileRepository Protocol (runtime_checkable)
[ ] src/parser_studio/adapters/profiles/in_memory_repository.py — InMemoryProfileRepository
[ ] src/parser_studio/application/profiles/build_layout_profile.py — BuildLayoutProfile + BuildRequest + BuildResult + GoldSample
[ ] pytest tests/unit/domain/profiles/ tests/unit/ports/test_profile_repository.py tests/unit/adapters/profiles/ tests/unit/application/profiles/ — svi PASS (40-50 testova ukupno)
[ ] pytest cijeli suite — NEMA novih regression-a (test count raste)
[ ] ruff check src/parser_studio/domain/profiles/ src/parser_studio/ports/profile_repository.py src/parser_studio/adapters/profiles/ src/parser_studio/application/profiles/ tests/unit/domain/profiles/ tests/unit/adapters/profiles/ tests/unit/application/profiles/ — All checks passed
[ ] architecture testovi i dalje PASS (V3 DEP-001 — domain NE importuje sqlite3/openpyxl/xlrd/docling/adapters/presentation/contract)
[ ] BuildLayoutProfile.use_case NE importuje adapters (kroz port)
[ ] import parser_studio.domain.profiles.layout_fingerprint — OK
[ ] import parser_studio.application.profiles.build_layout_profile — OK
[ ] InMemoryProfileRepository NEMA sqlite3 dependency
[ ] Commit na task/m2-profile-builder grani sa selektivnim git add
[ ] Push na origin/task/m2-profile-builder
[ ] Evidence fajl sa stvarnim pytest izlazom i git diff --stat
```

---

## V3 architecture compliance

```text
domain/profiles/layout_fingerprint.py:
  - frozen=True, slots=True
  - SHA-256 hash deterministicki (isti input = isti output)
  - components sortirani po name prije hash-a

domain/profiles/layout_profile.py:
  - frozen=True, slots=True
  - version: int (1-based)
  - built_at: datetime (immutable)
  - source_documents: tuple[str, ...] (paths)

ports/profile_repository.py:
  - runtime_checkable Protocol
  - find(vendor_id, version=None) — None = latest
  - list_versions(vendor_id) — sorted ascending

adapters/profiles/in_memory_repository.py:
  - NE importuje sqlite3
  - dict-based storage
  - thread-safe NIJE obaveza za M2

application/profiles/build_layout_profile.py:
  - prima ProfileRepository kroz request.repo (NE kroz konstruktor)
  - BuildRequest je frozen
  - execute(request) -> BuildResult
  - Ako gold_samples imaju različite fingerprints: bump version, warning
  - Spremi profil prije vraca BuildResult
```

---

## Testiranje

```powershell
cd H:/parser_studio-m2

# 1. M2 testovi
python -m pytest tests/unit/domain/profiles/ tests/unit/ports/test_profile_repository.py tests/unit/adapters/profiles/ tests/unit/application/profiles/ -v

# 2. Regression
python -m pytest -q --ignore=tests/integration

# 3. Ruff
python -m ruff check src/parser_studio/domain/profiles/ src/parser_studio/ports/profile_repository.py src/parser_studio/adapters/profiles/ src/parser_studio/application/profiles/ tests/unit/domain/profiles/ tests/unit/adapters/profiles/ tests/unit/application/profiles/

# 4. Architecture
python -m pytest tests/architecture/ -v
```

---

## Risk

**MEDIUM** — uvodimo derived artifact (V3 ARCH-004) koji se može rebuild-ati iz Gold-a. Greška u algoritmu za zajednička pravila može proizvesti nekvalitetan profil.

Mitigacija:
- Test sa 3+ različitih Gold primjera (deterministički hash)
- Warning za fingerprint mismatch (NE fail)
- `InMemoryProfileRepository` (NE sqlite3) — lako se mijenja
- Profil je DELTABLE i re-buildable (V3 ARCH-004 constraint)

Ako M2 utvrdi da je algoritam za `ProfileRule` extraction previše complex za jedan task — smanji scope: vrati samo `LayoutFingerprint` + `LayoutProfile` (data klase) + `ProfileRepository` (port + InMemory), bez `BuildLayoutProfile` use case-a. To je fallback M2-minimum.

---

## Definition of Done

```text
[ ] Kod u gore navedenim fajlovima napisan po acceptance kriterijima
[ ] Svi test PASS (acceptance + regression + architecture)
[ ] ruff clean za M2 fajlove
[ ] Commit na task/m2-profile-builder sa selektivnim git add (NE git add --all)
[ ] Commit message: arch(M2): LayoutFingerprint + LayoutProfile + BuildLayoutProfile use case (V3 E1+E2)
[ ] Push na origin/task/m2-profile-builder
[ ] Evidence fajl: agent_reports/2026-09-14-M2-evidence.md sa stvarnim pytest izlazom + git diff --stat
[ ] NE SMIJE dirati M4 fajlove (provjeriti sa git diff --stat dev..HEAD)
[ ] NE SMIJE dirati M3/M1 fajlove
```

---

**Status:** ACTIVE — Mavis implementira na `task/m2-profile-builder` u `H:/parser_studio-m2`.
**Parallel partner:** Pi agent na `task/m4-review-gui` u `H:/parser_studio-m4` (korisnik pokreće).

---
task_id: A6
title: "LearningRepository port + SQLite adapter + Gold Dataset projection"
status: ACTIVE
risk: MEDIUM
date: 2026-09-14
branch: dev (base)
worktree: TBD
---

# A6 — LearningRepository + SQLite adapter + Gold Dataset projection

> Implementirati `LearningRepository` Protocol (A5 deklarisan) sa SQLite adapterom, append-only `learning_events` tabelom, i Gold Dataset projection tabelom. Domain NE importuje `sqlite3` (po V3 DEP-001).

---

## Roles

```text
Human Owner:    <tvoj unos>
Coordinator:    Claude Code
Implementer:    <tvoj unos>
Reviewer:       <tvoj unos — nezavisni>
```

---

## Canonical references

```text
docs/PLAN.md                                  (V3, sekcija 13: Learning arhitektura; sekcija 14: SQLite adapter; sekcija 41: A6; sekcija 42: B1-B4 FAZA B)
.agent/PROJECT_MAP.md                         (sekcija B: adapters/persistence/sqlite; sekcija C: MIGRATION MAP)
.agent/TASK_ROUTING.md                        (sekcija "Learning / SQLite")
src/parser_studio/domain/learning/             (A5: LearningEvent + EventType)
src/parser_studio/application/review/confirm_invoice.py  (A5: LearningRepository Protocol)
agent_reports/2026-09-14-graft-evaluation.md  (Graft SECONDARY pravila)
```

---

## Current-state preconditions

```text
[ ] branch: dev na b3f16cd (A5 docs)
[ ] A5 acceptance DONE — LearningEvent, EventType, LearningRepository Protocol
[ ] Graft status: SECONDARY (probacioni period)
[ ] baseline testovi: 310 PASS + 1 FAIL (test_f9 pre-existing)
[ ] ruff: 172 errors
[ ] contract drift: PASS
[ ] DEKLARANT_PRO_ROOT: H:/deklarant_pro
```

A6 može krenuti.

---

## Problem

V3 sekcija 13 specificira:

```python
class LearningRepository(Protocol):
    def append(self, event: LearningEvent) -> None:
        ...

    def events_for(
        self, document_id: str, field: str | None = None
    ) -> list[LearningEvent]:
        ...

    def events_since(
        self, since: datetime, field: str | None = None
    ) -> list[LearningEvent]:
        ...
```

V3 sekcija 14 specificira SQLite adapter:
- `sqlite3` je adapter iza LearningRepository porta
- Domain NE smije importovati `sqlite3`
- Append-only `learning_events` tabela
- Projection tabele za Gold Dataset, profiles, itd.

Trenutno stanje:
- `LearningRepository` Protocol DEKLARISAN u `src/parser_studio/application/review/confirm_invoice.py` (samo `append`)
- NEMA SQLite adaptera
- NEMA append-only tabele
- NEMA projection logike
- `learning_repo=None` u `bootstrap.build_default_application()`

---

## Goal

1. Proširiti `LearningRepository` Protocol sa `events_for()` i `events_since()` metodama
2. Implementirati `SQLiteLearningRepository` (in-memory i file-based)
3. Kreirati SQLite migration skripte (learning_events + gold_dataset projection)
4. Kreirati `GoldDataset` projection view/tabelu
5. Wire u `bootstrap.py`
6. Unit testovi za sve

Acceptance:
- 2 nove metode u Protocolu (events_for, events_since)
- SQLiteLearningRepository (in-memory + file-based)
- 2+ migracije (learning_events + gold_dataset)
- `build_default_application()` sa SQLite repo
- 8+ unit testova
- pytest NE SMIJE imati više od 1 FAIL
- ruff NE SMIJE imati značajno više grešaka
- contract drift PASS
- Legacy `core/` netaknut
- NEMA stvarnih poslovnih podataka u test fixture-ima (samo sintetički)

---

## In scope

### Novi fajlovi

```text
src/parser_studio/adapters/persistence/
    __init__.py
    sqlite/
        __init__.py
        connection.py          # SQLite connection helper + pragmas
        migrations/
            __init__.py
            001_learning_events.py    # CREATE TABLE learning_events
            002_gold_dataset.py       # CREATE TABLE gold_dataset_projection + VIEW
        learning_repository.py  # SQLiteLearningRepository implementacija
        gold_dataset.py         # GoldDataset projection

src/parser_studio/adapters/persistence/migrations/runner.py  # migracijski runner

tests/unit/adapters/persistence/
    __init__.py
    sqlite/
        __init__.py
        test_learning_repository.py
        test_gold_dataset.py
        test_migrations.py
```

Izmjene:
- `src/parser_studio/application/review/confirm_invoice.py` — proširiti `LearningRepository` Protocol sa `events_for` i `events_since`
- `src/parser_studio/bootstrap.py` — `build_default_application` kreira SQLite repo (file-based, putanja iz env ili default `~/.parser_studio/learning.db`)

### LearningRepository Protocol proširenje

```python
# u src/parser_studio/application/review/confirm_invoice.py (nadogradnja)
from datetime import datetime

class LearningRepository(Protocol):
    def append(self, event: LearningEvent) -> None: ...
    def events_for(
        self, document_id: str, field: str | None = None
    ) -> list[LearningEvent]: ...
    def events_since(
        self, since: datetime, field: str | None = None
    ) -> list[LearningEvent]: ...
```

### SQLite schema (V3 spec)

```sql
-- migration 001: learning_events (append-only)
CREATE TABLE IF NOT EXISTS learning_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL,
    item_id TEXT,
    field_name TEXT NOT NULL,
    event_type TEXT NOT NULL,
    old_value TEXT,           -- JSON-serialized
    new_value TEXT,           -- JSON-serialized
    locator_json TEXT,        -- JSON-serialized Locator ili None
    source TEXT NOT NULL,
    note TEXT,
    created_at TEXT NOT NULL, -- ISO 8601 UTC
    schema_version INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_learning_events_document_id
    ON learning_events(document_id);
CREATE INDEX IF NOT EXISTS idx_learning_events_field_name
    ON learning_events(field_name);
CREATE INDEX IF NOT EXISTS idx_learning_events_created_at
    ON learning_events(created_at);

-- migration 002: gold_dataset_projection (VIEW)
CREATE VIEW IF NOT EXISTS gold_dataset_projection AS
SELECT
    document_id,
    item_id,
    field_name,
    new_value AS confirmed_value,
    COUNT(*) FILTER (WHERE event_type = 'USER_CONFIRMED') AS confirm_count,
    MAX(created_at) AS last_confirmed_at
FROM learning_events
WHERE event_type IN ('USER_CONFIRMED', 'USER_VERIFIED')
GROUP BY document_id, item_id, field_name;
```

### SQLiteLearningRepository specifikacija

```python
# src/parser_studio/adapters/persistence/sqlite/learning_repository.py
from __future__ import annotations
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from parser_studio.adapters.persistence.sqlite.connection import open_connection
from parser_studio.domain.learning.learning_event import EventType, LearningEvent
from parser_studio.domain.evidence.locator import Locator


def _serialize_locator(locator: Locator | None) -> str | None:
    if locator is None:
        return None
    return json.dumps({
        "source_path": locator.source_path,
        "kind": locator.kind,
        "page": locator.page,
        "bbox": locator.bbox,
        "sheet": locator.sheet,
        "row": locator.row,
        "col": locator.col,
        "char_span": locator.char_span,
    })


def _deserialize_locator(data: str | None) -> Locator | None:
    if data is None:
        return None
    d = json.loads(data)
    return Locator(
        source_path=d["source_path"],
        kind=d["kind"],
        page=d.get("page"),
        bbox=d.get("bbox"),
        sheet=d.get("sheet"),
        row=d.get("row"),
        col=d.get("col"),
        char_span=d.get("char_span"),
    )


def _serialize_value(value: object) -> str:
    if value is None:
        return None
    return json.dumps(value, default=str)


def _deserialize_value(data: str | None) -> object:
    if data is None:
        return None
    return json.loads(data)


class SQLiteLearningRepository:
    """SQLite implementacija LearningRepository porta.
    Append-only 'learning_events' tabela + Gold Dataset projection."""

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = str(db_path)
        self._conn = open_connection(self._db_path)

    def append(self, event: LearningEvent) -> None:
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO learning_events (
                    document_id, item_id, field_name, event_type,
                    old_value, new_value, locator_json, source, note,
                    created_at, schema_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    event.document_id,
                    event.item_id,
                    event.field_name,
                    event.event_type.value,
                    _serialize_value(event.old_value),
                    _serialize_value(event.new_value),
                    _serialize_locator(event.locator),
                    event.source,
                    event.note,
                    event.created_at.isoformat(),
                ),
            )

    def events_for(
        self, document_id: str, field: str | None = None
    ) -> list[LearningEvent]:
        if field is None:
            rows = self._conn.execute(
                """
                SELECT id, document_id, item_id, field_name, event_type,
                       old_value, new_value, locator_json, source, note, created_at
                FROM learning_events
                WHERE document_id = ?
                ORDER BY created_at, id
                """,
                (document_id,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT id, document_id, item_id, field_name, event_type,
                       old_value, new_value, locator_json, source, note, created_at
                FROM learning_events
                WHERE document_id = ? AND field_name = ?
                ORDER BY created_at, id
                """,
                (document_id, field),
            ).fetchall()
        return [_row_to_event(row) for row in rows]

    def events_since(
        self, since: datetime, field: str | None = None
    ) -> list[LearningEvent]:
        since_iso = since.isoformat()
        if field is None:
            rows = self._conn.execute(
                """
                SELECT id, document_id, item_id, field_name, event_type,
                       old_value, new_value, locator_json, source, note, created_at
                FROM learning_events
                WHERE created_at >= ?
                ORDER BY created_at, id
                """,
                (since_iso,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT id, document_id, item_id, field_name, event_type,
                       old_value, new_value, locator_json, source, note, created_at
                WHERE created_at >= ? AND field_name = ?
                ORDER BY created_at, id
                """,
                (since_iso, field),
            ).fetchall()
        return [_row_to_event(row) for row in rows]

    def close(self) -> None:
        self._conn.close()


def _row_to_event(row: sqlite3.Row) -> LearningEvent:
    return LearningEvent(
        document_id=row["document_id"],
        field_name=row["field_name"],
        event_type=EventType(row["event_type"]),
        new_value=_deserialize_value(row["new_value"]),
        locator=_deserialize_locator(row["locator_json"]),
        source=row["source"],
        item_id=row["item_id"],
        old_value=_deserialize_value(row["old_value"]),
        note=row["note"] or "",
        created_at=datetime.fromisoformat(row["created_at"]),
    )
```

### Connection helper

```python
# src/parser_studio/adapters/persistence/sqlite/connection.py
from __future__ import annotations
import sqlite3
from pathlib import Path


def open_connection(db_path: str | Path) -> sqlite3.Connection:
    """Otvori SQLite konekciju sa parser_studio pragmas."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn
```

### Migration runner

```python
# src/parser_studio/adapters/persistence/migrations/runner.py
from __future__ import annotations
import sqlite3
from importlib import resources


def run_migrations(conn: sqlite3.Connection) -> None:
    """Pokreni sve SQL migracije iz migrations/ paketa.
    Za MVP: pokrece ih sve po redu. Za budućnost: schema_migrations tabela
    za pracenje verzije."""
    migrations = [
        "001_learning_events",
        "002_gold_dataset",
    ]
    for name in migrations:
        sql_file = resources.files("parser_studio.adapters.persistence.sqlite.migrations").joinpath(f"{name}.sql")
        sql = sql_file.read_text(encoding="utf-8")
        conn.executescript(sql)
        conn.commit()
```

### bootstrap.py izmjene

```python
# Nadogradnja
import os
from pathlib import Path

from parser_studio.adapters.persistence.sqlite.learning_repository import (
    SQLiteLearningRepository,
)


def build_default_application(
    db_path: str | Path | None = None,
) -> tuple[
    ImportDocument, AnalyzeInvoice, ConfirmInvoice, SQLiteLearningRepository
]:
    """Kreiraj default aplikaciju sa SQLite LearningRepository."""
    if db_path is None:
        env_path = os.environ.get("PARSER_STUDIO_DB")
        if env_path:
            db_path = env_path
        else:
            home = Path.home()
            db_path = home / ".parser_studio" / "learning.db"

    # Provjeri da direktorij postoji
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    excel_reader = ExcelDocumentReader()
    import_doc = ImportDocument(readers=(excel_reader,))

    excel_header_producer = ExcelHeaderProducer()
    analyze = AnalyzeInvoice(producers=(excel_header_producer,))

    repo = SQLiteLearningRepository(db_path=db_path)
    confirm = ConfirmInvoice(learning_repo=repo)

    return import_doc, analyze, confirm, repo
```

### Unit testovi

```text
tests/unit/adapters/persistence/sqlite/test_learning_repository.py
  - konstrukcija (in-memory + file-based)
  - append jednog eventa
  - append vise evenata
  - events_for za dokument
  - events_for za dokument + field
  - events_since sa filterom po polju
  - close()
  - round-trip LearningEvent -> SQLite -> LearningEvent (sa Locator)

tests/unit/adapters/persistence/sqlite/test_gold_dataset.py
  - VIEW vraca USER_CONFIRMED događaje
  - query po document_id
  - query po field
  - confirm_count aggregation

tests/unit/adapters/persistence/sqlite/test_migrations.py
  - run_migrations kreira tabele
  - run_migrations je idempotent (CREATE IF NOT EXISTS)
  - indeksi postoje
```

---

## Out of scope

```text
- Profile builder (BuildLayout*, MatchLayout*) — FAZA E
- Gold Dataset corpus (stvarni fakture) — B5 posao
- OCR recovery (RecoverFieldOCR) — FAZA F
- AI Advisor (FAZA G)
- Codegen, Verifier (FAZA H/I)
- CLI export (FAZA J)
- Review GUI (FAZA B / M4)
- Migracija legacy core/ u novu strukturu (A7 cleanup)
- Architecture test (opcioni; moze u A7)
- Fix test_f9_no_broken_rows regression (benchmark cleanup)
- Cleanup 172+ ruff gresaka
- Uklanjanje cryptography iz pyproject.toml
- Async/concurrent access (za MVP, single-process)
- Migrations versioning (schema_migrations tabela) — za buduću verziju
```

---

## Expected files

```text
Novi:
- src/parser_studio/adapters/persistence/__init__.py
- src/parser_studio/adapters/persistence/sqlite/__init__.py
- src/parser_studio/adapters/persistence/sqlite/connection.py
- src/parser_studio/adapters/persistence/sqlite/migrations/__init__.py
- src/parser_studio/adapters/persistence/sqlite/migrations/001_learning_events.sql
- src/parser_studio/adapters/persistence/sqlite/migrations/002_gold_dataset.sql
- src/parser_studio/adapters/persistence/sqlite/learning_repository.py
- src/parser_studio/adapters/persistence/migrations/runner.py
- src/parser_studio/adapters/persistence/sqlite/gold_dataset.py
- tests/unit/adapters/__init__.py
- tests/unit/adapters/persistence/__init__.py
- tests/unit/adapters/persistence/sqlite/__init__.py
- tests/unit/adapters/persistence/sqlite/test_learning_repository.py
- tests/unit/adapters/persistence/sqlite/test_gold_dataset.py
- tests/unit/adapters/persistence/sqlite/test_migrations.py

Izmijenjeni:
- src/parser_studio/application/review/confirm_invoice.py
  (LearningRepository Protocol proširen sa events_for, events_since)
- src/parser_studio/bootstrap.py
  (build_default_application sada kreira SQLite repo)

Obrisani:        nijedan
Premješteni:    nijedan
```

---

## Architecture boundaries

A6 NE SMIJE probiti:

```text
[ ] domain/learning/ → sqlite3 (domain NE importuje sqlite3; adapter ga apstrahuje)
[ ] application/review/ → sqlite3 direktno (samo preko porta)
[ ] application/ → adapters/persistence (samo preko porta)
[ ] ports/learning_repository → sqlite3
```

**Dozvoljeno:**
- `adapters/persistence/sqlite/` importuje `sqlite3` (konkretna tehnologija)
- `adapters/persistence/sqlite/learning_repository.py` importuje `parser_studio.domain.learning.LearningEvent`
- `adapters/persistence/sqlite/migrations/` SQL fajlovi — čitaju se kao text resursi
- `application/review/confirm_invoice.py` (Protocol) NE importuje sqlite3

---

## Compatibility requirements

```text
[ ] Svi postojeći testovi i dalje rade (310 PASS + 1 FAIL = test_f9 pre-existing)
[ ] Svi legacy importi iz core/ i dalje rade
[ ] NEMA promjene legacy koda (core/, cli/, services/, views/, viewmodels/)
[ ] NEMA promjene legacy testova
[ ] NEMA parallel "core/" + "src/" business koda
[ ] LearningRepository Protocol proširen, ali ConfirmInvoice API ostaje isti (backward compatible)
[ ] Svi SQLite testovi koriste in-memory ili privremeni file, NE diraju ~/.parser_studio/learning.db
[ ] NEMA stvarnih poslovnih podataka u SQLite test fixture-ima (samo sintetički)
```

---

## Acceptance criteria

```text
[ ] LearningRepository Protocol proširen (events_for, events_since)
[ ] SQLiteLearningRepository implementacija
[ ] 2+ migracije (001_learning_events.sql, 002_gold_dataset.sql)
[ ] Gold Dataset projection VIEW
[ ] Connection helper sa pragmas (foreign_keys=ON, journal_mode=WAL)
[ ] Migration runner (idempotent)
[ ] bootstrap.py sa SQLite repo (file-based sa default path)
[ ] 8+ unit testova
[ ] pytest ista ili bolja statistika (max 1 FAIL = test_f9 pre-existing)
[ ] ruff ne značajno gore od baseline (172)
[ ] contract drift PASS
[ ] python -c "from parser_studio.adapters.persistence.sqlite.learning_repository import SQLiteLearningRepository" OK
[ ] python -c "from parser_studio.bootstrap import build_default_application" OK
[ ] Graft blast: nema false "impacted dependents"
[ ] CURRENT_STATE A6 status DONE
[ ] Commit + push na dev
```

---

## Required tests

```text
Unit (novi):
- tests/unit/adapters/persistence/sqlite/test_learning_repository.py
  - SQLiteLearningRepository(":memory:") kreira tabele
  - append jednog eventa
  - append vise evenata (redoslijed po created_at)
  - events_for(document_id) vraca samo eventa tog dokumenta
  - events_for(document_id, field) filterira po polju
  - events_since(since) filtrira po datumu
  - events_since(since, field) kombinira oba filtera
  - Locator round-trip (serialize/deserialize)
  - close() zatvara konekciju
  - file-based repo kreira fajl na disku

- tests/unit/adapters/persistence/sqlite/test_gold_dataset.py
  - VIEW vraca USER_CONFIRMED događaje agregirane
  - query po document_id
  - confirm_count aggregation

- tests/unit/adapters/persistence/sqlite/test_migrations.py
  - run_migrations kreira obje tabele
  - run_migrations je idempotent (poziv 2x ne baca gresku)
  - indeksi na learning_events(document_id, field_name, created_at) postoje

Unit (postojeći):
- svi ostali testovi i dalje PASS

Integration:    nijedan u A6 (za buduću verziju)
Architecture:   opcioni (database testovi)
```

---

## Impact analysis required (Graft SECONDARY period)

```text
[Da] MEDIUM risk

Simboli za praćenje (NOVI):
- parser_studio.adapters.persistence.sqlite.learning_repository.SQLiteLearningRepository
- parser_studio.adapters.persistence.sqlite.connection.open_connection
- parser_studio.adapters.persistence.migrations.runner.run_migrations

Simboli za proširenje (IZMJENA):
- parser_studio.application.review.confirm_invoice.LearningRepository (Protocol)
- parser_studio.bootstrap.build_default_application

Alati:
- graft build                 # reindeksiranje
- graft grep "SQLiteLearningRepository"
- graft grep "open_connection"
- graft blast                 # diff working tree vs HEAD
- ručni grep fallback
```

**"Zero callers" NIJE dovoljno.**

---

## Risks

```text
1. SQLite schema mora biti stabilan kroz migracije.
   Mitigacija: CREATE TABLE IF NOT EXISTS + CREATE VIEW IF NOT EXISTS
               (idempotent); za budućnost schema_migrations tabela.

2. Locator serialize/deserialize round-trip mora biti lossless.
   Mitigacija: JSON sa svim Locator poljima; test round-trip.

3. SQLite file-based repo moze zakljucati WAL ako paralelni procesi.
   Mitigacija: za MVP single-process; WAL mode za sigurnost.

4. Bootstrap kreira ~/.parser_studio/learning.db bez dozvole.
   Mitigacija: env var PARSER_STUDIO_DB za override; mkdir parents=True exist_ok.

5. ConfirmInvoice.execute() sada pise u SQLite ako repo postoji.
   Mitigacija: test_learning_repository provjerava append poziv.

6. Testovi mogu ostaviti temp SQLite fajlove na disku.
   Mitigacija: tmp_path fixture iz pytest-a + cleanup.

7. SQLite JSON podrška je ovisna o verziji Python sqlite3 modula.
   Mitigacija: koristiti json.dumps/loads standard library (Python 3.6+).
```

---

## Execution evidence required

```text
[ ] git diff --stat base..HEAD (samo novi fajlovi + LearningRepository proširenje + bootstrap.py izmjena)
[ ] python -m pytest -q stvarni izlaz
[ ] python -m ruff check . stvarni izlaz
[ ] python -m contract.drift_check "$DEKLARANT_PRO_ROOT" stvarni izlaz
[ ] python -c "from parser_studio.adapters.persistence.sqlite.learning_repository import SQLiteLearningRepository" OK
[ ] python -c "from parser_studio.bootstrap import build_default_application" OK
[ ] python -c "from parser_studio.adapters.persistence.sqlite.learning_repository import SQLiteLearningRepository; r = SQLiteLearningRepository(':memory:'); from parser_studio.domain.learning import LearningEvent, EventType; from parser_studio.domain.evidence.locator import Locator; e = LearningEvent(document_id='d', field_name='kolicina', event_type=EventType.USER_CONFIRMED, new_value=5, locator=Locator(source_path='f.xlsx', kind='excel'), source='test'); r.append(e); print('OK', len(r.events_for('d')))" OK
[ ] graft build output
[ ] graft blast output
[ ] File:line dokaz za legacy netaknutost
```

---

## Reviewer evidence

```text
[ ] vlastiti git diff review
[ ] vlastiti pytest -q reprodukcija
[ ] vlastiti ruff reprodukcija
[ ] vlastiti import sanity provjera (6 modula)
[ ] provjera da legacy core/ NIJE DIRAN
[ ] provjera da domain NE importuje sqlite3 (grep)
[ ] provjera LearningRepository Protocol round-trip (test u REPL)
[ ] provjera SQL migracija (CREATE IF NOT EXISTS, idempotent)
[ ] provjera Gold Dataset projection VIEW
[ ] R-001 ... nalazi
```

---

## Integration gate

```text
[ ] Implementer != Reviewer
[ ] Svi acceptance criteria zadovoljeni
[ ] CURRENT_STATE.md A6 status DONE
[ ] nema stvarnih faktura / poslovnih podataka u Git diffu
[ ] nema secret / token podataka u Git diffu
[ ] Post-merge integration gate: ponoviti pytest + ruff + drift
```

---

## Definition of Done — A6

```text
[ ] LearningRepository Protocol proširen (events_for, events_since)
[ ] SQLiteLearningRepository implementacija (in-memory + file-based)
[ ] 2+ migracije (learning_events, gold_dataset VIEW)
[ ] Gold Dataset projection radi
[ ] bootstrap.py sa SQLite repo
[ ] 8+ unit testova
[ ] pytest ista ili bolja statistika
[ ] ruff ne značajno gore
[ ] contract drift PASS
[ ] Graft blast čist
[ ] CURRENT_STATE A6: DONE
[ ] commit + push
```

---

## Notes

- A6 zavisi od A5 (LearningRepository Protocol vec deklarisan).
- Migracije su u SQL fajlovima (ne Python) — citaju se kao resource iz paketa.
- Gold Dataset projection je SQL VIEW (ne Python klasa) — minimalan, za MVP.
- File-based SQLite repo po defaultu u `~/.parser_studio/learning.db`; env var `PARSER_STUDIO_DB` za override.
- Legacy `core/engines/` ostaje netaknut (A7 cleanup).
- Ako zelis podjelu, mogu predloziti:
  - A6.1 — LearningRepository Protocol proširenje + SQLiteLearningRepository + 001_learning_events
  - A6.2 — Gold Dataset projection (002_gold_dataset.sql) + VIEW + testovi

---

## Final status

```text
[ ] DRAFT
[ ] ACTIVE
[ ] REVIEW
[ ] DONE
[ ] CANCELLED
```

---

## OUT_OF_SCOPE_FINDING (popunjava implementer)

```text
(navesti ako postoji)
```

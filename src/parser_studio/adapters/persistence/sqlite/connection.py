# Adapter: persistence/sqlite/connection.
# Posjeduje: open_connection helper.
# Ne zna za: domain (samo SQLite niske).
"""SQLite connection helper sa parser_studio pragmas.

PRAGMA foreign_keys = ON  - podrska za buduce foreign key veze.
PRAGMA journal_mode = WAL - bolje konkurentno citanje dok se pise.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path


def open_connection(db_path: str | Path) -> sqlite3.Connection:
    """Otvori SQLite konekciju sa parser_studio pragmas.

    db_path moze biti:
    - ":memory:" za in-memory test
    - string/Path za file-based bazu
    """
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


__all__ = ["open_connection"]

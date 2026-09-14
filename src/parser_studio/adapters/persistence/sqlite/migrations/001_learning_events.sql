-- Migration 001: learning_events append-only tabela.
-- V3 sekcija 14: Append-only learning_events + projection tabele.

CREATE TABLE IF NOT EXISTS learning_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL,
    item_id TEXT,
    field_name TEXT NOT NULL,
    event_type TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    locator_json TEXT,
    source TEXT NOT NULL,
    note TEXT,
    created_at TEXT NOT NULL,
    schema_version INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_learning_events_document_id
    ON learning_events(document_id);

CREATE INDEX IF NOT EXISTS idx_learning_events_field_name
    ON learning_events(field_name);

CREATE INDEX IF NOT EXISTS idx_learning_events_created_at
    ON learning_events(created_at);

CREATE INDEX IF NOT EXISTS idx_learning_events_event_type
    ON learning_events(event_type);

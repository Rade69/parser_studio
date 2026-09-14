-- Migration 002: gold_dataset_projection VIEW.
-- V3 sekcija 15: Gold Dataset je projection iz learning_events.
-- V3 sekcija 14: Stvarni poslovni podaci iz Gold Dataseta NE idu u Git (VIEW je lokalna).

CREATE VIEW IF NOT EXISTS gold_dataset_projection AS
SELECT
    document_id,
    item_id,
    field_name,
    new_value AS confirmed_value,
    event_type,
    locator_json,
    source,
    created_at AS confirmed_at,
    schema_version
FROM learning_events
WHERE event_type IN ('USER_CONFIRMED', 'USER_VERIFIED')
ORDER BY created_at, id;

# Lesson procedure segments (versioned JSON)

**Status:** Design (storage not yet required in `curriculum.db`)  
**Related:** [CURRICULUM_JSON_DATABASE_ETL.md](./CURRICULUM_JSON_DATABASE_ETL.md), [CURRICULUM_EXTRACTION_ARCHITECTURE.md](../../scrapers/CURRICULUM_EXTRACTION_ARCHITECTURE.md)

## Purpose

Procedure content today is primarily **`procedure_html`** on `lessons`, with UI splitting driven by the same anchors as `_is_procedure_subheader` in `table_extractor.py` (warm-up, lesson activity, numbered activities, cool-down, synthesis). Agents and ETL consumers should not depend on re-parsing HTML long term.

## Proposed column

- **`lessons.procedure_structured`** (TEXT, JSON) — versioned array of segments, **or** a side table `lesson_procedure_segments (lesson_id, ordinal, kind, title, body_html, body_plain)` if querying per segment is required.

## JSON shape (draft v1)

```json
{
  "schema_version": 1,
  "segments": [
    {
      "kind": "warm_up",
      "title": "Warm-up",
      "body_html": "<p>...</p>"
    },
    {
      "kind": "activity",
      "title": "Activity 1",
      "body_html": "<p>...</p>"
    },
    {
      "kind": "cool_down",
      "title": "Cool-down",
      "body_html": "<p>...</p>"
    }
  ]
}
```

`kind` is an enumerated string aligned with parser anchors: `warm_up`, `activity`, `lesson_synthesis`, `activity_synthesis`, `cool_down`, `other`.

## Pipeline

1. During `flush_buffer` / section close, append segments when `_is_procedure_subheader` fires (same signals as HTML headings).
2. Keep **`procedure_html`** as the render cache until all consumers read JSON.
3. Bump **`schema_version`** only for breaking shape changes; document migrations in this file.

## Validation

- Optional JSON Schema file under `tools/db/schemas/` when implementation lands.
- Extend [tools/scraper/verify_curriculum_db.py](../../../tools/scraper/verify_curriculum_db.py) with a “non-empty `procedure_structured` for sample unit” check once ingestion writes the column.

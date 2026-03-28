# Curriculum database schema (SSOT)

## Canonical source

The **authoritative definition** for a **new** `curriculum.db` used with `backend/database/curriculum.py` is:

1. **[initialize_db.py](initialize_db.py)** — creates `units`, `units_intro`, `lessons`, `standards`, `lesson_standards`, `unit_standards`, `vocabulary_items`, `vocabulary_translations`, `vocabulary_audio`, `lesson_vocabulary`, **`resources`**, and **`lesson_resources`**.

### `lessons.standards_structured`

The **`lessons`** table includes **`standards_structured`** (TEXT, JSON array) as a first-class column in `initialize_db.py`. It stores panel/section/code/`description_lines` structures produced by [tools/scraper/table_extractor.py](../scraper/table_extractor.py) during `ingest_to_curriculum`. Older `curriculum.db` files created before this column existed need migration, for example:

```sql
ALTER TABLE lessons ADD COLUMN standards_structured TEXT;
```

(Apply only if `PRAGMA table_info(lessons)` shows the column is missing.)

### `lessons.ela_key_learning_summary`

**`ela_key_learning_summary`** (TEXT, JSON object) stores the unit-level **Summary of Key Learning** matrix row for that lesson, produced by [tools/scraper/ela_summary_table.py](../scraper/ela_summary_table.py) during ELA `ingest_to_curriculum` when the table is detected. Older databases may lack the column:

```sql
ALTER TABLE lessons ADD COLUMN ela_key_learning_summary TEXT;
```

**Writer parity:** include `ela_key_learning_summary` in `upsert_lesson` `requested_columns` and in `curriculum_validation.REQUIRED_COLUMNS["lessons"]`. [backend/database/curriculum.py](../../backend/database/curriculum.py) `ensure_provenance_columns` (or equivalent) should add the column on existing DBs so API validation matches `initialize_db.py`.

### `lessons.ela_lesson_plan_structured`

**`ela_lesson_plan_structured`** (TEXT, JSON object) stores the per-lesson **detailed** ELA plan table when [tools/scraper/ela_lesson_plan_table.py](../scraper/ela_lesson_plan_table.py) recognizes the grid (`Lesson N:` title row plus Learning Intention / Success Criteria headers). Older databases may lack the column:

```sql
ALTER TABLE lessons ADD COLUMN ela_lesson_plan_structured TEXT;
```

**Writer parity:** include it in `upsert_lesson` `requested_columns`, `_LESSON_EXTRA_SCHEMA_COLUMNS` in [backend/database/curriculum.py](../../backend/database/curriculum.py), and `REQUIRED_COLUMNS["lessons"]` in [backend/database/curriculum_validation.py](../../backend/database/curriculum_validation.py).

**API startup parity:** [backend/database/curriculum_validation.py](../../backend/database/curriculum_validation.py) enforces required `lessons` columns (including `standards_structured`) before curriculum routes run. When you add a column to `initialize_db.py` and `upsert_lesson`, update the validator’s `REQUIRED_COLUMNS` in the same change set.

Run from repo root (or adjust path): this script **recreates** `d:\LP\data\curriculum.db` from scratch. Use only when intentional.

After a fresh init, seed at least one `units` row before `ingest_to_curriculum` (see [seed_reference_unit.py](seed_reference_unit.py)) or run [recreate_and_ingest_sample.py](recreate_and_ingest_sample.py).

2. **[init_resource_db.py](../scraper/init_resource_db.py)** — `CREATE TABLE IF NOT EXISTS` for `resources` and `lesson_resources` on an existing DB (safe to run on older DBs that lack those tables).

## Legacy / reference only

- **[init_curriculum_db.sql](init_curriculum_db.sql)** — older sketch with different `vocabulary` / `resources` shapes. **Do not** use as SSOT for new installs. Code and migrations in the wild may have evolved past this file; treat it as historical reference.

## Runtime evolution

Existing `curriculum.db` files may have extra columns (e.g. wide `lessons` rows from [extract_curriculum.py](extract_curriculum.py)). `CurriculumDatabase.upsert_lesson` only writes columns that exist (`PRAGMA table_info`).

## Validation

- [backend/database/curriculum_validation.py](../../backend/database/curriculum_validation.py) checks required tables and columns at API startup for curriculum routes.
- [../scraper/verify_curriculum_db.py](../scraper/verify_curriculum_db.py) — manual or CI check after ingestion.

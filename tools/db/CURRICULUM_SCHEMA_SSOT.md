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

### `lessons.science_doc_lesson_number` and `lessons.science_li_sc_day_structured`

- **`science_doc_lesson_number`** (INTEGER, nullable): the curriculum-writer `Lesson N` number from the DOCX module heading for Science ingest (repeats across modules in a long guide; used to align overview tables).
- **`science_li_sc_day_structured`** (TEXT, JSON object): per-module **Learning intention / Success criteria** overview table split into ordered **day segments**. Each segment uses **`label`** (writer day key, e.g. `Day 1`, `Days 2&3`), **`learning_intention_html`**, **`success_criteria_html`**, **`brief_overview`** (HTML from the **Summary of Key Learning** table when detected in the tables preceding that lesson’s LI/SC grid), **`lesson_in_action_html`** (full **THE LESSON IN ACTION** table, lossless), and optionally **`experimental_splits`** (`opening_html`, `during_html`, `closing_html`, `online_html`) only when heading-based validation succeeds in the scraper. **`schema_version`** `2` indicates this segment shape. Produced by [tools/scraper/science_lesson_tables.py](../scraper/science_lesson_tables.py) during Science `ingest_to_curriculum` (`source` may be `science_lesson_tables@v2` when action tables were merged).

```sql
ALTER TABLE lessons ADD COLUMN science_doc_lesson_number INTEGER;
ALTER TABLE lessons ADD COLUMN science_li_sc_day_structured TEXT;
```

**Writer parity:** include both in `upsert_lesson` `requested_columns`, `_LESSON_EXTRA_SCHEMA_COLUMNS` in [backend/database/curriculum.py](../../backend/database/curriculum.py), and `REQUIRED_COLUMNS["lessons"]`.

### `science_lesson_day_segments`

Relational mirror of **`lessons.science_li_sc_day_structured`**: one row per writer day segment for Science ingest. Populated in the same ingest transaction via `CurriculumDatabase.replace_science_lesson_day_segments` (stable `id` = `{lesson_id}_sci_{segment_index}`). The JSON column remains the scraper SSOT; the bundle API exposes ordered `science_day_segments` for clients that should not parse JSON.

| Column | Type | Notes |
|--------|------|--------|
| `id` | TEXT PK | `{lesson_id}_sci_{segment_index}` |
| `lesson_id` | TEXT NOT NULL | FK to `lessons.id` |
| `segment_index` | INTEGER NOT NULL | 0-based; UNIQUE with `lesson_id` |
| `day_label` | TEXT NOT NULL | Writer label (e.g. Day 1) |
| `science_doc_lesson_number` | INTEGER | From payload `doc_lesson_number` |
| `learning_intention_html` | TEXT | |
| `success_criteria_html` | TEXT | |
| `brief_overview_html` | TEXT | From segment `brief_overview` in JSON |
| `lesson_in_action_html` | TEXT | |
| `experimental_splits_json` | TEXT | Optional JSON object |

Idempotent creation: `CurriculumDatabase.ensure_science_lesson_day_segments_table()` (via `ensure_provenance_columns`).

### `g2_science_book_lesson_supplement`

Optional **Grade 2 Inspire Science student workbook** cross-reference (not writer SSOT for lesson HTML). One row per canonical `lesson_id` under `Science_2_Mod*`. Populated by [`seed_g2_science_book_lesson_supplement.py`](seed_g2_science_book_lesson_supplement.py) from the PDF beside the scraped DOCX plus [`Tab_1.md`](../../reference_docs/scraped/Copy_of__2nd_Grade_Science/Tab_1/Tab_1.md). Exposed on `GET /api/curriculum/lessons/{id}/bundle` as `book_lesson_supplement` when present.

| Column | Type | Notes |
|--------|------|--------|
| `lesson_id` | TEXT PK | FK `lessons.id` |
| `source_pdf_label` | TEXT | Stable label for the workbook artifact |
| `isbn13` | TEXT | From filename / metadata |
| `pdf_page_start` / `pdf_page_end` | INTEGER | Heuristic span where worksheet title appears in page header |
| `pdf_title_hit_count` | INTEGER | Pages matching title-in-head heuristic |
| `first_page_workbook_pattern` | TEXT | e.g. `MODULE_OPENER`, `ASSESS_LESSON_READINESS` |
| `paired_read_block_title` | TEXT | Curated teacher-facing block names |
| `teacher_curriculum_cue` | TEXT | Snippet from Tab_1 near title + paired-read wording |
| `format_notes` | TEXT | e.g. PDF module order vs canonical `unit_number` |
| `updated_at` | TEXT | ISO8601 UTC |

Idempotent creation: `CurriculumDatabase.ensure_g2_science_book_lesson_supplement_table()` (via `ensure_provenance_columns`).

### `g2_science_book_lesson_extract`

Per-page **plain text** from the same Grade 2 Inspire student workbook PDF, aligned to canonical `lesson_id` (title-in-head heuristic + optional overrides). **Complement only** (ADR-003); does not replace teacher lesson HTML.

| Column | Type | Notes |
|--------|------|--------|
| `id` | TEXT PK | Stable id e.g. `{lesson_id}_bkp{page}` |
| `lesson_id` | TEXT NOT NULL | FK `lessons.id` |
| `page_number` | INTEGER NOT NULL | 1-based PDF page |
| `body_text` | TEXT NOT NULL | Normalized `pdfplumber` extract |
| `char_count` | INTEGER | |
| `content_sha256` | TEXT | Hash of `body_text` for invalidation |
| `alignment_confidence` | TEXT | `high` / `low` / `none` (stored values: high/low from matcher) |
| `alignment_ambiguous` | INTEGER | 0/1 when multiple same-length title hits |
| `source_pdf_label` | TEXT | Same label as supplement rows (`SOURCE_PDF_LABEL` in tools) |
| `ingest_parser_version` | TEXT | e.g. `g2_book_extract@v1` |
| `ingested_at` | TEXT | ISO8601 UTC |

**UNIQUE** (`lesson_id`, `page_number`). Populated by [`ingest_g2_science_book_pdf.py`](ingest_g2_science_book_pdf.py). Bundle API: optional `book_page_extracts` on `GET /api/curriculum/lessons/{id}/bundle?include_book_extracts=true`; paginated `GET /api/curriculum/lessons/{id}/book-extracts`. Long `body_text` responses are truncated server-side.

Idempotent creation: `CurriculumDatabase.ensure_g2_science_book_lesson_extract_table()` (via `ensure_provenance_columns`).

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

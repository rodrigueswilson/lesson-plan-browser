# Curriculum extraction architecture

This document describes how curriculum content moves from Google Docs / DOCX into SQLite and the API. For schema ownership, see [tools/db/CURRICULUM_SCHEMA_SSOT.md](../../tools/db/CURRICULUM_SCHEMA_SSOT.md) and [ADR-002: Curriculum SQLite schema SSOT](../decisions/ADR-002-curriculum-schema-ssot.md).

## End-to-end flow

```mermaid
flowchart LR
  subgraph fetch [Fetch and export]
    DC[docs_client.DocsClient]
    GP[Google Docs API / Drive export]
    DC --> GP
    GP --> JSON[Document JSON]
    GP --> DOCX[DOCX on disk]
  end
  subgraph transform [Transform]
    MDP[docs_processor.GoogleDocsProcessor]
    JSON --> MDP
    MDP --> MD[Markdown per tab]
    RTP[table_extractor.RecursiveTableParser]
    DOCX --> RTP
  end
  subgraph persist [Persistence]
    OLP[(original_lesson_plans)]
    CUR[(curriculum.db tables)]
    RTP -->|ingest_to_db| OLP
    RTP -->|ingest_to_curriculum| CUR
  end
  subgraph api [API]
    R[routers/curriculum.py]
    CDB[CurriculumDatabase]
    CUR --> CDB
    CDB --> R
  end
```

## Module responsibilities

| Module | Role |
|--------|------|
| [tools/scraper/main.py](../../tools/scraper/main.py) | CLI orchestration: recursive doc walk, export HTML/DOCX/JSON, markdown tabs, optional `ingest_to_db` when `--user_id` is set. |
| [tools/scraper/docs_client.py](../../tools/scraper/docs_client.py) | OAuth client: `get_document`, `export_document`, `get_document_json`. |
| [tools/scraper/docs_processor.py](../../tools/scraper/docs_processor.py) | Google Docs JSON to markdown; tabs and nested tabs; inline image placeholders. |
| [tools/scraper/crawler.py](../../tools/scraper/crawler.py) | Link extraction and classification from doc JSON for recursion. |
| [tools/scraper/table_extractor.py](../../tools/scraper/table_extractor.py) | DOCX parse: recursive tables, hyperlinks, semantic stream; `ingest_to_curriculum` (lessons/standards/vocab/resources); `ingest_to_db` (extraction cache). |
| [tools/scraper/cell_content_format.py](../../tools/scraper/cell_content_format.py) | **Cross-subject SSOT helpers** on table cell JSON: walk runs/paragraphs, collect hyperlinks, split leading bold title vs body (shared by ELA summary and ingest tooling). |
| [tools/scraper/subject_config.py](../../tools/scraper/subject_config.py) | Subject-specific lesson title regexes and section anchor strings. |
| [tools/scraper/science_lesson_tables.py](../../tools/scraper/science_lesson_tables.py) | Grade 2 Science: structured pass for learning-intention / success-criteria grids (and related merges into lesson records); complements the semantic DOCX stream, not ELA table rules. |
| [backend/database/curriculum.py](../../backend/database/curriculum.py) | Reads/writes `curriculum.db` for explorer, lessons, unit intro, vocabulary, resources. |
| [backend/database/curriculum_validation.py](../../backend/database/curriculum_validation.py) | Validates required tables/columns before curriculum routes run. |
| [backend/routers/curriculum.py](../../backend/routers/curriculum.py) | REST endpoints for curriculum explorer and lesson detail. |

The lesson-plan browser loads full lesson payloads via **`GET /api/curriculum/lessons/{lesson_id}/bundle`** (lesson + vocabulary + standards in one response), with optional client-side IndexedDB caching and `If-None-Match` when `content_hash` yields an ETag.

### Grade 2 Science: module day-band index (API + UI)

- **`GET /api/curriculum/units/{unit_id}/science-day-outline`** — Returns **`unit_id`**, **`lessons`** (each with **`lesson_id`**, **`lesson_number`**, **`title`**, **`segments`**: **`segment_index`**, **`day_label`** only), and **`total_writer_bands`**. This is a **read-only SSOT index** for pacing context; it is **not** a school-calendar projection (see [ADR-003-grade2-science-cluster-ssot-and-daily-projection.md](ADR-003-grade2-science-cluster-ssot-and-daily-projection.md)). Source: `science_lesson_day_segments` joined to `lessons` ([`backend/database/curriculum.py`](../../backend/database/curriculum.py) `get_unit_science_day_outline`).
- **Full segment payloads** (HTML, experimental splits, etc.) remain on the **lesson bundle** as **`science_day_segments`**.
- **Explorer:** [`lesson-plan-browser/frontend/src/components/CurriculumExplorer.tsx`](../../lesson-plan-browser/frontend/src/components/CurriculumExplorer.tsx) loads the outline for units whose ids match the canonical Science module pattern; the module overview shows cumulative writer bands and uses **Module N** labeling for those units.

## Two ingestion modes (do not conflate)

1. **`RecursiveTableParser.ingest_to_db(docx_path, metadata)`**  
   - Target: application **lesson-plans** SQLite (same default as `SQLiteDatabase()`, not `curriculum.db`), table **`original_lesson_plans`**.  
   - Purpose: structured extraction cache (JSON + `full_text`) for downstream processing.  
   - Writer: [backend/database/plans.py](../../backend/database/plans.py) via `SQLiteDatabase.create_original_lesson_plan`.

2. **`RecursiveTableParser.ingest_to_curriculum(docx_path, unit_id, subject)`**  
   - Target: **`curriculum.db`** (path configurable on `CurriculumDatabase`).  
   - Purpose: normalized curriculum graph: `units` / `lessons` / `standards` / `vocabulary_*` / `resources` / junction tables.  
   - Used by scraper batch scripts and [test_full_ingestion.py](../../tools/scraper/test_full_ingestion.py), not by the default `main.py` recursive flow.

## Operational notes

- **Linked Google Docs** may enrich `procedure_html` when `docs.google.com/document/d/...` links exist; Drive files and Slides are not DOCX-exportable and are skipped for recursion.  
- **Section routing** in `ingest_to_curriculum` depends on anchor strings in `SubjectConfig`; missing anchors can leave `procedure_html` empty until anchors or fallbacks are extended.  
- **Grade 2 Science:** procedure routing often needs **curriculum-specific** anchor strings (writer headings such as “THE LESSON IN ACTION,” “Do It Now in Science,” “Online Learning Activities”) added to `SubjectConfig.SCIENCE` when those strings bound procedural content in the DOCX. Grids for learning intentions and success criteria are parsed in a **separate pass** by [`tools/scraper/science_lesson_tables.py`](../../tools/scraper/science_lesson_tables.py) (analogous in role to ELA’s dedicated table extractors, not a duplicate of `ela_summary_table.py`). After changes, **cross-check** semantic-stream fields (for example `procedure_html`) against structured Science payloads so no block appears only in one path. See [RUNBOOK-grade2-science-three-step-pacing-and-daily-drafts.md](./RUNBOOK-grade2-science-three-step-pacing-and-daily-drafts.md).  
- **Schema drift**: `upsert_lesson` filters columns against `PRAGMA table_info(lessons)`; unknown columns are omitted (warnings logged when keys are dropped).

## AI-assisted extraction policy (optional second pass)

- **Default authority:** Deterministic `tools/scraper` extraction remains the SSOT baseline for curriculum ingestion.
- **Scope:** AI/agentic extraction may be used only as an optional second pass for targeted gaps (for example, missing/ambiguous sections or layout-classification uncertainty).
- **Field ownership:** Any AI-assisted write scope must be documented in issue/ADR acceptance criteria before implementation; do not allow implicit field expansion.
- **No silent replacement:** AI output must not silently replace deterministic output outside the declared field scope.
- **Failure behavior:** Missing credentials, timeout/rate limit, or invalid schema response must preserve deterministic results and emit ingest evidence/warnings.
- **A4 provenance:** AI-assisted paths must preserve provenance expectations, including hyperlink/resource lineage semantics when applicable.

## High-fidelity lesson fields (ingestion and API)

### `standards_structured` on `lessons`

During `flush_buffer`, the parser builds a JSON array of objects shaped like `{ "panel": "left"|"right", "section": string, "code": string, "description_lines": string[] }` from standards panels (NJ, MP, NCTM content/process). That JSON is stored on the lesson row as **`standards_structured`** (TEXT JSON) and written by `upsert_lesson` in [backend/database/curriculum.py](../../backend/database/curriculum.py). The curriculum API returns it on lesson detail; the explorer UI prefers it for standards layout when present. See also [backend/database/curriculum_validation.py](../../backend/database/curriculum_validation.py) (required column at API startup).

### ELA `ela_key_learning_summary` (Summary of Key Learning matrix)

For **`ingest_to_curriculum`** with **`subject="ELA"`**, the first DOCX table that matches the unit-level **Summary of Key Learning** layout (see `SubjectConfig.ELA_SUMMARY_TABLE` and [tools/scraper/ela_summary_table.py](../../tools/scraper/ela_summary_table.py)) is parsed into structured JSON per **lesson number** and stored on **`lessons.ela_key_learning_summary`**. That table is **not** flattened into the semantic stream, so its text is not duplicated into `procedure_html`. Per-lesson **detailed** tables are still flattened into the semantic stream **and**, when they match the **Lesson N:** grid (see [tools/scraper/ela_lesson_plan_table.py](../../tools/scraper/ela_lesson_plan_table.py)), are parsed into **`lessons.ela_lesson_plan_structured`** (JSON by section titles: learning intentions, NJSLS block, key practices, vocabulary/resources, procedures buckets, differentiation).

**Column-level SSOT (Grade 2–3 style matrix):** [ELA_SUMMARY_OF_KEY_LEARNING_STRUCTURE.md](./ELA_SUMMARY_OF_KEY_LEARNING_STRUCTURE.md).

### Standards vs procedure boundaries and buffers

- **Link and standards extraction** always iterate the **raw** paragraph buffer (`self._buffer`) so headings such as `Activity n:`, `Warm-up`, resource lines, and short section titles are not appended into standard descriptions.
- **HTML assembly** for most lesson columns may use a **merged** copy of the buffer: `merge_docx_soft_break_paragraphs` is applied only when the active section is in `_SOFT_BREAK_MERGE_SECTIONS` in [tools/scraper/table_extractor.py](../../tools/scraper/table_extractor.py). **`_standards_temp` is not in that set** (standards side panels are excluded from soft-break merge for HTML).
- **`_is_non_standard_heading`** prevents procedure/resource headings from being treated as standards text during merge heuristics where relevant.

### Procedure subheaders

Lines that match warm-up / numbered activity / cool-down / lesson or activity synthesis (see `_is_procedure_subheader` in `table_extractor.py`) force routing into **`procedure_html`** and are re-emitted as content so titles appear in the rendered HTML.

### Soft-break paragraph merge

`merge_docx_soft_break_paragraphs` joins adjacent DOCX paragraphs when Word split mid-sentence: the previous chunk has **no** sentence-ending punctuation and the next starts with a **lowercase** letter. **Two bullets are never merged.** Merge is **not** applied across procedure subheaders, non-standard headings, or known standards section title lines.

Lesson fields in **`_SOFT_BREAK_MERGE_SECTIONS`**: `narrative_html`, `purpose`, `procedure_html`, `learning_intentions`, `objectives_student`, `mlr`, `materials`, `vocabulary`, `instructional_resources`, `daily_instructional_task`, `success_criteria`, `essential_questions`, `lesson_narrative`.

### Vocabulary

The **Vocabulary** section populates the lesson’s **`vocabulary`** HTML field and drives term extraction into **`_vocabulary`** / relational **`lesson_vocabulary`** (and related `vocabulary_items` rows) during ingestion.

### Cross-links

- [tools/db/recreate_and_ingest_sample.py](../../tools/db/recreate_and_ingest_sample.py) — recreate DB, seed unit, ingest sample Math Unit 2 DOCX.  
- [backend/routers/curriculum.py](../../backend/routers/curriculum.py) — REST surface for explorer hierarchy and lesson detail.  
- [backend/database/curriculum_validation.py](../../backend/database/curriculum_validation.py) — schema gate for curriculum routes.

### Cross-subject cell JSON and display (Math + ELA)

- **Structural SSOT:** Parsed DOCX table cells are lists of elements (`paragraph` with `runs` / `is_bullet` / `ilvl`, nested `table`). Math and ELA both use the same model from `RecursiveTableParser._parse_paragraph` / `_parse_table`. Do not re-derive structure by regex-parsing stored HTML for ingestion or shared algorithms.
- **HTML SSOT:** `RecursiveTableParser.json_to_html` is the primary emitter for lesson HTML fields. Optional **leading bold label** enrichment wraps the first bold run sequence of the first paragraph in each cell-level `json_to_html` call in `<span class="rich-cell-label">` for UI styling (see `.rich-html` in the lesson-plan-browser stylesheet).
- **Document layouts (reference only):** [math_unit_structure_analysis.md](math_unit_structure_analysis.md) (math grid anchors and in-cell bold labels); [ELA_SUMMARY_OF_KEY_LEARNING_STRUCTURE.md](ELA_SUMMARY_OF_KEY_LEARNING_STRUCTURE.md) (unit matrix + column C bold task title).
- **Local-first curriculum links:** Google Doc hyperlinks are emitted as `<a href="…" data-resource-id="…">`. The `resources` table may store `local_path` when a file exists under `CURRICULUM_LOCAL_FILES_ROOT` (see `backend.config.Settings`). The API exposes `GET /api/curriculum/resources/google-id/{id}/resolve` (preferred URL for open) and `GET /api/curriculum/resources/google-id/{id}/file` (serve local file when present). The curriculum explorer rewrites or intercepts `data-resource-id` links to use the resolver.

## External references and research

For **agentic / LLM-assisted** document extraction, local shallow clones of reference projects, and per-repository research questions keyed to this pipeline, use the committed index [Agentic document extraction research](../research/agentic_doc_extraction_index.md). On-disk clones and spikes live under `research/agentic_doc_extraction/` ([README](../../research/agentic_doc_extraction/README.md)); those folders are gitignored except the README.

## Related docs

- [math_unit_structure_analysis.md](math_unit_structure_analysis.md) — observed DOCX grid patterns.  
- [ADR-003-grade2-science-cluster-ssot-and-daily-projection.md](ADR-003-grade2-science-cluster-ssot-and-daily-projection.md) — Grade 2 Science decision record for cluster SSOT, calendar projection, and AI advisory drafts.
- [RUNBOOK-grade2-science-three-step-pacing-and-daily-drafts.md](RUNBOOK-grade2-science-three-step-pacing-and-daily-drafts.md) — operational workflow for Science variation (ingest, projection, validation, troubleshooting).
- [tools/db/CURRICULUM_SCHEMA_SSOT.md](../../tools/db/CURRICULUM_SCHEMA_SSOT.md) — canonical curriculum tables.  
- [tools/scraper/verify_curriculum_db.py](../../tools/scraper/verify_curriculum_db.py) — post-ingestion integrity CLI.
- [tools/db/recreate_and_ingest_sample.py](../../tools/db/recreate_and_ingest_sample.py) — wipe/recreate `curriculum.db` from SSOT, seed reference unit, ingest sample DOCX (`--full-unit` for entire Unit 2 file).

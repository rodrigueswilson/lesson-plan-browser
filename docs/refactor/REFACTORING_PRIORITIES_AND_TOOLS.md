# Refactoring Priorities and Tools

This document lists **refactoring and fix priorities** for the codebase and gives a **critical overview of Python refactoring libraries** and when they are worth using. It also defines a **multi-session plan** (branches, commits, merges) and a **progress log** so different Cursor sessions can resume work consistently.

---

## 0. Multi-session plan and progress (update this as you go)

**Last updated:** 2026-02-22 (Session 26: six biggest files under 400 LOC — fill_cell, extraction, signatures, analyze_objectives_layout, users, metrics; see 0.1, 0.5, 1.4.)

### 0.1 Progress summary


| Status          | Items                                                                                                                                                                                                                                                                     |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Done**        | Batch processor package; Database alias and optional db_path (see 1.4). Session 1 (branch `fix/test-suite-collection`): test suite collection and fixes. Session 2 (branch `refactor/split-api`): split backend/api.py into routers (health, settings, users, plans, process-week, analytics); app mounts routers; duplicate analytics removed; API/smoke tests pass. Follow-up: core router (validate, render, progress, transform, repair, tablet export), FastAPI lifespan, enrich_lesson_json_with_times in backend.utils.lesson_times, plan download in plans router; call sites updated (combine.py, scripts). Session 3 (refactor llm_service): prompt_builder, validation, providers, schema, parse_llm_response, post_process, domain_analysis extracted to backend/llm/; llm_service.py 789 lines; merged to master. Session 23 (branch refactor/llm-service-split): api_key, token_limits, transform_runner extracted to backend/llm/; llm_service.py slim facade (~329 lines). See **0.5** for line counts per file. Session 4 (branch `refactor/performance-tracker`): retention 30 days, cleanup on init, sampling + debug_mode (env DEBUG_PERFORMANCE_TRACKING), critical ops include llm_api_call; retention/sampling/debug_mode tests; SQLite WAL for file DBs. Session 5 (branches `refactor/docx-renderer`, `refactor/docx-renderer-table-cell`): DOCX renderer package with style.py, hyperlink_placement.py, renderer.py, table_cell package (fill, format, placement); merged to master. Session 6 (branch `refactor/docx-parser`): DOCX parser package with structure.py, no_school.py, table_extraction.py, content_sections.py, slot_extraction.py, images_metadata.py, parser.py, parse_docx; public API unchanged. Line counts in **0.5**. Session 7 (branch `refactor/database-split`): backend/database.py replaced by package backend/database/ (engine, users, slots, plans, metrics, schedule, lesson_steps, lesson_mode, sqlite_impl, get_db); single get_db() and DatabaseInterface preserved; DB/API tests pass. Line counts in **0.5**. Session 8 (branch `refactor/combined-original-styles`): post-merge style normalization for combined_originals DOCX; docProps replacement; docx_utils module logger; style tests; hyperlink Times New Roman 8pt in markdown; Supabase log-once. See **1.4**. Session 9 (branch `refactor/supabase-module`): backend/supabase_database.py replaced by package backend/supabase/ (auth, query_helpers, sync, client, database); facade supabase_database.py re-exports; get_project1_db/get_project2_db added; sync script uses backend.supabase.sync. See **1.4**. Session 10 (branch `refactor/frontend-analytics`): Analytics moved to Settings/Admin; Analytics split into useAnalytics hook and subcomponents; ErrorBreakdown copy clarified. See **1.4**. Session 11 (branch `refactor/batch-processor-tsx`): BatchProcessor.tsx refactor — useBatchProcessor hook and subcomponents; re-exports. See **1.4**. Session 12 (branch `refactor/root-declutter`): root declutter per ROOT_DECLUTTERING_PLAN; docs/scripts archived; links verified. Session 13 (branch `refactor/orchestrator-split`): week_flow, slot_flow; orchestrator thin coordinator; merged to master. See **0.9**, **1.4**. Session 14 (branch `refactor/plans-router-split`): plans router split into plans.py (slim), lesson_mode.py, lesson_steps.py, lesson_steps_generator service; API/slot tests pass; merged to master and pushed to origin; post-merge fix (build-apk.ps1, TabletSync, lesson-steps test). See **1.4**. Session 15 (branch `refactor/users-router-split`): users router split into users.py (slim), slots.py, schedule.py; conftest get_db patches for slots/schedule; API/slot tests pass. See **1.4**, **0.5**. Session 16 (branch `refactor/combine-split`): combine.py split into originals_json.py, combine_render.py; combine.py slim (merge + combine orchestration); batch_processor/originals/combined_original tests pass. See **1.4**. Session 17 (branch `refactor/sentence-frames-objectives-split`): sentence_frames_pdf_generator and objectives_printer split into sentence_frames/ and objectives/ subpackages; facades preserve API; tests pass. See **1.4**, **0.5**. Session 18 (branch `refactor/schedule-slot-frontend`): ScheduleInput and SlotConfigurator refactor — schedule_input/ (useScheduleInput, ScheduleInputHeader, ScheduleInputTable, ScheduleColorLegend, NoUserSchedule), slot_configurator/ (useSlotConfigurator, SortableSlotItem); re-exports. See **1.4**. Session 19 (branch `refactor/fill-py-split`): table_cell/fill.py split into fill_metadata.py, fill_day.py, fill_cell.py; fill.py re-exports. See **1.4**. Session 20 (branch `refactor/slot-flow-split`): slot_flow.py split into slot_flow_resolve.py, slot_flow_extract.py, slot_flow_transform.py; slot_flow.py slim orchestrator; process_one_slot unchanged. See **0.5**. Session 21 (branch `refactor/lesson-steps-generator-split`): lesson_steps_generator.py split into backend/services/lesson_steps/ (plan_resolve, slot_data, phase_steps, vocab_frames_steps); facade lesson_steps_generator.py; generate_lesson_steps public API unchanged. See **0.5**. Session 22 (branch `refactor/week-flow-split`): week_flow.py split into week_flow_load.py, week_flow_existing.py, week_flow_parallel.py, week_flow_sequential.py, week_flow_merge_render.py; week_flow.py slim orchestrator; run_process_user_week public API unchanged. See **0.5**. Session 24 (branch `refactor/slim-docx-renderer-renderer`): renderer.py slimmed; format_*, fill_metadata/fill_single_slot_day/fill_multi_slot_day, try_*, extract_*, filter_*, force_* removed or delegated to table_cell/style; table_cell calls style directly for fonts. See **0.5**, **1.4**. Session 25 (branches refactor/slim-tools-json-repair, refactor/slim-backend-lesson-schema-models, refactor/slim-tools-docx-utils): json_repair, lesson_schema_models, docx_utils under 400 LOC; extractions to json_repair_fixes, lesson_schema_vocabulary, lesson_schema_support, docx_style_utils. See **0.5**, **1.4**. Session 26 (six biggest files): fill_cell (section_mappings, fill_cell_cleanup), extraction (extraction_primary_file), signatures (signature_table_fill), analyze_objectives_layout (objectives_layout_heights), users (users_list_logic), metrics (metrics_aggregate); all under 400 LOC. See **0.5**, **1.4**. |
| **In progress** | None. |
| **Not started** | None. |


### 0.2 Session plan: branches, commits, merges

Work in order when possible; fix test suite (Session 1) before large refactors so tests are reliable.


| Session | Branch name                         | Priorities    | Create branch                           | Commit working/tested                                                                                                             | Merge to master                                      |
| ------- | ----------------------------------- | ------------- | --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| 1       | `fix/test-suite-collection`         | 4             | Start of session 1                      | After TestClient, test_api_endpoints, test_week_calculation, DOCX paths, backend_connection fixes; pytest collects and runs.      | When all targeted tests pass and no new regressions. |
| 2       | `refactor/split-api`                | 1             | Start of session 2 (from latest master) | After splitting into routers (users, plans, process-week, analytics, settings, health); app mounts routers; smoke/API tests pass. | When API tests and manual smoke pass.                |
| 3       | `refactor/llm-service`              | 2             | Start of session 3                      | After extracting prompt building, retry/validation, provider adapters; existing LLM tests pass.                                   | When LLM tests and one full flow pass.               |
| 4       | `refactor/performance-tracker`      | 3             | Start of session 4                      | After adding retention (e.g. 30 days), optional sampling/debug-only tracking; DB size/lock checks pass.                           | When metrics tests and manual check pass.            |
| 5       | `refactor/docx-renderer`            | 5             | Start of session 5                      | After extracting table/cell, hyperlink, multi-slot, style modules; render tests pass.                                             | When DOCX render tests and one full week run pass.   |
| 6       | `refactor/docx-parser`              | 6             | Start of session 6                      | After extracting structure, slot extraction, table/paragraph modules; parser tests pass.                                          | When parser tests and pipeline run pass.             |
| 7       | `refactor/database-split`           | 7             | Start of session 7                      | After splitting by domain (user CRUD, plans/slots, lesson steps, metrics, migrations); single `get_db()`; DB tests pass.          | When all DB-dependent tests pass.                    |
| 8       | `refactor/combined-original-styles` | 8             | Start of session 8                      | After style conflict handling per ERROR_ANALYSIS; combined-original output checked.                                               | When style checks and one full combine pass.         |
| 9       | `refactor/supabase-module`          | 9             | Start of session 9                      | After extracting auth, query helpers, sync logic; Supabase tests pass.                                                            | When Supabase/local tests pass.                      |
| 10      | `refactor/frontend-analytics`       | 10            | Start of session 10                     | After moving to Settings/Admin and splitting subcomponents/hooks; frontend build and smoke pass.                                  | When build and analytics smoke pass.                 |
| 11      | `refactor/batch-processor-tsx`      | 11            | Start of session 11                     | After extracting week/slot, progress, error components/hooks; BatchProcessor smoke pass.                                          | When frontend build and batch UI smoke pass.         |
| 12      | `refactor/root-declutter`           | 12            | Start of session 12                     | After archiving/organizing per ROOT_DECLUTTERING_PLAN; docs and scripts still findable.                                           | When links/scripts verified.                         |
| 13      | `refactor/orchestrator-split`       | 13 (optional) | Start of session 13                     | After splitting by phase if done; batch_processor_pkg tests pass.                                                                 | When batch pipeline tests pass.                      |


### 0.3 Workflow rules (per session)

1. **Start:** Pull latest `master`, create the session branch from `master`.
2. **Use refactoring libraries where they help:** To make changes **safer**, **faster**, and **more efficient**, use the Python tools in **Section 2** (Rope, Bowler, LibCST, and optionally Refex) and the **Section 3** workflow: IDE/Rope for renames and local extracts; Bowler or LibCST for mechanical patterns across many files; manual edits for large-file splits. This reduces errors and avoids missed call sites/imports.
3. **During:** Make small, testable commits on the branch. Run the focused test set or full pytest (and frontend build if touching frontend) before each "working" commit.
4. **Commit "working/tested":** When the scope for that session is done and tests pass, commit with a clear message (e.g. `refactor(api): split into routers by domain`).
5. **Merge to master:** When the branch is fully tested and reviewed, merge to `master` (e.g. via PR or direct merge per your process). Then update section 0.1 and 1.4 in this document: move the item to "Done" and add a short note under 1.4 if needed.
6. **Next session:** Start from updated `master` and the next row in the table.

**Running the full suite:** The suite has 650+ tests and can take several minutes. Run in your own terminal: `python -m pytest tests/ -q` (or `-v`). `pytest.ini` sets `--timeout=120` per test (requires `pytest-timeout`); if a test hits 120s it will fail instead of hanging. To override: `python -m pytest tests/ -q --timeout=180` or `--timeout=0` to disable. For a quick check: `python -m pytest tests/test_api.py tests/test_database_crud.py tests/test_week_calculation.py -q`. **TestClient/httpx:** Tests require `httpx>=0.24,<0.28` for Starlette TestClient compatibility (see `requirements.txt`). **DB-dependent tests:** Use the shared `isolated_db` (or `temp_db` / `test_db` / `db`) fixture from `tests/conftest.py` so each test gets an initialized, isolated SQLite DB; do not use `session.cursor()` — use `session.execute(text("..."))` with SQLModel Session.

### 0.4 How to update this document after each session

- **Section 0.1 (Progress summary):** Move completed priorities from "Not started" to "Done"; put the current session's work in "In progress" while active.
- **Section 0.2:** Leave as-is unless you add or reorder sessions.
- **Section 1.4 (Done):** Add a one-line bullet per completed refactor (branch name and what was done), e.g. `- **Split backend/api.py** — Branch refactor/split-api; routers by domain (see session 2).`
- **Last updated:** Set to the date when you last edited this file.

### 0.5 Line counts (backend LLM, post–Session 23; docx_renderer post–Session 24 slim)

| Lines | File |
| -----:| ------ |
| 673 | `backend/llm/prompt_builder.py` |
| 673 | `backend/llm/validation.py` |
| 329 | `backend/llm_service.py` |
| 320 | `backend/llm/transform_runner.py` |
| 290 | `backend/llm/providers.py` |
| 141 | `backend/llm/schema.py` |
| 127 | `backend/llm/api_key.py` |
| 112 | `backend/llm/domain_analysis.py` |
| 82 | `backend/llm/token_limits.py` |
| 45 | `backend/llm/post_process.py` |
| 36 | `backend/llm/__init__.py` |

**DOCX renderer (Session 5 + Session 24 slim; pipeline, fallback_media, template_structure, CLI in __main__):**

| Lines | File |
| -----:| ------ |
| 394 | `tools/docx_renderer/table_cell/fill_cell.py` |
| 87 | `tools/docx_renderer/table_cell/fill_cell_cleanup.py` |
| 35 | `tools/docx_renderer/table_cell/section_mappings.py` |
| 359 | `tools/docx_renderer/table_cell/fill_day.py` |
| 273 | `tools/docx_renderer/hyperlink_placement.py` |
| 240 | `tools/docx_renderer/render_pipeline.py` |
| 214 | `tools/docx_renderer/table_cell/placement.py` |
| 186 | `tools/docx_renderer/table_cell/format.py` |
| 165 | `tools/docx_renderer/renderer.py` |
| 155 | `tools/docx_renderer/style.py` |
| 120 | `tools/docx_renderer/fallback_media.py` |
| 48 | `tools/docx_renderer/template_structure.py` |
| 48 | `tools/docx_renderer/table_cell/__init__.py` |
| 35 | `tools/docx_renderer/inject_inline.py` |
| 29 | `tools/docx_renderer/__main__.py` |
| 15 | `tools/docx_renderer/table_cell/fill.py` |
| 14 | `tools/docx_renderer/get_indices.py` |
| 8 | `tools/docx_renderer/__init__.py` |

**Session 25 (json_repair, lesson_schema_models, docx_utils under 400 LOC):**

| Lines | File |
| -----:| ------ |
| 372 | `tools/json_repair_fixes.py` |
| 408 | `tools/docx_style_utils.py` |
| 344 | `backend/lesson_schema_models.py` |
| 202 | `tools/json_repair.py` |
| 164 | `backend/lesson_schema_vocabulary.py` |
| 155 | `tools/docx_utils.py` |
| 65 | `backend/lesson_schema_support.py` |

**DOCX parser (Session 6, post package extraction):**

| Lines | File |
| -----:| ------ |
| 364 | `tools/docx_parser/parser.py` |
| 307 | `tools/docx_parser/images_metadata.py` |
| 250 | `tools/docx_parser/content_sections.py` |
| 194 | `tools/docx_parser/slot_extraction.py` |
| 135 | `tools/docx_parser/structure.py` |
| 76 | `tools/docx_parser/no_school.py` |
| 70 | `tools/docx_parser/table_extraction.py` |
| 7 | `tools/docx_parser/__init__.py` |

**Database (Session 7 + Session 26 metrics slim):**

| Lines | File |
| -----:| ------ |
| 394 | `backend/database/metrics.py` |
| 115 | `backend/database/metrics_aggregate.py` |
| 394 | `backend/database/sqlite_impl.py` |
| 281 | `backend/database/plans.py` |
| 166 | `backend/database/users.py` |
| 164 | `backend/database/lesson_mode.py` |
| 154 | `backend/database/slots.py` |
| 125 | `backend/database/schedule.py` |
| 87 | `backend/database/engine.py` |
| 66 | `backend/database/get_db.py` |
| 59 | `backend/database/lesson_steps.py` |
| 14 | `backend/database/__init__.py` |

**Orchestrator (Session 13, post split):**

| Lines | File |
| -----:| ------ |
| 472 | `tools/batch_processor_pkg/orchestrator.py` |

**Week flow (Session 22, post split):**

| Lines | File |
| -----:| ------ |
| 216 | `tools/batch_processor_pkg/week_flow.py` |
| 187 | `tools/batch_processor_pkg/week_flow_sequential.py` |
| 174 | `tools/batch_processor_pkg/week_flow_load.py` |
| 139 | `tools/batch_processor_pkg/week_flow_parallel.py` |
| 81 | `tools/batch_processor_pkg/week_flow_existing.py` |
| 76 | `tools/batch_processor_pkg/week_flow_merge_render.py` |

**Session 26 (batch_processor_pkg extraction, signatures):**

| Lines | File |
| -----:| ------ |
| 313 | `tools/batch_processor_pkg/extraction.py` |
| 201 | `tools/batch_processor_pkg/extraction_primary_file.py` |
| 336 | `tools/batch_processor_pkg/signatures.py` |
| 252 | `tools/batch_processor_pkg/signature_table_fill.py` |

**Slot flow (Session 20, post split):**

| Lines | File |
| -----:| ------ |
| 343 | `tools/batch_processor_pkg/slot_flow.py` |
| 421 | `tools/batch_processor_pkg/slot_flow_extract.py` |
| 123 | `tools/batch_processor_pkg/slot_flow_resolve.py` |
| 158 | `tools/batch_processor_pkg/slot_flow_transform.py` |

**Lesson steps generator (Session 21, post split):**

| Lines | File |
| -----:| ------ |
| 138 | `backend/services/lesson_steps_generator.py` |
| 228 | `backend/services/lesson_steps/slot_data.py` |
| 182 | `backend/services/lesson_steps/vocab_frames_steps.py` |
| 156 | `backend/services/lesson_steps/phase_steps.py` |
| 101 | `backend/services/lesson_steps/plan_resolve.py` |
| 1 | `backend/services/lesson_steps/__init__.py` |

**Session 26 (diagnostics analyze_objectives_layout):**

| Lines | File |
| -----:| ------ |
| 399 | `tools/diagnostics/analyze_objectives_layout.py` |
| 95 | `tools/diagnostics/objectives_layout_heights.py` |

**Plans router (Session 14, post split):**

| Lines | File |
| -----:| ------ |
| 406 | `backend/routers/plans.py` |
| 346 | `backend/routers/lesson_steps.py` |
| 247 | `backend/routers/lesson_mode.py` |
| 880 | `backend/services/lesson_steps_generator.py` |

**Users router (Session 15 + Session 26 slim):**

| Lines | File |
| -----:| ------ |
| 387 | `backend/routers/users.py` |
| 108 | `backend/routers/users_list_logic.py` |
| 380 | `backend/routers/schedule.py` |
| 272 | `backend/routers/slots.py` |

**Supabase database (Session 9b, post package split):**

| Lines | File |
| -----:| ------ |
| 256 | `backend/supabase/database/slots.py` |
| 253 | `backend/supabase/database/metrics.py` |
| 200 | `backend/supabase/database/lesson_mode.py` |
| 190 | `backend/supabase/database/users.py` |
| 145 | `backend/supabase/database/plans.py` |
| 139 | `backend/supabase/database/lesson_steps.py` |
| 117 | `backend/supabase/database/schedule.py` |
| 57 | `backend/supabase/database/__init__.py` |
| 7 | `backend/supabase/database/exceptions.py` |

**Combine (Session 16, post split):**

| Lines | File |
| -----:| ------ |
| 784 | `tools/batch_processor_pkg/combine_render.py` |
| 233 | `tools/batch_processor_pkg/combine.py` |
| 196 | `tools/batch_processor_pkg/originals_json.py` |

**Sentence frames (Session 17, post split):**

| Lines | File |
| -----:| ------ |
| ~230 | `backend/services/sentence_frames_pdf_generator.py` (facade) |
| ~230 | `backend/services/sentence_frames/extraction.py` |
| ~280 | `backend/services/sentence_frames/html_builder.py` |
| ~75 | `backend/services/sentence_frames/pdf_renderer.py` |
| ~280 | `backend/services/sentence_frames/docx_renderer.py` |

**Objectives (Session 17, post split):**

| Lines | File |
| -----:| ------ |
| ~180 | `backend/services/objectives_printer.py` (facade) |
| ~100 | `backend/services/objectives/subject_parsing.py` |
| ~120 | `backend/services/objectives/extraction.py` |
| ~180 | `backend/services/objectives/formatting.py` |
| ~45 | `backend/services/objectives/printing.py` |
| ~230 | `backend/services/objectives/font_calculation.py` |
| ~280 | `backend/services/objectives/docx_renderer.py` |

### 0.6 Session 8 plan: Combined-original DOCX styles (Priority 8)

**Branch:** `refactor/combined-original-styles`  
**Reference:** `docs/ERROR_ANALYSIS_COMBINED_ORIGINAL_STYLES.md`

**Goal:** Eliminate or reliably avoid the Word "Styles 1" / "unreadable content" error on `combined_originals_*.docx` by completing style conflict handling and validating output.

**Current state:**
- Combined original flow lives in `tools/batch_processor_pkg/combined_original.py` (`generate_combined_original_docx`) and `tools/batch_processor_pkg/combine.py` (`merge_docx_files`).
- Per-sub-doc: strip (problematic elements, headers/footers, sections, custom styles), then `normalize_styles_from_master(style_master, sub_doc)`; reload from `_normalized_stream` when file-based fallback was used; save temp file.
- Merge uses template-only master (template loaded, body cleared, then each temp file appended via docxcompose). **No post-merge style fix is applied to the final merged document.**
- `tools/docx_utils.py`: `normalize_styles_from_master`, `normalize_styles_via_file`, `diagnose_style_conflicts` exist; ERROR_ANALYSIS notes logs still show ~15 style conflicts and normalization completion may not always run or persist into the final file.

**Planned steps:**

1. **Post-merge style normalization (final document)**  
   After `merge_docx_files(..., master_template_path=template)` writes the output file, load the merged DOCX, replace its styles (and optionally numbering) with the template’s using the existing file-based path (`normalize_styles_via_file` or equivalent), then save over the output path. Implement either:
   - in `combine.merge_docx_files`: optional post-save step when `master_template_path` is set (load output, normalize from template, save), or  
   - in `combined_original.generate_combined_original_docx`: after `processor._merge_docx_files(...)`, load `output_path`, run normalization from template, save.  
   Prefer a single place (SSOT) and minimal API surface; document the choice in ERROR_ANALYSIS.

2. **Ensure normalization runs and is visible**  
   - Confirm `normalize_styles_from_master` (and file-based fallback) runs for every sub-doc and that `_normalized_stream` reload is used when set.  
   - Optionally call `diagnose_style_conflicts(style_master, sub_doc)` before normalizing a sub-doc (or once per run) and log at DEBUG/INFO so future debugging is easy.  
   - Add or keep one WARNING/INFO log when the **final** post-merge style replacement runs (success/failure).

3. **Style checks and tests**  
   - Add or extend a test that builds a small combined_original DOCX (e.g. 2 plans, mocked or fixture data), then either: (a) opens it with python-docx and asserts style count or key style IDs match template, or (b) runs a small script that opens the file and checks for duplicate/broken style definitions.  
   - Optionally add a test that calls `diagnose_style_conflicts` and `normalize_styles_via_file` on two in-memory documents and asserts conflict count drops or styles match after normalize.

4. **One full combine pass**  
   - Run the full batch pipeline (or the combined-original path only) for one real week; open the generated `combined_originals_*.docx` in Word and confirm no "Styles 1" / "unreadable content" dialog (or document any remaining edge case in ERROR_ANALYSIS).

5. **Update ERROR_ANALYSIS**  
   - Set "Implementation Status" to reflect post-merge fix and any remaining knowns.  
   - Note where post-merge normalization is implemented (file and function).

**Success criteria (merge to master):**
- Post-merge style normalization is applied to the final combined document.
- Style checks and one full combine pass pass; no (or documented) Word errors on the generated file.
- No regressions in existing combined-original or merge tests (e.g. `test_combined_original_export.py`, any merge tests).

**Tools:** Manual edits and existing `docx_utils` helpers; no new refactoring library required.

### 0.7 Session 10 plan: Frontend Analytics (Priority 10)

**Branch:** `refactor/frontend-analytics`  
**Reference:** [docs/planning/CRITICAL_REVIEW_AND_CORRECTIONS.md](docs/planning/CRITICAL_REVIEW_AND_CORRECTIONS.md) (Hide Advanced Analytics)

**Goal:** Move Analytics to Settings/Admin and split `frontend/src/components/Analytics.tsx` into subcomponents and a `useAnalytics` hook; keep main nav focused on workflow.

**Implemented (on branch):**
- **Settings/Admin view:** Top-level nav "Settings" (replaces Analytics and Database). Settings page has sub-tabs: User & Sync (SupabaseSyncToggle, SyncTestButton), Database (DatabaseSettings), Analytics (Analytics dashboard).
- **Analytics package:** `frontend/src/components/analytics/` with `useAnalytics.ts` (state, fetch, export, formatters, derived chart data), `AnalyticsHeader.tsx`, `SummaryCards.tsx`, `ErrorBreakdown.tsx`, `ModelChart.tsx`, `WorkflowChart.tsx`, `DailyChart.tsx`, `OperationsTable.tsx`, `ParallelStats.tsx`, `SessionTable.tsx`, `index.tsx` (AnalyticsView container). `frontend/src/components/Analytics.tsx` re-exports from `./analytics/index` so existing lazy imports unchanged.
- **Nav:** DesktopNav shows Settings (not Analytics or Database). Unified App `case 'settings'` with sub-tabs; `case 'analytics'` and `case 'database'` removed.

**Success criteria (merge to master):**
- Analytics reachable only via Settings > Analytics.
- Frontend build passes (Analytics-related code compiles; pre-existing TS errors in other packages may remain).
- Analytics smoke: open Settings, Analytics tab, select user, load data, change time range, export CSV.
- No regressions in main workflow (Home, Plans, Schedule, Browser, History).

**Tools:** Manual edits; no refactoring library.

### 0.8 Session 11 plan: BatchProcessor.tsx refactor (Priority 11)

**Branch:** `refactor/batch-processor-tsx`  
**Reference:** This document, Session 11 (Priority 11).

**Goal:** Extract week/slot selection, progress display, and error handling from `BatchProcessor.tsx` into a `useBatchProcessor` hook and subcomponents; keep `BatchProcessor.tsx` as a thin re-export so the batch UI is maintainable and testable.

**Implemented (on branch):**
- **Hook:** `frontend/src/components/batch_processor/useBatchProcessor.ts` — state, effects, handlers, derived values (`progressPercentage`, `sortedSlots`); types `ButtonState`, `WeekStatus`, `RecentWeek`, `ProcessResult`.
- **Subcomponents:** `WeekSection.tsx` (week input, recent weeks, Generate button), `ProgressSection.tsx` (progress bar when processing), `BatchAlerts.tsx` (error, success, partial-failure alerts), `SlotSection.tsx` (slot list, Select All/Deselect All, done/force badges), `ConfirmDialog.tsx` (source folder, week, partial/missingOnly, slot count, Cancel/Proceed).
- **Container:** `batch_processor/index.tsx` — `BatchProcessorView` composes hook + subcomponents; no-user and no-slots early returns in container.
- **Re-export:** `frontend/src/components/BatchProcessor.tsx` re-exports `BatchProcessorView as BatchProcessor` from `./batch_processor` so existing imports unchanged.

**Success criteria (merge to master):**
- Week/slot selection, progress display, and error handling live in dedicated hook + subcomponents; `BatchProcessor.tsx` is a thin re-export.
- Frontend build passes (batch_processor code compiles; pre-existing TS errors in other packages may remain).
- Batch UI smoke: open Batch view, choose week (manual + recent), select/deselect slots, open confirm dialog, run generate (or mock); no console errors or broken layout.
- No regressions in main workflow (Home, Plans, Schedule, Browser, History).

**Tools:** Manual edits; no refactoring library.

### 0.9 Session 13 plan: Orchestrator split (Priority 13)

**Branch:** `refactor/orchestrator-split`  
**Reference:** This document, Session 13 (Priority 13).

**Goal:** Split `tools/batch_processor_pkg/orchestrator.py` by phase so the batch pipeline stays testable and maintainable; public API unchanged.

**Implemented (on branch):**
- **slot_flow.py:** Single-slot orchestration extracted from `_process_slot` into `process_one_slot(processor, ...)` (resolve file, extract, transform, persist). Orchestrator `_process_slot` delegates to it.
- **week_flow.py:** Week-level orchestration extracted from `process_user_week` into `run_process_user_week(processor, ...)` (load user/slots, enrich, parallel or sequential, combine, result dict). Orchestrator `process_user_week` delegates to it.
- **orchestrator.py:** Thin coordinator; holds `BatchProcessor`, `process_batch`, and thin delegate methods; exposes `get_db`, `get_file_manager` on processor for flow modules. Line counts in **0.5**.

**Success criteria (merge to master):**
- Public API unchanged: `from tools.batch_processor import BatchProcessor, process_batch, SlotProcessingContext`.
- Batch-processor and batch-pipeline tests pass (no new failures).
- Orchestrator under ~600 lines; week_flow and slot_flow hold the extracted logic.

**Tools:** Manual edits; no refactoring library.

---

## 1. Refactoring and fix priorities

Priorities are ordered by impact and risk. Do high-priority items on a branch; run focused tests before and after.

### 1.1 High priority (stability and maintainability)


| Priority | Item                                                 | Location / reference                                                         | Notes                                                                                                                                                                        |
| -------- | ---------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1        | **Split `backend/api.py`** (~4,200 lines)            | `backend/api.py`                                                             | Single FastAPI app with all routes. Split into routers by domain: users, plans, process-week, analytics, settings, health. Reduces merge conflicts and clarifies ownership.  |
| 2        | **Refactor `backend/llm_service.py`** (done; 789 lines) | `backend/llm_service.py`, `backend/llm/`                                     | Done: prompt_builder, validation, providers, schema, parse_llm_response, post_process, domain_analysis in `backend/llm/`. See **0.5** for line counts per file. |
| 3        | **PerformanceTracker simplification** (done)         | `docs/planning/CRITICAL_REVIEW_AND_CORRECTIONS.md`                           | Done: retention 30 days, cleanup on init, sampling + debug_mode (DEBUG_PERFORMANCE_TRACKING), critical ops (batch_process, plan_generation, llm_call, llm_api_call); retention/sampling/debug_mode tests; SQLite WAL for file DBs. |
| 4        | **Fix remaining test suite collection errors**       | `docs/fix/DATABASE_PROBLEMS.md` (done); TestClient, test_api_endpoints, etc. | Database import fixed. Still to fix: TestClient API, test_api_endpoints module-level code, test_week_calculation first_date format, DOCX paths, backend_connection sys.exit. |


### 1.2 Medium priority (large files, clear boundaries)


| Priority | Item                                              | Location                                          | Notes                                                                                                                                                |
| -------- | ------------------------------------------------- | ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| 5        | **Split `tools/docx_renderer`** (done)             | `tools/docx_renderer/`                            | Done: package with style.py, hyperlink_placement.py, renderer.py, table_cell package (fill, format, placement). Merged to master (Session 5). Line counts in **0.5**. |
| 6        | **Split `tools/docx_parser.py`** (done; was ~2,146 lines) | `tools/docx_parser/`                            | Done: package with structure.py, no_school.py, table_extraction.py, content_sections.py, slot_extraction.py, images_metadata.py, parser.py, parse_docx; public API unchanged. Line counts in **0.5**. |
| 7        | **Split `backend/database.py`** (done)             | `backend/database/`                               | Done: package with engine, users, slots, plans, metrics, schedule, lesson_steps, lesson_mode, sqlite_impl, get_db; single get_db() and interface. Line counts in **0.5**. |
| 8        | **Combined-original DOCX styles**                 | `docs/ERROR_ANALYSIS_COMBINED_ORIGINAL_STYLES.md` | Refactor rendering/merge so style conflicts are avoided or cleaned up post-merge.                                                                    |
| 9        | **Supabase database module** (done)                | `backend/supabase/`                               | Done: auth (client creation, verify_schema), query_helpers (serialization/hydration), sync (sync_users_to_supabase), client (get_project1_db, get_project2_db), database (SupabaseDatabase); facade supabase_database.py. |


### 1.3 Lower priority (polish and cleanup)


| Priority | Item                           | Location                                                   | Notes                                                                                                      |
| -------- | ------------------------------ | ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| 10       | **Frontend Analytics**         | `frontend/src/components/Analytics.tsx` (~770 lines)       | Move to Settings/Admin; split into subcomponents and hooks (charts, filters, export). See CRITICAL_REVIEW. |
| 11       | **BatchProcessor.tsx**         | `frontend/src/components/BatchProcessor.tsx` (~560 lines)  | Extract: week/slot selection, progress display, error handling into smaller components/hooks.              |
| 12       | **Root decluttering**          | `docs/implementation/ROOT_DECLUTTERING_PLAN.md`            | Archive root-level docs and scripts; organize into `docs/archive/`, `tools/`, etc.                         |
| 13       | **Orchestrator further split** | `tools/batch_processor_pkg/orchestrator.py` (~2,560 lines) | Already in package. Optional: split by phase (extract / transform / combine / render) if adding features.  |


### 1.4 Done (for reference)

- **Batch processor package** — `tools/batch_processor.py` → `tools/batch_processor_pkg/` (see `BATCH_PROCESSOR_REFACTOR.md`).
- **Database alias and optional db_path** — `Database = SQLiteDatabase`, `SQLiteDatabase(db_path=...)` for tests/migrations (see `docs/fix/DATABASE_PROBLEMS.md`).
- **Test suite collection (Session 1)** — Branch `fix/test-suite-collection`: conftest `client` fixture and isolated DB fixture; httpx<0.28; script-style tests converted; DB tests use Session/engine APIs; DOCXRenderer row constants and None guards. Pytest collects 654+ tests with 0 collection errors.
- **Split backend/api.py (Session 2)** — Branch `refactor/split-api`; routers by domain: health, settings, users, plans, process-week, analytics; app mounts all six routers; duplicate analytics routes removed; API/smoke tests pass (same pre-existing failures as baseline).
- **api.py core router and lifespan** — Pipeline routes moved to `backend/routers/core.py` (validate, render, progress, transform, repair, tablet export); FastAPI lifespan context manager replaces on_event startup/shutdown; `enrich_lesson_json_with_times` in `backend/utils/lesson_times.py`; GET plan download in plans router; `tools/batch_processor_pkg/combine.py` and scripts import from `backend.utils.lesson_times`.
- **Refactor llm_service (Session 3)** — Branch `refactor/llm-service` (merged); extracted to `backend/llm/`: prompt_builder, validation, providers, schema, parse_llm_response (validation), post_process, domain_analysis; `llm_service.py` 789 lines (was ~1,247). Line counts: see **0.5**. LLM tests updated and pass.
- **PerformanceTracker simplification (Session 4)** — Branch `refactor/performance-tracker`; retention 30 days, cleanup on init, sampling + debug_mode (env DEBUG_PERFORMANCE_TRACKING), critical ops include llm_api_call; retention/sampling/debug_mode tests in test_performance_tracker.py; SQLite WAL for file-based DBs in database.py.
- **DOCX renderer package (Session 5)** — Branches `refactor/docx-renderer` and `refactor/docx-renderer-table-cell` merged to master. `tools/docx_renderer.py` replaced by package `tools/docx_renderer/` with style.py, hyperlink_placement.py, renderer.py, table_cell package (fill, format, placement, __init__.py); public API unchanged. Line counts in **0.5**.
- **Slim docx_renderer/renderer.py (Session 24)** — Branch `refactor/slim-docx-renderer-renderer`; merged to master. Extracted get_* to get_indices.py; fallback_media.py (append_unmatched_media, insert_images); template_structure.py (initialize_structure); render_pipeline.py (run_render_pipeline); CLI moved to __main__.py. renderer.py ~165 lines (facade + delegates). Line counts in **0.5**.
- **DOCX parser package (Session 6)** — Branch `refactor/docx-parser`. `tools/docx_parser.py` (2,146 lines) replaced by package `tools/docx_parser/` with structure.py, no_school.py, table_extraction.py, content_sections.py, slot_extraction.py, images_metadata.py, parser.py, parse_docx; public API (DOCXParser, parse_docx, validate_slot_structure) unchanged. Parser/slot/subject/no_school tests pass.
- **Database package (Session 7)** — Branch `refactor/database-split`. `backend/database.py` (1,676 lines) replaced by package `backend/database/` with engine.py, users.py, slots.py, plans.py, metrics.py, schedule.py, lesson_steps.py, lesson_mode.py, sqlite_impl.py, get_db.py; single get_db() and DatabaseInterface preserved; DB/API/user_profiles/performance_tracker tests pass. Line counts in **0.5**.
- **Combined-original styles (Session 8)** — Branch `refactor/combined-original-styles`. Post-merge style normalization in `combined_original.generate_combined_original_docx` (normalize_styles_via_file after merge); docProps/custom.xml and docProps/core.xml added to replacement in docx_utils; module logger `_log` in docx_utils; tests/test_docx_utils_styles.py and combined-original style check; hyperlink Times New Roman 8pt in markdown_to_docx._add_hyperlink; Supabase fallback log-once in users router; ERROR_ANALYSIS updated.
- **Supabase module (Session 9)** — Branch `refactor/supabase-module`. Package `backend/supabase/`: auth (create_supabase_client, verify_schema), query_helpers (normalize_day, serialize/hydrate lesson step and session payloads), sync (sync_users_to_supabase, get_target_projects, etc.), client (get_project1_db, get_project2_db), database (SupabaseDatabase, exceptions); `backend/supabase_database.py` facade re-exports; tools/sync_users_to_supabase.py uses backend.supabase.sync.
- **Supabase database package split (Session 9b)** — Single file `backend/supabase/database.py` (1,306 lines) replaced by package `backend/supabase/database/` with mixins: users.py, slots.py, plans.py, metrics.py, schedule.py, lesson_steps.py, lesson_mode.py, exceptions.py; `SupabaseDatabase` in `__init__.py` inherits all mixins and `DatabaseInterface`; public API unchanged. Line counts in **0.5**.
- **Frontend Analytics (Session 10)** — Branch `refactor/frontend-analytics`. Analytics moved to Settings/Admin (sub-tabs: User & Sync, Database, Analytics); top-level nav Analytics and Database replaced by Settings. Analytics split into `frontend/src/components/analytics/`: useAnalytics hook, AnalyticsHeader, SummaryCards, ErrorBreakdown, ModelChart, WorkflowChart, DailyChart, OperationsTable, ParallelStats, SessionTable; Analytics.tsx re-exports. ErrorBreakdown copy and failure-type labels clarified.
- **BatchProcessor.tsx refactor (Session 11)** — Branch `refactor/batch-processor-tsx`. BatchProcessor.tsx split into `frontend/src/components/batch_processor/`: useBatchProcessor hook, WeekSection, ProgressSection, BatchAlerts, SlotSection, ConfirmDialog; BatchProcessor.tsx re-exports BatchProcessorView.
- **Root decluttering (Session 12)** — Branch `refactor/root-declutter`. Root archived/organized per ROOT_DECLUTTERING_PLAN; docs to docs/archive/root-documentation, logs to logs/archive, test files to docs/archive/test-files, Python scripts to tools/archive/root-scripts, batch/PowerShell to docs/archive/scripts; CONTRIBUTING and ROOT_ARCHIVE_INDEX updated; links/scripts verified.
- **Orchestrator split (Session 13)** — Branch `refactor/orchestrator-split`. week_flow.py (run_process_user_week), slot_flow.py (process_one_slot); orchestrator thin coordinator; get_db/get_file_manager on processor; public API unchanged. Line counts in **0.5**.
- **Plans router split (Session 14)** — Branch `refactor/plans-router-split`. lesson_mode.py (5 endpoints), lesson_steps.py (get/generate), lesson_steps_generator.py service; plans.py slim (plan detail, download, user plans, week status). API/slot tests pass. Merged to master; pushed to origin. Post-merge fix (commit 2793ffa): build-apk.ps1 restored at repo root, TabletSync APK build status message clarified, lesson-steps API test expects 4 steps.
- **Users router split (Session 15)** — Branch `refactor/users-router-split`. backend/routers/users.py split into users.py (user CRUD only), slots.py (class slots), schedule.py (schedule entries); all mounted in api.py with prefix /api; conftest get_db patches for slots and schedule. API/slot tests pass. Line counts in **0.5**.
- **Combine.py split (Session 16)** — Branch `refactor/combine-split`. originals_json.py (convert_originals_to_json, reconstruct_slots_from_json), combine_render.py (_render_single_slot, _render_multi_slot); combine.py slim (merge_docx_files, combine_lessons, combine_lessons_impl, re-exports). Batch_processor/originals/combined_original tests pass. Line counts in **0.5**.
- **Sentence frames + objectives_printer split (Session 17)** — Branch `refactor/sentence-frames-objectives-split`. sentence_frames_pdf_generator split into `backend/services/sentence_frames/` (extraction, html_builder, pdf_renderer, docx_renderer); objectives_printer split into `backend/services/objectives/` (subject_parsing, extraction, formatting, printing, font_calculation, docx_renderer). Facades preserve public API; sentence-frames and objectives tests pass. See **0.5** for line counts.
- **ScheduleInput + SlotConfigurator refactor (Session 18)** — Branch `refactor/schedule-slot-frontend`. ScheduleInput split into `frontend/src/components/schedule_input/`: useScheduleInput hook, ScheduleInputHeader, ScheduleInputTable, ScheduleColorLegend, NoUserSchedule; SlotConfigurator split into `frontend/src/components/slot_configurator/`: useSlotConfigurator hook, SortableSlotItem; ScheduleInput.tsx and SlotConfigurator.tsx re-exports. Public API unchanged. Smoke-tested: schedule and slots tabs OK.
- **table_cell/fill.py split (Session 19)** — Branch `refactor/fill-py-split`; merged to master. fill.py (956 lines) split into fill_metadata.py (fill_metadata), fill_day.py (fill_day, fill_single_slot_day, fill_multi_slot_day, _format_slot_field), fill_cell.py (fill_cell); fill.py re-exports. table_cell public API unchanged; docx_renderer tests (7/9 pass; 2 pre-existing failures unrelated to fill).
- **slot_flow split (Session 20)** — Branch `refactor/slot-flow-split`. slot_flow.py split into slot_flow_resolve.py (resolve_primary_file, raise_no_primary_file_error, open_parser_for_slot), slot_flow_extract.py (find_slot_number, extract_media_for_slot, extract_content_for_slot, no_school builders, content helpers), slot_flow_transform.py (run_llm_transform, finalize_lesson_json); slot_flow.py slim orchestrator; process_one_slot public API unchanged. Batch processor and slot tests pass.
- **lesson_steps_generator split (Session 21)** — Branch `refactor/lesson-steps-generator-split`. lesson_steps_generator.py split into backend/services/lesson_steps/ (plan_resolve, slot_data, phase_steps, vocab_frames_steps); facade lesson_steps_generator.py; generate_lesson_steps public API unchanged. API and DB tests pass.
- **week_flow split (Session 22)** — Branch `refactor/week-flow-split`. week_flow.py split into week_flow_load.py (user/slots/schedule enrich), week_flow_existing.py (existing plan + missing_only), week_flow_parallel.py (parallel extract/transform/collect), week_flow_sequential.py (sequential loop), week_flow_merge_render.py (merge + combine/render); week_flow.py slim orchestrator; run_process_user_week public API unchanged. API and batch_processor facade tests pass.
- **llm_service split (Session 23)** — Branch `refactor/llm-service-split`. backend/llm_service.py slimmed: api_key resolution in backend/llm/api_key.py, token limits in backend/llm/token_limits.py, transform loop in backend/llm/transform_runner.py; LLMService and get_llm_service() public API unchanged. LLM and validation tests pass.
- **json_repair under 400 LOC (Session 25)** — Branch `refactor/slim-tools-json-repair`. Control-char, unescaped-quotes, truncation helpers extracted to tools/json_repair_fixes.py; json_repair.py ~202 lines. Public API unchanged.
- **lesson_schema_models under 400 LOC (Session 25)** — Branch `refactor/slim-backend-lesson-schema-models`. Vocabulary/sentence-frames/homework -> backend/lesson_schema_vocabulary.py; SupportsByLevel/BilingualOverlay -> backend/lesson_schema_support.py; lesson_schema_models.py ~344 lines. Re-exports preserved.
- **docx_utils under 400 LOC (Session 25)** — Branch `refactor/slim-tools-docx-utils`. Style normalization (normalize_styles_via_file, normalize_styles_from_master, _normalize_styles_via_api, diagnose_style_conflicts) -> tools/docx_style_utils.py; docx_utils.py ~155 lines. Public API unchanged.
- **fill_cell under 400 LOC (Session 26)** — Branch `refactor/slim-table-cell-fill-cell`. section_mappings.py (SECTION_MAPPINGS, section_matches), fill_cell_cleanup.py (remove_duplicate_coordinate_hyperlinks); fill_cell.py ~394 lines.
- **extraction under 400 LOC (Session 26)** — Branch `refactor/slim-batch-processor-pkg-extraction`. resolve_primary_file + _safe_get -> extraction_primary_file.py; extraction.py ~313 lines.
- **signatures under 400 LOC (Session 26)** — Branch `refactor/slim-batch-processor-pkg-signatures`. add_signature_image_to_table, add_user_name_to_table -> signature_table_fill.py; signatures.py ~336 lines.
- **analyze_objectives_layout under 400 LOC (Session 26)** — Branch `refactor/slim-diagnostics-analyze-objectives-layout`. calculate_estimated_heights -> objectives_layout_heights.py; analyze_objectives_layout.py ~399 lines.
- **users router under 400 LOC (Session 26)** — Branch `refactor/slim-routers-users`. fetch_active_users (Supabase + SQLite fallback, dedupe, filter) -> users_list_logic.py; users.py ~387 lines.
- **metrics under 400 LOC (Session 26)** — Branch `refactor/slim-database-metrics`. get_aggregate_stats -> metrics_aggregate.py; metrics.py ~394 lines.

*(New refactors: track branches, commits, and merges in **Section 0** above; add a one-line bullet here when each is merged to master.)*

---

## 2. Python refactoring libraries: when they help

The libraries below can make refactoring **safer** (fewer missed renames/imports), **faster** (scripted or IDE-driven changes), and **more efficient** (repeatable patterns across many files). Use them as recommended so each session benefits from tooling instead of manual-only edits.

Automated refactoring tools are useful for **mechanical, repeated changes** (renames, simple extractions, syntax migrations). They are **not** a substitute for **structural refactors** (splitting a 4,000-line file into modules, redesigning APIs). Use tools where they clearly save time and reduce errors; otherwise prefer IDE refactors and manual edits with tests.

**AST vs CST:** Tools that use an **Abstract Syntax Tree** (e.g. Rope) are good for analysis and renames but can lose comments/whitespace. **Concrete Syntax Tree** tools (Bowler, LibCST) preserve formatting, comments, and style, which keeps diffs cleaner and reduces merge noise. Prefer CST-based tools when doing scripted transforms across many files so version control stays readable.

### 2.1 Rope

- **What it is:** Refactoring library (rename, move, extract variable/function, change signature, organize imports). AST-based; often used via IDE or LSP. Mature (rope on GitHub, actively maintained).
- **When it helps:** Safe **rename** across a project (symbols, modules, parameters). **Extract method/variable** in a single file. **Move** module/package with import updates. Good for incremental renames after an API change.
- **When it does not:** Splitting a large file into multiple modules (you still design and move code by hand). Complex semantic changes (e.g. changing how two modules interact). Rope does not understand your runtime or tests.
- **IDE / LSP:** **pylsp-rope** plugs into Python LSP Server and adds LSP rename (variables, classes, functions); install in the same virtualenv as `python-lsp-server` so it auto-discovers. Some Rope features are not yet exposed via LSP; expect occasional limitations. For VS Code, use PyLSP with pylsp-rope rather than the older standalone Rope extension.
- **Recommendation:** Use **IDE integration** (PyCharm, or VS Code with pylsp-rope) for renames and extract in daily work. Use the **Rope API** only if you need scripted renames (e.g. “rename X to Y in 50 files”) and your IDE cannot do it. Do not add Rope as a mandatory CI step unless you have a concrete scripted refactor.
- **Links:** [Rope](https://rope.readthedocs.io/), [pylsp-rope](https://github.com/python-rope/pylsp-rope).

### 2.2 Bowler

- **What it is:** Refactoring tool built on `lib2to3` (standard library); fluent API and CLI for scripted, composable changes. Uses a **CST**-style approach: preserves formatting, comments, and whitespace, so version-control diffs stay clean.
- **When it helps:** **Scripted, repeatable transforms** (e.g. “replace pattern A with B in 100 files”, “add a parameter to all calls of function X”). Good when you can express the change as a query + transform and want to run it as a one-off or in a script.
- **When it does not:** One-off manual refactors (IDE is faster). Structural splits (Bowler does not decide how to split a file). Very complex or context-dependent changes that need human judgment.
- **Why use it:** Designed for **reusable refactoring scripts** and “future ready”: built on stdlib so new Python versions are often supported early without waiting for the tool to update. Backward compatible.
- **Recommendation:** Consider Bowler when you have a **clear, mechanical pattern** to apply across many files (e.g. standardizing a call signature, updating imports after a move). Write a small script, run it, then review diffs and run tests. Do not use for “exploratory” or design-heavy refactors.
- **Links:** [Bowler](https://pybowler.io/).

### 2.3 LibCST and codemods

- **What it is:** Library that parses Python to a **Concrete Syntax Tree** (preserves comments/whitespace). Includes a **codemod** framework for multi-file transforms with metadata and multi-pass support.
- **When it helps:** **Large-scale, automated migrations** (e.g. `.format()` → f-strings, replacing magic values with constants, project-wide syntax or style changes). When you need to preserve formatting and run the same transform across the repo.
- **When it does not:** Small refactors (overhead not justified). Structural redesign (splitting modules, changing architecture). One-off edits (direct LibCST or even search-replace is enough).
- **Usage:** Initialize with `python3 -m libcst.tool initialize` (creates `.libcst.codemod.yaml` for formatter integration, blacklists, etc.). Run a codemod with `python3 -m libcst.tool codemod <CodemodName> <path>`. Built-in codemods exist (e.g. `ConvertFormatStringCommand` for `.format()` → f-strings). Review diff and run tests after each run.
- **Recommendation:** Use **LibCST codemods** when you have a **defined, repeatable migration** (e.g. “we are standardizing on pattern X in 200 files”). For most “refactor this big file” work in this repo, manual extraction with tests is simpler and safer. Add LibCST only if you commit to writing and maintaining codemod scripts.
- **Links:** [LibCST](https://libcst.readthedocs.io/), [Codemods](https://libcst.readthedocs.io/en/latest/codemods.html).

### 2.4 Refex (optional, expression-level patterns)

- **What it is:** Syntactically aware search-and-replace for Python using AST (with token preservation via asttokens). Template-based patterns (e.g. `$x.foo()` → `($x.foo() + 1)`) with correct parenthesis and precedence.
- **When it helps:** **Expression-level** pattern replace across files when you need something more precise than regex but lighter than a full Bowler/LibCST script. Good for “replace this call pattern everywhere” without writing a codemod. CLI: `refex --mode=py.expr 'pattern' --sub='replacement' -i file.py`; also usable as a library.
- **When it does not:** Full refactors (rename symbol, extract method, move module). Use Rope/IDE for those. Not a replacement for Bowler/LibCST when you need multi-pass or project-wide codemods.
- **Recommendation:** Optional. Use when a session needs **targeted expression rewrites** and Refex’s template syntax fits; otherwise stick to IDE + Rope/Bowler/LibCST as in Section 3.
- **Links:** [Refex](https://refex.readthedocs.io/).

### 2.5 What not to rely on

- **Relying on LLMs for refactors:** LLMs can suggest edits but often miss call sites, imports, and tests. Use them for drafts and ideas; **run tests and review diffs** and do renames/moves with IDE or Rope/Bowler when possible.
- **Fully automated “split this file”:** No current library decides how to split a 4,000-line file into modules. That remains a design and manual edit task, with tools helping only for the mechanical parts (renames, import fixes).
- **Regex for code changes:** Plain search-replace can break syntax (e.g. wrong operator precedence, broken parentheses). Prefer Refex (expression-aware), Bowler, or LibCST for pattern-based changes so structure is preserved.

---

## 3. Suggested workflow for this repo

1. **Rename / extract in one or a few files:** Use your **IDE** (rename symbol, extract method/variable). If the IDE uses Rope (e.g. via pylsp-rope), you get safe renames across the project.
2. **Mechanical pattern across many files:** Consider a **Bowler** script or a **LibCST** codemod; run on a branch, review diff, run full test suite. For expression-level pattern replace without a full codemod, **Refex** (Section 2.4) is an option.
3. **Large-file splits and API redesign (api.py, llm_service, docx_renderer, database):** Do **manually**: create new modules, move code, fix imports, add tests. Use IDE “move to file” or “extract” only for small, local pieces.
4. **After any refactor:** Run the **focused test set** (see `BATCH_PROCESSOR_REFACTOR.md`) or full pytest; fix collection errors first so tests actually run.

---

## 4. References

- `docs/refactor/BATCH_PROCESSOR_REFACTOR.md` — Batch processor package refactor (done).
- `docs/fix/DATABASE_PROBLEMS.md` — Database alias and db_path (done).
- `docs/planning/CRITICAL_REVIEW_AND_CORRECTIONS.md` — PerformanceTracker, No School, analytics UI.
- `docs/ERROR_ANALYSIS_COMBINED_ORIGINAL_STYLES.md` — Combined-original style refactor.
- `docs/implementation/ROOT_DECLUTTERING_PLAN.md` — Root directory cleanup.
- `docs/planning/db_architecture/LOCAL_OPTIMIZATION_PLAN.md` — BatchProcessor + joblib/cache (optional).

### 4.1 LOC, git, and refactoring tools for Cursor

- **LOC and metrics:** See `docs/refactor/LOC_AND_METRICS.md`. Refresh section 0.5 with `python tools/refactor/count_loc.py` (use `--markdown` for tables).
- **Git during refactoring:** See `docs/refactor/GIT_DURING_REFACTORING.md` (branching, commits, merge; SSOT for session order remains sections 0.2 and 0.3 above).
- **Refactoring with Cursor:** When refactoring with Cursor (AI), follow `docs/refactor/REFACTORING_TOOLS_FOR_CURSOR.md` so Rope/Bowler/LibCST are used where appropriate (renames, mechanical patterns, large-file splits).
- **Priorities from LOC:** See `docs/refactor/REFACTORING_PRIORITIES_FROM_LOC.md` for analysis of top files from the LOC script and how to refactor them per this module (plans/users routers, combine.py, PDF services, etc.).


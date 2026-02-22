# Refactoring Priorities from LOC Analysis

This document analyzes the top files from `python tools/refactor/count_loc.py` and proposes how to refactor them **according to the refactoring module** ([REFACTORING_PRIORITIES_AND_TOOLS.md](REFACTORING_PRIORITIES_AND_TOOLS.md), [REFACTORING_TOOLS_FOR_CURSOR.md](REFACTORING_TOOLS_FOR_CURSOR.md), [GIT_DURING_REFACTORING.md](GIT_DURING_REFACTORING.md)). It maps each file to a strategy (manual split vs mechanical tools), suggests split boundaries, and reminds which tools to use when.

**Thresholds (from [LOC_AND_METRICS.md](LOC_AND_METRICS.md)):** >500 lines = review; >800 lines = strong split candidate.

---

## 1. Strong split candidates (>800 lines)

### 1.1 `backend/routers/plans.py` (1,885 lines) — **Done (Session 14)**

**Current shape (pre-split; now split into plans.py, lesson_mode.py, lesson_steps.py, lesson_steps_generator):** Single router with many endpoints: `get_plan_detail`, `download_plan_file`, `get_lesson_steps`, `generate_lesson_steps` (very large), `create_lesson_mode_session`, `get_active_lesson_mode_session`, `get_lesson_mode_session`, `update_lesson_mode_session_endpoint`, `end_lesson_mode_session_endpoint`, `get_user_plans`, `get_week_status`.

**Refactor strategy (per module):**

- **Large-file split / API redesign** → **Manual edits** (REFACTORING_TOOLS_FOR_CURSOR: use IDE extract only for small local pieces; design and move code by hand).
- **After extract:** Use **pylsp-rope** or Rope for any renames and import updates so call sites stay in sync.

**Proposed split:**

1. **Plans router (keep in `plans.py` or rename):** Plan CRUD/detail: `get_plan_detail`, `download_plan_file`, `get_user_plans`, `get_week_status`. Thin router that delegates to handlers or services if needed.
2. **Lesson steps router (new file or sub-router):** `get_lesson_steps`, `generate_lesson_steps`. The `generate_lesson_steps` logic is huge; extract the core logic into a **service** (e.g. `backend/services/lesson_steps_generator.py`) and keep the router thin. Use **Cursor (AI)** for the design and extraction; then **Rope/IDE** for renames and import fixes.
3. **Lesson mode router (new file or sub-router):** `create_lesson_mode_session`, `get_active_lesson_mode_session`, `get_lesson_mode_session`, `update_lesson_mode_session_endpoint`, `end_lesson_mode_session_endpoint`. Clear subdomain; can live in `backend/routers/lesson_mode.py` and be mounted under the same prefix if desired.

**Git:** One branch per refactor (e.g. `refactor/plans-router-split`). Small commits: e.g. (1) extract lesson mode routes, (2) extract lesson steps service + routes, (3) slim plans router. Run API tests and smoke after each commit (GIT_DURING_REFACTORING).

---

### 1.2 `tools/batch_processor_pkg/combine.py` (1,190 lines)

**Current shape:** `merge_docx_files`, `convert_originals_to_json`, `reconstruct_slots_from_json`, `combine_lessons`, `combine_lessons_impl`, `_render_single_slot`, `_render_multi_slot`. Merge and JSON conversion are smaller; the bulk is in combine impl and render helpers.

**Refactor strategy:**

- **Large-file split** → **Manual edits.** Bowler/LibCST are for mechanical patterns across many files; they do not decide how to split. Use **Cursor (AI)** to design the split and extract; then **Rope/IDE** for renames/imports.
- **Reusable scripts:** If after the split you standardize a pattern (e.g. import paths), consider a small Bowler script under `tools/refactor/` and run with `.diff(interactive=True)` (REFACTORING_TOOLS_FOR_CURSOR).

**Proposed split:**

1. **Merge + JSON (keep or separate):** `merge_docx_files` can stay; `convert_originals_to_json` and `reconstruct_slots_from_json` could move to e.g. `originals_json.py` in the same package so `combine.py` focuses on “combine” orchestration.
2. **Combine orchestration:** `combine_lessons`, `combine_lessons_impl` in `combine.py` (or a thin `combine.py` that imports from a new module).
3. **Render helpers:** `_render_single_slot` and `_render_multi_slot` are large; move to e.g. `combine_render.py` (or a subpackage) and import from `combine.py`. Preserve public API: `merge_docx_files`, `convert_originals_to_json`, `reconstruct_slots_from_json`, `combine_lessons` remain the contract; call sites in batch_processor_pkg and elsewhere must not break.

**Git:** Branch e.g. `refactor/combine-split`. Commits: (1) extract originals_json, (2) extract combine_render, (3) slim combine.py. Run batch_processor and combine-related tests after each step.

---

### 1.3 `backend/routers/users.py` (1,119 lines) — **Done (Session 15)**

**Current shape (pre-split; now split into users.py, slots.py, schedule.py):** Many endpoints: user CRUD, `update_user_base_path`, `update_user_template_paths`, class slots (create, get, update, delete), schedule (create, get, get_current_lesson, update, delete, bulk_create).

**Split (implemented):**

**users.py** — user CRUD, get_recent_weeks, base-path, template-paths. **slots.py** — slot CRUD. **schedule.py** — schedule CRUD + get_current_lesson + bulk_create. All mounted in api.py with prefix /api; URLs unchanged.

**Git:** Branch `refactor/users-router-split`. Conftest get_db patches for slots and schedule; API/slot tests pass.

---

### 1.4 `backend/services/sentence_frames_pdf_generator.py` (183 lines, post-split facade) — **Done (Session 17)**

**Current shape (post-split):** Facade `sentence_frames_pdf_generator.py` + subpackage `backend/services/sentence_frames/` (extraction, html_builder, pdf_renderer, docx_renderer). Public API unchanged.

**Refactor strategy:**

- **Large-file split** → **Manual edits.** Extract by responsibility (e.g. HTML building, PDF rendering, DOCX export) into separate modules or a small package; keep a thin facade or main class that composes them. **Cursor** for design and extraction; **Rope** for renames/imports.
- No Bowler/LibCST needed unless you later standardize a pattern across many files.

**Proposed split:**

1. Identify natural phases in `SentenceFramesPDFGenerator` (e.g. data prep, HTML generation, PDF/DOCX output). Extract each phase into a module (e.g. `sentence_frames_html.py`, `sentence_frames_pdf.py`, `sentence_frames_docx.py`) or a subpackage `backend/services/sentence_frames/` with a facade that preserves the current public API (`generate_sentence_frames_`*).
2. Keep the existing module-level functions as the public API; they can delegate to the new modules. Update call sites only where the facade is used; use **Rope** for any symbol renames.

**Git:** Branch e.g. `refactor/sentence-frames-pdf-split`. Commits: (1) extract HTML phase, (2) extract PDF/DOCX phases, (3) slim main class/facade. Run any sentence-frames or PDF tests.

---

### 1.5 `backend/services/objectives_printer.py` (158 lines, post-split facade) — **Done (Session 17)**

**Current shape (post-split):** Facade `objectives_printer.py` + subpackage `backend/services/objectives/` (subject_parsing, extraction, formatting, printing, font_calculation, docx_renderer). Public API unchanged.

**Refactor strategy:** Same as sentence_frames: **manual** split by phase/responsibility; **Cursor** for extraction; **Rope** for renames. Consider a small package `backend/services/objectives/` (parsing, formatting, printing) with a facade preserving `print_objectives_from_`*.

---

### 1.6 `tools/docx_renderer/table_cell/fill.py` (956 lines) — **Done (Session 19)**

**Current shape (post-split):** Split into fill_metadata.py, fill_day.py, fill_cell.py; fill.py is a thin re-export. Public API unchanged (fill_metadata, fill_day, fill_single_slot_day, fill_multi_slot_day, fill_cell).

**Refactor strategy:** **Manual** extraction of logical groups (e.g. by cell type or by step in the fill pipeline). **Cursor** to identify boundaries; **Rope** for renames. Branch `refactor/fill-py-split`; merged to master.

---

### 1.7 `tools/batch_processor_pkg/slot_flow.py` (918) and `week_flow.py` (862)

**Current shape:** Already split in Session 13 (orchestrator split). These hold the extracted flow logic.

**Refactor strategy:** Lower priority unless adding features. If needed: **manual** extraction of sub-steps (e.g. slot_flow: resolve file, extract, transform, persist as separate helpers). No need for Bowler/LibCST unless you have a repeatable pattern across the package.

---

## 2. Review candidates (500–800 lines)

- **backend/llm_service.py (789):** Already refactored (Session 3); llm/ package exists. Monitor; only re-split if it grows again.
- **tools/docx_renderer/renderer.py (739):** Already in package. Consider extracting smaller helpers if touching this file.
- **backend/services/objectives_pdf_generator.py (719):** Same pattern as objectives_printer; consider splitting after objectives_printer if both share structure.
- **backend/llm/prompt_builder.py, validation.py (673 each):** Already split. Review only if complexity grows.
- **tools/batch_processor_pkg/combined_original.py (660):** Candidate for extracting style/merge helpers if it grows.
- **tools/docx_utils.py (636), tools/json_repair.py (615):** Utility modules; split only if a clear subdomain appears (e.g. docx_utils: style vs structure).
- **backend/lesson_schema_models.py (581), tools/batch_processor_pkg/signatures.py (553):** Data/schema; split only if logical groupings are clear.

---

## 3. Frontend

- **ScheduleInput.tsx (450), SlotConfigurator.tsx (423):** **Done (Session 18).** Below 500-line threshold but sizeable. Per REFACTORING_PRIORITIES_AND_TOOLS (BatchProcessor.tsx refactor pattern): extract subcomponents and hooks (e.g. useScheduleInput, useSlotConfigurator) and keep the main component as a thin composition. Branch `refactor/schedule-slot-frontend`: schedule_input/ (useScheduleInput, ScheduleInputHeader, ScheduleInputTable, ScheduleColorLegend, NoUserSchedule), slot_configurator/ (useSlotConfigurator, SortableSlotItem); ScheduleInput.tsx and SlotConfigurator.tsx re-exports. Smoke-tested: schedule and slots tabs OK.

---

## 4. How this aligns with the refactoring module


| Practice                                                    | Where it applies                                                                                                                                       |
| ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **One refactor, one branch; small atomic commits**          | GIT_DURING_REFACTORING. Use branch names like `refactor/plans-router-split`, `refactor/combine-split`.                                                 |
| **Run tests before each commit**                            | GIT_DURING_REFACTORING. API tests, batch_processor tests, and any service-specific tests.                                                              |
| **Large-file splits = manual edits**                        | REFACTORING_TOOLS_FOR_CURSOR. Cursor (AI) for design and extraction; Rope/pylsp-rope for renames and import updates.                                   |
| **Bowler/LibCST for mechanical patterns across many files** | Use only when you have a repeatable pattern (e.g. standardizing imports or a call signature); run with `.diff(interactive=True)` on a refactor branch. |
| **After AI refactors: run tests + Rope for follow-up**      | REFACTORING_TOOLS_FOR_CURSOR. Prevents missed call sites and imports.                                                                                  |
| **Refresh section 0.5 after merge**                         | LOC_AND_METRICS. Run `python tools/refactor/count_loc.py --markdown` and update REFACTORING_PRIORITIES_AND_TOOLS.                                      |


---

## 5. Suggested session order (for planning only)

Not mandated by REFACTORING_PRIORITIES_AND_TOOLS 0.2; use as a draft:

1. **plans router split** — **Done (Session 14).** High impact; clear subdomains (plans, lesson steps, lesson mode). Merged to master; pushed to origin.
2. **users router split** — **Done (Session 15).** Same pattern; reduces merge conflicts and clarifies ownership.
3. **combine.py split** — Batch processor package already exists; keeps combine maintainable.
4. **sentence_frames_pdf_generator / objectives_printer** — **Done (Session 17).** Service-layer splits; branch `refactor/sentence-frames-objectives-split`; merged to master.
5. **Frontend (ScheduleInput, SlotConfigurator)** — **Done (Session 18).** Branch `refactor/schedule-slot-frontend`; hook + subcomponents + re-exports.

Each session: create branch from `master`, make small commits, run tests, merge when done, update REFACTORING_PRIORITIES_AND_TOOLS 0.1 and 1.4 (and 0.5 if LOC changed).
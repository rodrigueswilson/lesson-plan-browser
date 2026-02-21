# Refactoring Priorities and Tools

This document lists **refactoring and fix priorities** for the codebase and gives a **critical overview of Python refactoring libraries** and when they are worth using. It also defines a **multi-session plan** (branches, commits, merges) and a **progress log** so different Cursor sessions can resume work consistently.

---

## 0. Multi-session plan and progress (update this as you go)

**Last updated:** 2026-02-21

### 0.1 Progress summary


| Status          | Items                                                                                                                                                                                                                                                                     |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Done**        | Batch processor package; Database alias and optional db_path (see 1.4). Session 1 (branch `fix/test-suite-collection`): test suite collection and fixes. Session 2 (branch `refactor/split-api`): split backend/api.py into routers (health, settings, users, plans, process-week, analytics); app mounts routers; duplicate analytics removed; API/smoke tests pass (same pre-existing failures as baseline). |
| **In progress** | —                                                                                                                                                                                                                                                                         |
| **Not started** | Priorities 2–3 (high), 5–9 (medium), 10–13 (lower). Proceed to Session 3 (refactor llm_service) from updated master per Section 0.2.                                                                                                                                                                                                     |


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

---

## 1. Refactoring and fix priorities

Priorities are ordered by impact and risk. Do high-priority items on a branch; run focused tests before and after.

### 1.1 High priority (stability and maintainability)


| Priority | Item                                                 | Location / reference                                                         | Notes                                                                                                                                                                        |
| -------- | ---------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1        | **Split `backend/api.py`** (~4,200 lines)            | `backend/api.py`                                                             | Single FastAPI app with all routes. Split into routers by domain: users, plans, process-week, analytics, settings, health. Reduces merge conflicts and clarifies ownership.  |
| 2        | **Refactor `backend/llm_service.py`** (~2,850 lines) | `backend/llm_service.py`                                                     | Extract: prompt building, retry/validation logic, provider adapters. Improves testability and future provider additions.                                                     |
| 3        | **PerformanceTracker simplification**                | `docs/planning/CRITICAL_REVIEW_AND_CORRECTIONS.md`                           | Add retention (e.g. 30 days), optional sampling / debug-only granular tracking. Reduces SQLite growth and locking risk.                                                      |
| 4        | **Fix remaining test suite collection errors**       | `docs/fix/DATABASE_PROBLEMS.md` (done); TestClient, test_api_endpoints, etc. | Database import fixed. Still to fix: TestClient API, test_api_endpoints module-level code, test_week_calculation first_date format, DOCX paths, backend_connection sys.exit. |


### 1.2 Medium priority (large files, clear boundaries)


| Priority | Item                                              | Location                                          | Notes                                                                                                                                                |
| -------- | ------------------------------------------------- | ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| 5        | **Split `tools/docx_renderer.py`** (~2,760 lines) | `tools/docx_renderer.py`                          | Extract: table/cell filling, hyperlink placement, multi-slot flow, style handling. Align with combined-original style refactor (see ERROR_ANALYSIS). |
| 6        | **Split `tools/docx_parser.py`** (~2,146 lines)   | `tools/docx_parser.py`                            | Extract: structure detection, slot extraction, table/paragraph handling.                                                                             |
| 7        | **Split `backend/database.py`** (~1,850 lines)    | `backend/database.py`                             | Split by domain: user CRUD, plans/slots, lesson steps, metrics, migrations. Keep single `get_db()` and interface.                                    |
| 8        | **Combined-original DOCX styles**                 | `docs/ERROR_ANALYSIS_COMBINED_ORIGINAL_STYLES.md` | Refactor rendering/merge so style conflicts are avoided or cleaned up post-merge.                                                                    |
| 9        | **Supabase database module**                      | `backend/supabase_database.py` (~1,520 lines)     | Extract: auth, query helpers, sync logic.                                                                                                            |


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


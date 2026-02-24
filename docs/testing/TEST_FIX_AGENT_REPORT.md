# Test Fix Agent Report (Runbook)

**Purpose:** This document is a runbook for an **agent-only** session. A new Cursor agent should follow it from top to bottom without requiring human decisions. It covers: running the full test suite, classifying failures, documenting known skips/failures, fixing unambiguous failures, and recording everything that needs human input for the companion report (TEST_FIX_HUMAN_REPORT.md).

**When to use:** Start a new chat/session and say: *"Follow the instructions in docs/testing/TEST_FIX_AGENT_REPORT.md. Execute all steps and update the documents as you go."*

---

## 0. Context for New Sessions

- **Project:** Bilingual Weekly Plan Builder (LP). Root: `d:\LP` (or repo root on your machine).
- **Tests:** All tests live under `tests/`. Run pytest from **project root**. Config: `pytest.ini` (testpaths = tests, timeout = 120s).
- **Canonical commands** (see also [Cursor Pytest Automation Prompt](../Cursor%20Pytest%20Automation%20Prompt.md) and [MAINTENANCE_RECOMMENDATIONS](../MAINTENANCE_RECOMMENDATIONS.md)):
  - **Quick check (before commit):**  
    `python -m pytest tests/test_api.py tests/test_database_crud.py tests/test_week_calculation.py -q`
  - **Critical path (CI core):**  
    `python -m pytest tests/test_api.py tests/test_database_crud.py tests/test_week_calculation.py tests/test_batch_processor_facade.py tests/test_docx_renderer.py -q`
  - **Full suite (before merge / for this runbook):**  
    `python -m pytest tests/ -q 2>&1 | tee pytest_full_suite.txt`  
    Run from project root; allow several minutes. The file `pytest_full_suite.txt` will contain the full output.
- **Branch:** Prefer working on a fix branch, e.g. `fix/test-failures-<date>` branched from `master`, so changes can be committed atomically.

---

## 1. Run Full Suite and Capture Output

1. From project root:  
   `python -m pytest tests/ -q 2>&1 | tee pytest_full_suite.txt`
2. If you already have a recent `pytest_full_suite.txt` from a prior run and the user wants to use it, you may skip running and use that file. Otherwise run the command above.
3. Note the summary line at the end of the file, e.g.:  
   `= X failed, Y passed, Z skipped, ... N errors in ...s`

---

## 2. Classify Failures

1. Open `pytest_full_suite.txt` and locate the **FAILED** and **ERROR** sections (usually at the end of the file). Each line has the form:
   - `FAILED tests/<file>::<test_id>`
   - `ERROR tests/<file>::<test_id>`
2. For each FAILED/ERROR, infer the **cause** from the traceback in the file (search for the test id and read the exception):
   - **setup_fixture** – failure in fixture or setup (e.g. Session vs cursor, missing DB init, UNIQUE constraint).
   - **import_attr** – ImportError or AttributeError in test or app code (e.g. module has no attribute X).
   - **assertion** – AssertionError; test expects different behavior (could be test bug or app bug).
   - **timeout_env** – test hits live backend or file and times out or skips when backend/file missing.
   - **other** – anything else (document briefly).
3. Build a **Failure groups** table. Group by test **file** (and optionally by cause). Example format:

   | File | FAILED | ERROR | Cause (summary) |
   |------|--------|-------|------------------|
   | test_analytics_integration.py | N | M | setup_fixture (Session/cursor; UNIQUE user) |
   | test_integration_authorization.py | 1 | K | setup_fixture; assertion (nonexistent_user_id) |
   | ... | ... | ... | ... |

4. Write this table into **Section 4** of this document (Known skips/failures), and keep a copy for Section 5 (Add to Human Report).

### Failure groups (from last full run)

**Summary line:** `= 73 failed, 560 passed, 36 skipped, 1 error in 374.52s`

| File | FAILED | ERROR | Cause (summary) |
|------|--------|-------|------------------|
| test_analytics_endpoints.py | 7 | 0 | assertion (total_operations, daily breakdown, CSV header, model_dist, operation_types) |
| test_analytics_simple.py | 6 | 0 | assertion (duration_ms, dates sort, tokens, total_duration_ms in stats) |
| test_analytics_with_mock_data.py | 0 | 1 | setup_fixture (fixture user_id not found); Session vs cursor in create_mock_data |
| test_diagnostic_logging.py | 9 | 0 | assertion (stage_file.exists() for parser/lesson_json/renderer paths) |
| test_hyperlink_improvements.py | 3 | 0 | assertion (placement observability, no_school filtering) |
| test_hyperlink_workflow_e2e.py | 3 | 0 | assertion (coordinate placement, referenced links, link locations) |
| test_integration_tracking.py | 4 | 0 | import_attr (AttributeError in tracking/CSV code) |
| test_integration_tracking_simple.py | 2 | 0 | assertion / import_attr |
| test_json_error_integration.py | 3 | 0 | import_attr (_analyze_json_error missing on LLMService) |
| test_json_error_prevention.py | 10 | 0 | import_attr (_pre_validate_json, _analyze_json_error, _detect_error_type missing) |
| test_json_resilience.py | 1 | 0 | import_attr (AttributeError type object) |
| test_llm_workflow.py | 1 | 0 | timeout_env / other (FileNotFoundError for file path) |
| test_log_errors_fixes.py | 1 | 0 | assertion (validate_structure truncates seven to six) |
| test_media_anchoring.py | 1 | 0 | assertion (inject_hyperlink_inline) |
| test_multislot_critical_fixes.py | 3 | 0 | assertion (first_slot_clears, image_subject_filtering) |
| test_multislot_hyperlinks.py | 8 | 0 | assertion (multislot structure, hyperlinks, empty slots, formatting) |
| test_user_workflow.py | 1 | 0 | setup_fixture (UNIQUE users.id / class_slots.id); ORM dict access |
| test_vocabulary_sentence_frames.py | 7 | 0 | assertion (ValidationError SentenceFrame; vocabulary/sentence_frames count, levels, stem, open_question) |
| test_wida_domain_selection.py | 4 | 0 | assertion (prompt domain section, schema examples, student_goal duplicates) |

**Unambiguous fixes applied this session:** test_analytics_with_mock_data (fixture + Session/PerformanceMetric + aggregate stats total_duration_ms/avg_duration_ms), test_user_workflow (unique user id, unique slot id, ORM attribute access).

---

## 3. Update Known Skips/Failures

1. Ensure the project has a single place for "known skips and failures" (e.g. a subsection in CONTRIBUTING, or a dedicated doc under `docs/testing/`). If it does not exist, create `docs/testing/KNOWN_SKIPS_AND_FAILURES.md`.
2. In that place:
   - **Skips:** List tests or files that are skipped by design (e.g. backend not running, optional live tests). For each: test id or pattern, reason, and "next step" if any (e.g. "Run with backend up" or "Skip in CI").
   - **Failures:** List failure groups (by file or by cause) that are not yet fixed. For each: short description, cause (from your classification), and "next step" (e.g. "Fix in Report 1", "Needs decision in Human Report").
3. Point to the **Failure groups** table (or paste a summary) so the next reader knows the current state.

---

## 4. Fix Unambiguous Cases (No Human Decision)

Apply fixes only when the fix is **mechanical** and does not require product/behavior decisions. Commit after each logical group; run verification after each commit.

**Rules:**
- **Session vs cursor:** If the traceback shows `'Session' object has no attribute 'cursor'` (or similar), the test or fixture is using a raw DB cursor while the app uses SQLAlchemy Session. Fix: use Session and `session.execute(text(...))` or ORM models (e.g. `PerformanceMetric`) instead of `conn.cursor()`. Ensure DB init (e.g. `db.init_db()`) and teardown are correct.
- **UNIQUE constraint (e.g. users.id):** If the same user id is reused across tests and causes IntegrityError, make user id unique per run (e.g. suffix with uuid) or use module-scoped fixture and single user for the module.
- **Missing fixture / parametrization:** If a test has a parameter (e.g. `filepath`) but no `@pytest.mark.parametrize` or fixture provides it, add parametrization with concrete fixture paths; if the file is optional, skip when the file is missing (e.g. `if not Path(filepath).exists(): pytest.skip(...)`).
- **Live backend / timeout:** If the test calls a live backend (e.g. localhost:8000) and fails when the server is down, add a health-check at the start and `pytest.skip(...)` when unreachable; add a timeout to requests.
- **ImportError / AttributeError in test code:** If the traceback points to a missing or wrong attribute in test code (or a test helper), fix the import or the attribute name. If it points to application code, still fix only if the fix is obvious (e.g. typo); otherwise add to Human Report.
- **Do not:** Weaken or remove assertions without a clear, documented reason; do not change application behavior unless the fix is obviously correct (e.g. wrong constant in app). When in doubt, add to Human Report.

**Workflow per group:**
1. Pick one failure group (e.g. one file) that you classified as fixable mechanically.
2. Run the failing test(s) in isolation:  
   `python -m pytest tests/<file>::<test_id> -vv -s`
3. Apply the fix (fixture, Session, parametrization, skip, etc.).
4. Re-run:  
   `python -m pytest tests/<file> -q`  
   then  
   `python -m pytest tests/test_api.py tests/test_database_crud.py tests/test_week_calculation.py tests/test_batch_processor_facade.py tests/test_docx_renderer.py -q`
5. Commit with a clear message, e.g. `fix(tests): use Session in test_analytics_integration fixtures`.

Repeat until no more unambiguous groups remain. Any failure that needs a **product decision** (e.g. "Is 403 acceptable here?", "Fix schema or relax test?") must **not** be fixed here; instead add it to Report 2 (Section 5 below).

---

## 5. Add to Human Report (Remaining Work)

For every failure (or failure group) that you did **not** fix in Section 4, add an entry to **docs/testing/TEST_FIX_HUMAN_REPORT.md** in the "Decisions needed" section. Use the format:

- **Group (file or name):** e.g. `test_vocabulary_sentence_frames` (7 tests).
- **Cause:** e.g. assertion (vocabulary count mismatch).
- **Decision needed:** e.g. "Fix schema to match test expectation, or relax test to match current behavior?"
- **Test ids (optional):** list or "see pytest_full_suite.txt".

Also ensure the **Failure groups** table (or a reference to it) is in the Human Report so the human sees the full picture. If you created or updated `docs/testing/KNOWN_SKIPS_AND_FAILURES.md`, add a line in the Human Report pointing to it.

---

## 6. Final Verification

1. Run **quick check:**  
   `python -m pytest tests/test_api.py tests/test_database_crud.py tests/test_week_calculation.py -q`
2. Run **critical path:**  
   `python -m pytest tests/test_api.py tests/test_database_crud.py tests/test_week_calculation.py tests/test_batch_processor_facade.py tests/test_docx_renderer.py -q`
3. If anything fails that was passing before your fixes, revert or fix the regression and re-commit.
4. Optionally run the full suite again and refresh `pytest_full_suite.txt` and the Failure groups table so the Human Report is up to date.

---

## 7. Handoff to Next Session

- **Agent-only work is done** when: classification is done, Known skips/failures updated, all unambiguous fixes applied and committed, Human Report updated with "Decisions needed" entries, and quick check + critical path are green.
- **Next session:** A human (with or without the same agent) should open **docs/testing/TEST_FIX_HUMAN_REPORT.md**, make the requested decisions, then have the agent apply those decisions (fixes, skips with ticket IDs, CI changes) and re-run the relevant tests.

**Last session handoff:** Classification and Failure groups table added (Section 2). KNOWN_SKIPS_AND_FAILURES.md created; TEST_FIX_HUMAN_REPORT.md updated with Failure groups and reference to known skips. Unambiguous fixes applied: test_analytics_with_mock_data (fixture, Session/PerformanceMetric, aggregate total_duration_ms/avg_duration_ms), test_user_workflow (unique user/slot ids in backend, ORM attribute access in test). Quick check and critical path both passed. You may commit the fixes on a branch (e.g. `fix/test-failures-2026-02-24`) and push; remaining failures are documented in the Human Report for product decisions.

---

## References

- [Cursor Pytest Automation Prompt](../Cursor%20Pytest%20Automation%20Prompt.md) – test execution strategy and CLI.
- [MAINTENANCE_RECOMMENDATIONS](../MAINTENANCE_RECOMMENDATIONS.md) – maintenance and CI.
- [CONTRIBUTING](../CONTRIBUTING.md) – development workflow and testing.

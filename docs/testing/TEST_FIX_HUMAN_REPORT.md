# Test Fix Human Report (Collaborative)

**Purpose:** This document lists **remaining test work that requires human decisions**. It is filled by the agent after running the [Test Fix Agent Report](TEST_FIX_AGENT_REPORT.md) runbook. In a follow-up session, you (the human) decide how to handle each item; the agent then implements those decisions (fixes, skips with ticket IDs, CI changes).

**When to use:** After an agent has executed the Agent Report (or after you have run the full suite and classified failures). Open this document, fill in the "Decision" and "Ticket / Notes" columns where indicated, then tell the agent: *"Apply the decisions in docs/testing/TEST_FIX_HUMAN_REPORT.md and run the relevant tests."*

---

## 0. Context for New Sessions

- **Relationship to Agent Report:** The [TEST_FIX_AGENT_REPORT](TEST_FIX_AGENT_REPORT.md) runbook instructs the agent to fix only **unambiguous** failures (e.g. fixture/Session, missing import, clear AttributeError in test code). Everything that needs a **product or policy decision** is listed here.
- **Your role:** For each row in "Decisions needed", choose: fix app, fix test, relax assertion, skip (quarantine), or leave for later. For "Quarantine list", provide a ticket ID and short reason so the agent can add `@pytest.mark.skip(reason="...")` and a comment. For "CI", decide whether to add markers/jobs for slow or live tests.
- **Agent's role:** Apply your choices: implement fixes, add skips with ticket references, update CI config, then run quick check and critical path (and optionally full suite).

---

## 1. Failure Groups Summary (from last run)

*(The agent fills this from the last full suite run. If empty, run the full suite and follow the Agent Report Section 2 to populate it.)*

| File | FAILED | ERROR | Cause (summary) |
|------|--------|-------|------------------|
| test_analytics_endpoints.py | 7 | 0 | assertion (stats shape, daily, CSV, model_dist, operation_types) |
| test_analytics_simple.py | 6 | 0 | assertion (duration_ms, sort, tokens, total_duration_ms) |
| test_diagnostic_logging.py | 9 | 0 | assertion (stage file paths exist) |
| test_hyperlink_improvements.py | 3 | 0 | assertion |
| test_hyperlink_workflow_e2e.py | 3 | 0 | assertion |
| test_integration_tracking.py | 4 | 0 | import_attr (AttributeError) |
| test_integration_tracking_simple.py | 2 | 0 | assertion / import_attr |
| test_json_error_integration.py | 3 | 0 | import_attr (_analyze_json_error missing) |
| test_json_error_prevention.py | 10 | 0 | import_attr (_pre_validate_json, _analyze_json_error, _detect_error_type missing) |
| test_json_resilience.py | 1 | 0 | import_attr |
| test_llm_workflow.py | 1 | 0 | FileNotFoundError (path) |
| test_log_errors_fixes.py | 1 | 0 | assertion |
| test_media_anchoring.py | 1 | 0 | assertion |
| test_multislot_critical_fixes.py | 3 | 0 | assertion |
| test_multislot_hyperlinks.py | 8 | 0 | assertion |
| test_vocabulary_sentence_frames.py | 7 | 0 | assertion / ValidationError (SentenceFrame) |
| test_wida_domain_selection.py | 4 | 0 | assertion |

**Fixed this session (no longer failing):** test_analytics_with_mock_data (was ERROR; fixture + Session + aggregate stats), test_user_workflow (UNIQUE + ORM access).

**Last full run output file:** `pytest_full_suite.txt` (project root)  
**Summary line (before fixes):** `= 73 failed, 560 passed, 36 skipped, 1 error in 374.52s`

**Known skips and failures doc:** [KNOWN_SKIPS_AND_FAILURES.md](KNOWN_SKIPS_AND_FAILURES.md)

---

## 2. Decisions Needed

For each failure group that the agent could not fix automatically, decide: **Fix app**, **Fix test**, **Relax assertion**, **Quarantine (skip)**, or **Defer**. The agent will use your decision to implement.

| Group (file or name) | Short description | Decision type | Your decision | Ticket / Notes |
|----------------------|-------------------|---------------|----------------|----------------|
| analytics_endpoints | Aggregate/daily/CSV/operation/model endpoints failing | fix app vs fix test / acceptable behavior? | | |
| analytics_simple | Daily breakdown, model distribution, operation breakdown, aggregate stats | fix app vs fix test | | |
| diagnostic_logging | DiagnosticLogger assertions (hyperlinks, lesson_json, renderer metadata, filtering, placement) | fix app vs fix test / relax assertion? | | |
| hyperlink_improvements | Placement observability, no_school filtering diagnostics | fix app vs fix test | | |
| hyperlink_workflow_e2e | Coordinate placement, referenced links section, link locations | fix app vs fix test | | |
| integration_tracking | complete_tracking_workflow, tracking_with_error, tracking_disabled, csv_export (AttributeError) | fix app vs fix test | | |
| integration_tracking_simple | multiple_operations_tracking, csv_export_with_mock_data | fix app vs fix test | | |
| json_error_integration | pre_validation, full_parse, error_analysis | fix app vs fix test | | |
| json_error_prevention | pre_validate_*, analyze_error_*, identify_day_at_position, detect_error_type (AttributeError) | fix app vs fix test | | |
| json_resilience | test_samples (AttributeError) | fix app vs fix test | | |
| llm_workflow | test_llm_transformation (FileNotFoundError) | fix test (path) vs skip when file missing? | | |
| log_errors_fixes | test_validate_structure_truncates_seven_to_six | fix app vs fix test | | |
| media_anchoring | test_inject_hyperlink_inline | fix app vs fix test | | |
| multislot_critical_fixes | first_slot_clears, image_subject_filtering | fix app vs fix test | | |
| multislot_hyperlinks | multislot structure, hyperlinks, empty slots, placeholder, edge cases | fix app vs fix test | | |
| user_workflow | test_user_workflow (IntegrityError) | fix fixture/DB vs fix test | | |
| vocabulary_sentence_frames | daily_plan vocabulary/sentence_frames count and level assertions, missing stem/open_question | fix schema vs relax test? | | |
| wida_domain_selection | prompt domain section, schema examples, student_goal disallows duplicates | fix app vs fix test | | |
| *(add more rows as needed from Agent Report)* | | | | |

---

## 3. Quarantine List (Skip with Ticket)

Tests to **skip** until a ticket is resolved. Human fills **Ticket ID** and **Reason**; agent adds `@pytest.mark.skip(reason="<Ticket ID>: <Reason>")` (or equivalent) and a one-line comment above the test.

| Test id (or pattern) | Ticket ID | Reason | Done (Y/N) |
|-----------------------|------------|--------|------------|
| | | | |
| | | | |

---

## 4. CI and Markers

- **Slow / live tests:** Should slow or live-only tests be excluded from default CI and run in a separate job or with a marker (e.g. `@pytest.mark.slow`, `@pytest.mark.live`)?  
  **Decision:** *(e.g. Add marker `live` and run in optional job; or leave as-is.)*

- **Critical path:** The project already runs a critical path in CI (test_api, test_database_crud, test_week_calculation, test_batch_processor_facade, test_docx_renderer). Keep as-is or add more modules?  
  **Decision:** *(e.g. Keep as-is.)*

- **Branch:** CI workflow should trigger on `master` (see MAINTENANCE_RECOMMENDATIONS). Confirm branches in `.github/workflows/ci-integration-tests.yml` include `master`.  
  **Decision:** *(e.g. Add master; agent will implement.)*

---

## 5. Relaxed Assertions to Confirm

If you decided to **relax** an assertion (e.g. change expected count or structure), list it here so the agent can implement and you can confirm the new behavior is acceptable.

| Test id | What was relaxed | Acceptable? (Y/N) |
|---------|------------------|-------------------|
| | | |
| | | |

---

## 6. After Decisions Are Applied

- Agent will: apply fixes, add skips with ticket reasons, update CI/markers if requested, run quick check and critical path, and optionally re-run full suite.
- You: review diffs, run tests locally if desired, then merge or iterate.

**References:** [TEST_FIX_AGENT_REPORT](TEST_FIX_AGENT_REPORT.md), [Cursor Pytest Automation Prompt](../Cursor%20Pytest%20Automation%20Prompt.md), [MAINTENANCE_RECOMMENDATIONS](../MAINTENANCE_RECOMMENDATIONS.md).

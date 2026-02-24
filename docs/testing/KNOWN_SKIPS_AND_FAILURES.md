# Known Skips and Failures

This document is the single place for known test skips and current failure groups. It is updated by the agent when running the [Test Fix Agent Report](TEST_FIX_AGENT_REPORT.md) runbook.

**Last full run:** See `pytest_full_suite.txt` (project root). Summary: 73 failed, 560 passed, 36 skipped, 1 error (before unambiguous fixes).

---

## Skips

Tests or files skipped by design (e.g. backend not running, optional live tests).

| Test id or pattern | Reason | Next step |
|--------------------|--------|-----------|
| test_content_images.py | Optional / resource-dependent | Skip in CI or run when resources available |
| test_image_context.py | Optional / resource-dependent | Skip in CI |
| test_image_row_detection.py | Optional / resource-dependent | Skip in CI |
| test_pipeline.py (some) | Live or slow | Marker or optional job |
| test_production.py | Production-only | Skip in CI |
| test_rate_limiter_redis.py (some) | Redis not running | Skip when Redis down |
| test_real_data.py | Real data / live | Skip in CI |
| test_structure_placement.py | Optional | Skip in CI |
| test_training_examples.py (multiple) | Optional training data | Skip in CI |
| test_slot_aware_real.py | Real/slot-aware | Skip in CI |
| test_new_training_examples.py | Optional | Skip in CI |
| test_integration_authorization.py (one) | Conditional skip | As designed |
| test_analytics_api.py (some) | Conditional | As designed |
| test_edge_cases.py | Conditional | As designed |
| test_live_pipeline_simple.py | Live backend | Skip when backend down |
| test_media_anchoring.py (one) | Conditional | As designed |
| test_media_quality.py (one) | Conditional | As designed |
| test_log_errors_fixes.py (some) | Conditional | As designed |

(Exact skip reasons may vary; run `pytest -v` to see `@pytest.mark.skip` reasons.)

---

## Failures (not yet fixed)

Failure groups from the last full run that still need fixes or human decisions. See [TEST_FIX_HUMAN_REPORT.md](TEST_FIX_HUMAN_REPORT.md) for "Decisions needed".

| File | FAILED | Cause (summary) | Next step |
|------|--------|------------------|-----------|
| test_analytics_endpoints.py | 7 | assertion (stats shape, daily, CSV, model_dist, operation_types) | Fix app vs fix test (Human Report) |
| test_analytics_simple.py | 6 | assertion (duration_ms, sort, tokens, total_duration_ms) | Fix app vs fix test (Human Report) |
| test_diagnostic_logging.py | 9 | assertion (stage file paths exist) | Fix app vs fix test (Human Report) |
| test_hyperlink_improvements.py | 3 | assertion | Fix app vs fix test (Human Report) |
| test_hyperlink_workflow_e2e.py | 3 | assertion | Fix app vs fix test (Human Report) |
| test_integration_tracking.py | 4 | AttributeError in tracking/CSV | Fix app vs fix test (Human Report) |
| test_integration_tracking_simple.py | 2 | assertion / AttributeError | Fix app vs fix test (Human Report) |
| test_json_error_integration.py | 3 | LLMService missing _analyze_json_error | Fix app vs fix test (Human Report) |
| test_json_error_prevention.py | 10 | LLMService missing _pre_validate_json, _analyze_json_error, _detect_error_type | Fix app vs fix test (Human Report) |
| test_json_resilience.py | 1 | AttributeError | Fix app vs fix test (Human Report) |
| test_llm_workflow.py | 1 | FileNotFoundError (path) | Fix test path vs skip when file missing (Human Report) |
| test_log_errors_fixes.py | 1 | assertion (truncates seven to six) | Fix app vs fix test (Human Report) |
| test_media_anchoring.py | 1 | assertion (inject_hyperlink_inline) | Fix app vs fix test (Human Report) |
| test_multislot_critical_fixes.py | 3 | assertion | Fix app vs fix test (Human Report) |
| test_multislot_hyperlinks.py | 8 | assertion | Fix app vs fix test (Human Report) |
| test_vocabulary_sentence_frames.py | 7 | ValidationError SentenceFrame; count/levels/stem/open_question | Fix schema vs relax test (Human Report) |
| test_wida_domain_selection.py | 4 | assertion (prompt, schema, student_goal) | Fix app vs fix test (Human Report) |

**Fixed this session (no longer in failures):** test_analytics_with_mock_data (fixture + Session + aggregate stats), test_user_workflow (unique user/slot id, ORM access).

---

## References

- [TEST_FIX_AGENT_REPORT.md](TEST_FIX_AGENT_REPORT.md) – runbook for classification and unambiguous fixes.
- [TEST_FIX_HUMAN_REPORT.md](TEST_FIX_HUMAN_REPORT.md) – decisions needed for remaining failures.

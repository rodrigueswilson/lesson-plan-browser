# PR-Ready Summary — Wave 2 ELA Autonomous Rollout (2026-04-07)

## Why
- Expand validated deterministic ELA ingest behavior beyond Unit 8 baselines.
- Enforce SSOT policy (`ela_lesson_plan_structured` primary) while preserving link/resource reliability.
- Produce reproducible evidence for rollout decisions.

## What changed
- Wave 2 unit onboarding and validation:
  - Added and ingested:
    - `ELA_2_U7_wave2` from Grade 2 Unit 7 tab DOCX
    - `ELA_3_U7_wave2` from Grade 3 Unit 7 synthesized tab DOCX
- Gate and evidence automation:
  - Reused/extended `tools/db/wave1_ela_unit8_compare.py` for arbitrary unit IDs.
  - Added `tools/db/wave2_ui_spotcheck.py` for first/middle/last scripted UI spot checks.
- Ingest link persistence hardening:
  - `tools/scraper/table_extractor.py`
    - Added `_collect_links_from_ela_structured_json` to extract links from structured JSON payloads.
    - Ensured structured-plan anchors merge into `_resources` during ELA ingest.
    - Added Google Doc ID derivation in `_merge_links_into_resources`, so `resources.id` uses stable `google_id`.
- Verifier SSOT alignment:
  - `tools/scraper/verify_curriculum_db.py`
    - Removed outdated warning expecting `ela_key_learning_summary` for `ELA_3_U8_sample`.
    - Warn only if both `ela_lesson_plan_structured` and `ela_key_learning_summary` are missing.
- Tests:
  - `tests/test_ela_lesson_plan_table.py`
    - Added assertions for `google_id` persistence in merged resources.
    - Added coverage for structured JSON link extraction helper.

## Key results
- Baseline units:
  - `ELA_2_U8_sample`: PASS
  - `ELA_3_U8_sample`: PASS
- Wave 2 units:
  - `ELA_2_U7_wave2`: PASS after targeted link persistence fix (`missing resources rows: 14 -> 0`)
  - `ELA_3_U7_wave2`: PASS
- Verifier:
  - `python tools/scraper/verify_curriculum_db.py`: PASS

## Evidence
- Full rollout evidence:
  - `docs/curriculum/acceptance-evidence/phase-7/WAVE_2_ELA_AUTONOMOUS_ROLLOUT_2026-04-07.md`
- Ingest reports:
  - `ingest_reports/2026-04-07T18-56-42Z_260a3c92.json`
  - `ingest_reports/2026-04-07T18-59-26Z_59acc651.json`

## Test plan (for reviewer)
- [ ] `python -m pytest tests/test_ela_lesson_plan_table.py -q --tb=short`
- [ ] `python tools/db/wave1_ela_unit8_compare.py --unit-id ELA_2_U8_sample`
- [ ] `python tools/db/wave1_ela_unit8_compare.py --unit-id ELA_3_U8_sample`
- [ ] `python tools/db/wave1_ela_unit8_compare.py --unit-id ELA_2_U7_wave2`
- [ ] `python tools/db/wave1_ela_unit8_compare.py --unit-id ELA_3_U7_wave2`
- [ ] `python tools/db/wave2_ui_spotcheck.py --units ELA_2_U7_wave2 ELA_3_U7_wave2`
- [ ] `python tools/scraper/verify_curriculum_db.py`

## Risk notes
- Wave 2 UI checks are script-aided and sampled (first/middle/last), not full visual exhaustive review for every lesson.
- Unit-template-specific optional fields (`learning_procedures_html`, `engagement_with_content_html`, `daily_instructional_task_html`) remain empty for these tab families and continue to rely on existing fallback rendering behavior.

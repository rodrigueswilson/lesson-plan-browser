# Phase 5 execution record — Cross-grade representative sample

**Branch:** `curriculum/phase-5-cross-grade-sample`  
**Governing plan:** `docs/curriculum/PHASED_ROLLOUT_PLAN.md` (Phase 5, Stages B/C)  
**Workflow template:** `docs/curriculum/PHASE_EXECUTION_TEMPLATE.md`  
**Start date:** 2026-03-29

## In-scope (completed / in flight)

- [x] Curated sample matrix Grades 2–8 with variance classes and registry paths — `PHASE_5_SAMPLE_MATRIX.md`
- [x] Tracked pass/fail and parser/tooling exception class for attempted export — `RefreshError` in matrix
- [x] ELA: documented `ela_key_learning_summary` vs `ela_lesson_plan_structured` for G2/G3 samples in DB; Explorer variance map — `PHASE_5_UI_EXPLORER_VARIANCE.md`
- [x] Archived gate logs under `docs/curriculum/acceptance-evidence/phase-5/`

## Out-of-scope (confirmed)

- Program-wide bulk ingest of all units

## Test gate #1 (pre-refactor)

- Commands:
  - `python tools/scraper/verify_curriculum_db.py`
  - `pytest tests/test_grade3_ela_ingest_smoke.py tests/test_math_fidelity_helpers.py tests/test_ingest_report_failure_codes.py tests/test_curriculum_gaps.py`
  - `npm run build` in `lesson-plan-browser/frontend`
- Result: Pass
- Evidence: `test-gate-5-1-verify_curriculum_db.txt`, `test-gate-5-1-pytest-phase-deps.txt`, `test-gate-5-1-lesson-browser-build.txt`

## Refactor pass

- **ELA summary coalescing (2026-03-29):** `RecursiveTableParser.ingest_to_curriculum` (`tools/scraper/table_extractor.py`) replaces paragraph-driven lessons with **Summary of Key Learning** rows when **no** lesson anchors match or when matched count is **below 35%** of summary rows (minimum **5** summary rows). Restores **ELA_6_U1_sample** and **ELA_8_U1_sample** on merged-tab DOCX without changing compendium tabs that already parse “Lesson N:” headings.

## Test gate #2 (post-refactor)

- Commands: same as gate #1
- Result: Pass
- Evidence: `test-gate-5-2-verify_curriculum_db.txt`, `test-gate-5-2-pytest-phase-deps.txt`, `test-gate-5-2-lesson-browser-build.txt`

## Local JSON ingest (Stage C vertical sample)

- Orchestrator / tooling: `tools/db/phase5_vertical_sample_ingest.py`, `tools/db/ingest_wave_unit.py --docx`, `tools/scraper/gdoc_tab_to_docx.py`
- Parser: `RecursiveTableParser` ELA **summary-table coalescing** (when paragraph lesson anchors are missing or coverage is below 35% of summary rows with at least 5 rows) — `tools/scraper/table_extractor.py`
- PASS rows (2026-03-29): `ELA_4_compendium_sample` (21), `ELA_5_compendium_sample` (15), `ELA_6_U1_sample` (34), `ELA_8_U1_sample` (24), `Math_8_U8_sample` (20)
- PENDING: Math G4/G5 matrix doc IDs (no matching `originals` JSON in repo)

## Test gate #3 (post–local-JSON ingest)

- Commands: same as gate #1, plus `verify_curriculum_db.py --ingest-report` for PASS ingest reports listed in `test-gate-5-3-verify_curriculum_db.txt`
- Result: Pass
- Evidence: `test-gate-5-3-verify_curriculum_db.txt`, `test-gate-5-3-pytest-phase-deps.txt`, `test-gate-5-3-lesson-browser-build.txt`

## Branch hygiene

- Merged `origin/master` into this branch — already up to date at session time

## Merge and push

- Phase 5 **evidence and scope** are **closed** (2026-03-29): no further ingest for deferred Math G4/G5 rows; see `PHASE_5_WRAP_UP.md`. Git merge/push of `curriculum/phase-5-cross-grade-sample` follows normal branch policy and is not blocked on those rows.

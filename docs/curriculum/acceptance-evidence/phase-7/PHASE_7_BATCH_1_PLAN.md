# Phase 7 — Batch 1 plan (controlled expansion)

**SSOT matrix (origin):** `docs/curriculum/acceptance-evidence/phase-5/PHASE_5_SAMPLE_MATRIX.md`  
**Registry:** `reference_docs/scraped_registry.json`

## Goal

Run the **first** Phase 7 ingest batch using the same safety pattern as Phase 3/5: one unit at a time, archived `ingest_reports`, `verify_curriculum_db.py --ingest-report`, and a **filesystem rollback** path.

## Operator workflow (every batch)

1. **Snapshot:** Copy `data/curriculum.db` and, if present, `data/curriculum.db-wal` / `data/curriculum.db-shm` to a local path such as `backups/curriculum-pre-batch-<ISO8601>.db` (or another directory outside git). Do not commit database files.
2. **Ingest:** Use `tools/db/ingest_wave_unit.py` (with `--docx` when using local exports) or a scoped driver such as `tools/db/phase5_vertical_sample_ingest.py` as a pattern for multi-step builds.
3. **Record:** Keep the JSON path printed as `Ingest report written: …` under `ingest_reports/`.
4. **Verify:** `python tools/scraper/verify_curriculum_db.py --ingest-report ingest_reports/<run_id>.json`
5. **Rollback:** If verification or spot checks fail, close apps using the DB, restore the three files from step 1, and note the failing report in this file or a session log.

## Batch 1 targets (priority)

| Order | `unit_id` (proposed) | Registry focus | Doc ID | Status |
|-------|----------------------|----------------|--------|--------|
| 1 | `Math_4_5_sample_U4` | Uncategorized Grade → Math → Unit 4 (Understanding Addition and Subtraction) | `1aMiqygM9kCrQ0DKFGPma3lKT91lJQkAUF-H8TvQMbus` | **Blocked:** no root-`documentId` `originals/*.json` in repo; need Docs API dump or DOCX + `--docx` |
| 2 | `Math_4_5_sample_U5` | Uncategorized Grade → Math → Unit 5 (Numbers to 1,000) | `1S9fRcM1-6futZzmOgOEg3eQ1hfRh8YpXHfjmyiPTu08` | **Blocked:** same |

When either artifact exists, add a row to the **Execution log** below with ingest report path and verify result.

## Execution log

| Date | Action | Result |
|------|--------|--------|
| 2026-03-29 | Batch 1 plan published; no ingest (prerequisites missing) | Documented |

## Post-batch regression (required after any ingest in this batch)

From repo root:

```text
python tools/scraper/verify_curriculum_db.py
pytest tests/test_grade3_ela_ingest_smoke.py tests/test_math_fidelity_helpers.py tests/test_ingest_report_failure_codes.py tests/test_curriculum_gaps.py tests/test_curriculum_resource_resolve.py tests/test_curriculum_fts_and_links.py -q
```

In `lesson-plan-browser/frontend`: `npm run build`

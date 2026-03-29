# Phase 7 execution record — Expansion readiness and controlled scale-up

**Phase:** 7 — Expansion readiness  
**Branch:** `curriculum/phase-7-expansion-readiness`  
**Governing plan:** `docs/curriculum/PHASED_ROLLOUT_PLAN.md` (Phase 7)  
**Workflow template:** `docs/curriculum/PHASE_EXECUTION_TEMPLATE.md`  
**Start date:** 2026-03-29

## In-scope (plan)

- [x] **Batch workflow documented** — `PHASE_7_BATCH_1_PLAN.md` (snapshot, ingest, verify, rollback); first targets = deferred Math G4/G5 matrix rows (blocked on artifacts).
- [ ] Bulk onboarding in **curated batches** with run reports (executed per batch plan as sources land).
- [ ] Continuous QA monitoring for newly ingested units (reuse `verify_curriculum_db.py`, `ingest_reports/*.json`, `FAILURE_TAXONOMY.md`).
- [ ] Maintenance cadence for parser and subject configs (tie changes to gates and evidence per governance section of rollout plan).

## Integration

- **2026-03-29:** Branch `curriculum/phase-7-expansion-readiness` **pushed** to `origin` (open PR: `https://github.com/rodrigueswilson/lesson-plan-browser/pull/new/curriculum/phase-7-expansion-readiness`).

## Existing tooling (SSOT for batches — extend, do not duplicate)

| Concern | Location |
|--------|----------|
| Per-unit ingest + report | `tools/db/ingest_wave_unit.py`, `ingest_reports/` |
| Vertical sample orchestration (pattern) | `tools/db/phase5_vertical_sample_ingest.py` |
| Schema / gap gate | `python tools/scraper/verify_curriculum_db.py` and `--ingest-report ingest_reports/<id>.json` |
| Legacy MD batch driver (paths may drift) | `tools/db/batch_ingest_units.py`, `batch_ingest_units_remnants.py` |
| Phase 3 G3 Math corpus driver | `tools/db/ingest_g3_math_phase3_corpus.py`, `g3_math_phase3_corpus.py` |

**Rollback (operator):** Copy `data/curriculum.db` (and `-wal`/`-shm` if present) before a batch; restore files if a batch must be abandoned. Document batch id + report paths in session notes.

## Out-of-scope guardrails

- Program-wide bulk ingest **without** curated batch plan and gates (see decision checkpoint in `PHASED_ROLLOUT_PLAN.md`).
- Autonomous agent-driven ingestion.

## Test gate #1 (Phase 7 kickoff — same baseline as Phases 5–6)

- Commands:
  - `python tools/scraper/verify_curriculum_db.py`
  - `pytest tests/test_grade3_ela_ingest_smoke.py tests/test_math_fidelity_helpers.py tests/test_ingest_report_failure_codes.py tests/test_curriculum_gaps.py tests/test_curriculum_resource_resolve.py tests/test_curriculum_fts_and_links.py -q`
  - `npm run build` in `lesson-plan-browser/frontend`
- Result: **Pass** (recorded below)
- Evidence: `test-gate-7-1-verify_curriculum_db.txt`, `test-gate-7-1-pytest-phase-deps.txt`, `test-gate-7-1-lesson-browser-build.txt`

## Test gate #2 (post–Batch 1 plan documentation)

- Commands: same as gate #1.
- Result: **Pass**
- Evidence: `test-gate-7-2-verify_curriculum_db.txt`, `test-gate-7-2-pytest-phase-deps.txt`, `test-gate-7-2-lesson-browser-build.txt`

## Refactor pass

- Deferred until a Phase 7 deliverable requires it (run template gate before/after any refactor).

## Exit criteria (from plan — not yet met)

- Transition to continuous ingestion mode **approved** (operational signoff).
- Branch `curriculum/phase-7-expansion-readiness` merged and pushed per repo policy.

## Merge and push

- Not executed at kickoff.

### Next working goal

Execute **Batch 1** ingests when **Math G4/G5** artifacts exist (see `PHASE_7_BATCH_1_PLAN.md`): pre-batch DB copy, `ingest_wave_unit.py`, archive `ingest_reports`, run `verify_curriculum_db.py --ingest-report …`, then regression commands in the batch plan. Update the plan execution log and this file; Phase 7 exit still requires operational signoff and merge.

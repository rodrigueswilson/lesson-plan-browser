# Phase 5 wrap-up — Cross-grade representative sample

## Result: **CLOSED** (operator decision, 2026-03-29)

Phase 5 work is **wrapped up without further curriculum ingest.** Regression evidence on branch `curriculum/phase-5-cross-grade-sample` remains valid for the units already in `data/curriculum.db` (see test gate #3 logs and matrix below). **Math G4/G5** matrix seeds (`Math_4_5_sample_U4` / `Math_4_5_sample_U5`) are **deferred**: documented in `PHASE_5_SAMPLE_MATRIX.md` with registry doc IDs, but **no** additional lesson rows will be loaded for this phase. This records an explicit amendment to the stricter “every matrix row ingested before closure” line in `PHASED_ROLLOUT_PLAN.md` (see Phase 5 addendum there).

Git **merge/push** of the phase branch is unchanged housekeeping (policy, review, CI)—not tied to ingesting the deferred Math rows.

## One-line summary

Cross-grade representative sampling for Phase 5 is **complete for the executed subset**: ELA and Math 8 vertical samples with local snapshots, plus Grades 2–3 ladder work, are ingested and gated; **ELA G6/G8** use summary-table coalescing in `tools/scraper/table_extractor.py`. **Math G4/G5** rows stay **out of DB** by choice for this closure.

## Deferred follow-ups (optional, not Phase 5)

1. **Math G4/G5:** If those units are needed in DB later, add root-`documentId` JSON under `reference_docs/scraped/…/originals/` or export DOCX and run `ingest_wave_unit.py --docx …`; see matrix for doc IDs and proposed `unit_id` seeds.
2. **OAuth:** Only required for Drive-native export paths; local `--docx` flow does not need refreshed tokens for work already done.

## Evidence paths

- `docs/curriculum/acceptance-evidence/phase-5/PHASE_5_SAMPLE_MATRIX.md`
- `docs/curriculum/acceptance-evidence/phase-5/PHASE_5_EXECUTION.md`
- `docs/curriculum/acceptance-evidence/phase-5/PHASE_5_UI_EXPLORER_VARIANCE.md`
- `docs/curriculum/acceptance-evidence/phase-5/test-gate-5-1-verify_curriculum_db.txt`
- `docs/curriculum/acceptance-evidence/phase-5/test-gate-5-1-pytest-phase-deps.txt`
- `docs/curriculum/acceptance-evidence/phase-5/test-gate-5-1-lesson-browser-build.txt`
- `docs/curriculum/acceptance-evidence/phase-5/test-gate-5-2-verify_curriculum_db.txt`
- `docs/curriculum/acceptance-evidence/phase-5/test-gate-5-2-pytest-phase-deps.txt`
- `docs/curriculum/acceptance-evidence/phase-5/test-gate-5-2-lesson-browser-build.txt`
- `docs/curriculum/acceptance-evidence/phase-5/test-gate-5-3-verify_curriculum_db.txt`
- `docs/curriculum/acceptance-evidence/phase-5/test-gate-5-3-pytest-phase-deps.txt`
- `docs/curriculum/acceptance-evidence/phase-5/test-gate-5-3-lesson-browser-build.txt`
- `docs/curriculum/acceptance-evidence/phase-5/PHASE_5_ELA_G2_ACCEPTANCE.md`

## Next-phase trigger prompt

`Start Phase 6: execute docs/curriculum/PHASE_EXECUTION_TEMPLATE.md for phase-6-navigator-semantic-links, run test gate #1, implement in-scope only, and report PASS/BLOCKED with evidence paths.`

Phase 5 is **closed** per the amendment above; Phase 6 may start when you are ready (program-wide bulk ingest remains gated per `PHASED_ROLLOUT_PLAN.md` decision checkpoint).

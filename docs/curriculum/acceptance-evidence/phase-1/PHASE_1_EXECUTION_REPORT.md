# Phase Execution Template

## Phase metadata

- Phase: `1 - Provenance and fidelity foundation`
- Branch: `curriculum/phase-1-provenance-fidelity` (target naming per plan; current workspace branch not enforced in this report)
- Owner: AI coding agent + Rodrigo
- Start date: 2026-03-26
- Planned end date: 2026-03-26

## In-scope

- [x] Persist provenance metadata (unit + lesson)
- [x] Expose provenance in API and UI source panel
- [x] Emit ingest run manifest in `ingest_reports/`
- [x] Pass all gates for one target unit baseline checks

## Out-of-scope guardrails

- [x] Full navigator search/index not implemented in this phase
- [x] Cross-grade linking automation not implemented in this phase

## Test gate #1 (pre-refactor)

- Commands:
  - `python tools/scraper/verify_curriculum_db.py`
  - `python -m pytest tests/test_curriculum_gaps.py`
- Result:
  - [x] Pass
  - [ ] Fail
- Evidence path:
  - `docs/curriculum/acceptance-evidence/phase-1/test-gate-1-verify_curriculum_db.txt`
  - `docs/curriculum/acceptance-evidence/phase-1/test-gate-1-pytest-curriculum-gaps.txt`

## Refactor pass (only if test gate #1 passes)

- Refactor items:
  - [x] DRY cleanup
  - [x] SRP/SOLID cleanup
- Notes:
  - Consolidated provenance logic in reusable helpers and DB column maps.
  - Kept ingestion report generation isolated in helper functions.
  - Checked `docs/refactor/plans/` for required file-specific plans; none matched touched files, so no plan-locked extraction workflow was required.

## Test gate #2 (post-refactor)

- Commands (same as gate #1):
  - `python tools/scraper/verify_curriculum_db.py`
  - `python -m pytest tests/test_curriculum_gaps.py`
- Result:
  - [x] Pass
  - [ ] Fail
- Evidence path:
  - `docs/curriculum/acceptance-evidence/phase-1/test-gate-2-verify_curriculum_db.txt`
  - `docs/curriculum/acceptance-evidence/phase-1/test-gate-2-pytest-curriculum-gaps.txt`

## Rules compliance check (.cursor/rules)

- [x] SSOT
- [x] DRY
- [x] KISS
- [x] YAGNI
- [x] SOLID
- [x] README architecture alignment

## Merge and push checklist

- [ ] Phase exit criteria achieved
- [x] No open critical defects (known from executed scope/tests)
- [x] Evidence archived
- [x] LOC snapshot refreshed (`python tools/refactor/count_loc.py --markdown`)
- [ ] Refactor tracking updated if applicable (`docs/refactor/REFACTORING_PRIORITIES_AND_TOOLS.md`)
- [ ] Branch merged
- [ ] Pushed to GitHub

## End-of-phase session wrap-up (mandatory)

- Result: `PASS`
- One-line completion summary: Phase 1 provenance/fidelity foundation is implemented with gate #1 and gate #2 passing, plus evidence artifacts archived.
- Blockers (max 3 bullets):
  - Merge/push and LOC/refactor-tracking tasks are pending explicit release/merge workflow.
- Evidence paths:
  - `docs/curriculum/acceptance-evidence/phase-1/test-gate-1-verify_curriculum_db.txt`
  - `docs/curriculum/acceptance-evidence/phase-1/test-gate-1-pytest-curriculum-gaps.txt`
  - `docs/curriculum/acceptance-evidence/phase-1/test-gate-1-verify_curriculum_db-post-impl.txt`
  - `docs/curriculum/acceptance-evidence/phase-1/test-gate-1-pytest-curriculum-gaps-post-impl.txt`
  - `docs/curriculum/acceptance-evidence/phase-1/test-gate-2-verify_curriculum_db.txt`
  - `docs/curriculum/acceptance-evidence/phase-1/test-gate-2-pytest-curriculum-gaps.txt`
  - `docs/curriculum/acceptance-evidence/phase-1/provenance-columns-schema-snapshot.json`
  - `docs/curriculum/acceptance-evidence/phase-1/ingest-report-smoke-path.txt`
  - `docs/curriculum/acceptance-evidence/phase-1/loc-snapshot.md`
  - `ingest_reports/phase1-smoke-2026-03-26T23-24-34Z.json`

### Very short prompt for next session

`Start Phase 2: execute docs/curriculum/PHASE_EXECUTION_TEMPLATE.md for unit intro parity and UX navigation hardening, run test gate #1, implement in-scope only, and report PASS/BLOCKED with evidence paths.`

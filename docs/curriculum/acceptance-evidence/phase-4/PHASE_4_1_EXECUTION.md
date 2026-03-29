# Phase 4.1 execution record (ELA extraction and DB contract)

Filled from [PHASE_EXECUTION_TEMPLATE.md](../../PHASE_EXECUTION_TEMPLATE.md). Substage **4.1 only**; Phase 4.2 UI is out of scope here.

## Phase metadata

- Phase: `4 - ELA hardening`
- Substage: `4.1 - ELA extraction and DB/API contract` (Track B)
- Branch: `curriculum/phase-4-ela-hardening`
- Owner: (session)
- Start date: 2026-03-29
- Planned end date: (session)

## In-scope

- [x] Stabilize JSON shapes and `schema_version` for `ela_key_learning_summary` and `ela_lesson_plan_structured`; golden tests in `tests/test_ela_summary_table.py` and `tests/test_ela_lesson_plan_table.py` (gate: `test-gate-4-1-pytest-ela.txt`)
- [x] Representative Grade 3 ELA sample unit(s) validated; standards/procedure boundaries; fidelity vs Math baseline where comparable (`verify_curriculum_db.py`, phase pytest slice)
- [x] Scraper SSOT under `docs/scrapers/` — no doc edits required this session (no parser/schema change)
- [x] Single `ingest_to_curriculum` path via `SubjectConfig` and ELA modules (no speculative UI work)

## Out-of-scope guardrails

- [x] Full cross-grade ELA matrix (Phase 5) — not started
- [x] Navigator UI restyle / ELA Explorer template work deferred to Phase 4.2
- [x] [LOCAL_FIRST_LINKS_BACKLOG.md](../../LOCAL_FIRST_LINKS_BACKLOG.md) and [MATH_LESSON_PORTAL_AND_TEACHER_GUIDE_UX.md](../../MATH_LESSON_PORTAL_AND_TEACHER_GUIDE_UX.md) — deferred (see wrap-up)

## Test gate #1 (pre-refactor)

- Commands:
  - `python -m pytest tests/ -m unit -q` (CI baseline; ELA golden tests are not in `-m unit`)
  - `python tools/scraper/verify_curriculum_db.py`
  - `python -m pytest tests/test_ela_summary_table.py tests/test_ela_lesson_plan_table.py -q`
  - `python -m pytest tests/test_grade3_ela_ingest_smoke.py tests/test_math_fidelity_helpers.py tests/test_ingest_report_failure_codes.py tests/test_curriculum_gaps.py -q`
- Result:
  - [x] Pass
  - [ ] Fail
- Evidence paths: [PHASE_4_1_WRAP_UP.md](./PHASE_4_1_WRAP_UP.md), `test-gate-4-1-*.txt` in this folder

## Refactor pass (only if test gate #1 passes)

- Deferred unless this session introduces duplication in touched files; follow `docs/refactor/plans/` if a touched file has a plan.

## Test gate #2 (post-refactor)

- Same commands as gate #1 when a refactor pass runs; otherwise not required for 4.1-only validation session.

## Rules compliance check (.cursor/rules)

- [x] SSOT
- [x] DRY
- [x] KISS
- [x] YAGNI
- [x] SOLID
- [x] README architecture alignment

## Merge and push checklist

- [x] Phase 4.1 exit criteria achieved (gates green; see wrap-up)
- [x] Evidence archived under this folder
- [ ] Branch merge/push per team process (not automatic in this session)

## End-of-phase session wrap-up

See [PHASE_4_1_WRAP_UP.md](./PHASE_4_1_WRAP_UP.md).

### Very short prompt for next session (Phase 4.2)

`Start Phase 4.2: execute docs/curriculum/PHASE_EXECUTION_TEMPLATE.md for ELA navigator UI template (Track B), run test gate #1, implement in-scope only, and report PASS/BLOCKED with evidence paths.`

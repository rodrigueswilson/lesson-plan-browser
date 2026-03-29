# Phase Execution Template

## Phase metadata

- Phase: `4 - ELA hardening (Grade 3 ELA sample; substages 4.1 / 4.2)`
- Branch: `curriculum/phase-4-ela-hardening` (per [PHASED_ROLLOUT_PLAN.md](../../PHASED_ROLLOUT_PLAN.md))
- Owner: AI coding agent + Rodrigo
- Start date: 2026-03-27
- Closed: 2026-03-28

## In-scope

- [x] Onboard one Grade 3 ELA unit sample set (stable unit id `ELA_3_U8_sample`, seed + reingest tooling; ingest via synthesized Unit 8 tab DOCX from `.docs-api.json`, 2026-03-28)
- [x] Validate standards/procedure boundaries for ELA-specific patterns (parser: ELA lesson title groups, ELA section keys on lesson payload, `unique_lessons` considers ELA fields; verify: optional Grade 3 ELA `standards_structured` gate when such a unit exists)
- [x] Compare fidelity and section coverage against Math baseline (shared `standards_structured` expectation in verify for the first Grade 3 ELA unit when present; Math unit 2 checks unchanged)
- [x] **4.2** Subject-aware lesson detail in `lesson-plan-browser/frontend/src/components/CurriculumExplorer.tsx` (`ela_key_learning_summary`, `ela_lesson_plan_structured`); see [PHASE_4_UI_ELA_ACCEPTANCE.md](./PHASE_4_UI_ELA_ACCEPTANCE.md)

## Out-of-scope guardrails

- [x] Broad multi-grade ELA rollout not done in this session
- [x] Full narrative merge heuristics for ELA (no Math-only soft phrase check applied to ELA)

## Test gate #1 (pre-refactor)

- Commands:
  - `python tools/scraper/verify_curriculum_db.py`
  - `python -m pytest tests/test_grade3_ela_ingest_smoke.py tests/test_math_fidelity_helpers.py tests/test_ingest_report_failure_codes.py tests/test_curriculum_gaps.py -q`
- Result:
  - [x] Pass
  - [ ] Fail
- Evidence path:
  - `docs/curriculum/acceptance-evidence/phase-4/test-gate-1-verify_curriculum_db-pre.txt`
  - `docs/curriculum/acceptance-evidence/phase-4/test-gate-1-verify_curriculum_db-post.txt`
  - `docs/curriculum/acceptance-evidence/phase-4/test-gate-1-pytest-phase-deps-pre.txt`
  - `docs/curriculum/acceptance-evidence/phase-4/test-gate-1-pytest-post.txt`

## Refactor pass (only if test gate #1 passes)

- Refactor items:
  - [x] Extracted `lessonDetailPresentationFlags()` in `CurriculumExplorer.tsx` (single place for ELA vs Math procedure UI flags; Phase 4 scoped)
  - [ ] DRY cleanup (shared DDL for isolated DB tests) — **deferred**, out of phase scope
  - [ ] Broader SRP/SOLID cleanup — **deferred**
- Notes:
  - `ingest_to_curriculum` uses `CurriculumDatabase(self.db_path)` so `RecursiveTableParser(db_path=...)` is honored (fixes silent writes to the default DB path).

## Test gate #2 (post-refactor)

- Commands (same slice as gate #1):
  - `python tools/scraper/verify_curriculum_db.py`
  - `python -m pytest tests/test_grade3_ela_ingest_smoke.py tests/test_math_fidelity_helpers.py tests/test_ingest_report_failure_codes.py tests/test_curriculum_gaps.py -q`
- Result:
  - [x] Pass
  - [ ] Fail
- Evidence path:
  - `docs/curriculum/acceptance-evidence/phase-4/test-gate-2-verify_curriculum_db-post-refactor.txt`
  - `docs/curriculum/acceptance-evidence/phase-4/test-gate-2-pytest-post-refactor.txt`

## 4.1 operator ingest (real DOCX)

- [x] **Executed 2026-03-28:** synthesized Unit 8 DOCX from Docs API JSON (`gdoc_tab_to_docx.py`, tab `t.2plykckkv6ev`) → `reference_docs/scraped/grade3_ela_exports/Grade3_ELA_Unit8_from_api_tab.docx`, then `reingest_grade3_ela_sample.py` into `data/curriculum.db` (`ELA_3_U8_sample`, 12 lessons). Provenance URL includes Unit 8 tab.
- Ingest report: `ingest_reports/2026-03-28T22-16-20Z_1a609674.json`
- Post-ingest verify + pytest slice: archived in `verify-after-unit8-reingest-2026-03-28.txt`
- **Note:** Artifact is API-synthesized DOCX, not a browser-native Word download; refresh JSON + regenerate if the live Google Doc changes materially.

## Rules compliance check (.cursor/rules)

- [x] SSOT (`SubjectConfig` remains single source for ELA anchors/patterns; verify gates reference DB state)
- [x] DRY (minimal duplication; seed/reingest mirror Math tooling pattern)
- [x] KISS
- [x] YAGNI (no multi-unit ELA matrix)
- [x] SOLID
- [x] README architecture alignment

## Merge and push checklist

- [x] Phase exit criteria achieved for **4.2 UI** and double-pass verify + pytest (gates #1 archived earlier + gate #2 this session)
- [x] No open critical defects (none known from executed tests)
- [x] Evidence archived under `docs/curriculum/acceptance-evidence/phase-4/`
- [x] LOC snapshot refreshed (`python tools/refactor/count_loc.py --markdown` → `loc-snapshot-phase-4-exit.txt`)
- [ ] Refactor tracking updated if applicable (no change to `REFACTORING_PRIORITIES_AND_TOOLS.md` this session)
- [x] Branch merged to `master` (fast-forward 2026-03-28)
- [x] Pushed to GitHub (`master` and `curriculum/phase-4-ela-hardening`)

## End-of-phase session wrap-up (mandatory)

- Result: `PASS` (4.2 + quality gates; Unit 8 sample re-ingested from synthesized DOCX 2026-03-28)
- One-line completion summary: Phase 4.2 delivers ELA-aware lesson detail in Curriculum Explorer; verify and phase pytest slice pass twice (gate #1 evidence on file + gate #2 post-refactor); `ELA_3_U8_sample` refreshed from tab `t.2plykckkv6ev` via `gdoc_tab_to_docx` + reingest.
- Blockers (max 3 bullets):
  - None for sample ingest; optional follow-up is a browser-native DOCX spot-check for layout fidelity vs synthesis.
- Evidence paths:
  - `docs/curriculum/acceptance-evidence/phase-4/test-gate-1-verify_curriculum_db-pre.txt`
  - `docs/curriculum/acceptance-evidence/phase-4/test-gate-1-verify_curriculum_db-post.txt`
  - `docs/curriculum/acceptance-evidence/phase-4/test-gate-1-pytest-phase-deps-pre.txt`
  - `docs/curriculum/acceptance-evidence/phase-4/test-gate-1-pytest-post.txt`
  - `docs/curriculum/acceptance-evidence/phase-4/test-gate-2-verify_curriculum_db-post-refactor.txt`
  - `docs/curriculum/acceptance-evidence/phase-4/test-gate-2-pytest-post-refactor.txt`
  - `docs/curriculum/acceptance-evidence/phase-4/loc-snapshot-phase-4-exit.txt`
  - `docs/curriculum/acceptance-evidence/phase-4/PHASE_4_UI_ELA_ACCEPTANCE.md`
  - `lesson-plan-browser/frontend/src/components/CurriculumExplorer.tsx`
  - `docs/curriculum/acceptance-evidence/phase-4/verify-after-unit8-reingest-2026-03-28.txt`
  - `ingest_reports/2026-03-28T22-16-20Z_1a609674.json`
  - `reference_docs/scraped/grade3_ela_exports/Grade3_ELA_Unit8_from_api_tab.docx` (local synthesized input; see evidence file for regenerate command)

### Very short prompt for next phase

`Start Phase 5: execute docs/curriculum/PHASE_EXECUTION_TEMPLATE.md for cross-grade representative sample, run test gate #1, implement in-scope only, and report PASS/BLOCKED with evidence paths.`

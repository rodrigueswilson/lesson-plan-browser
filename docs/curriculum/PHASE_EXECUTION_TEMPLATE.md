# Phase Execution Template

Use this template at the start of every phase branch.

## Phase metadata

- Phase: `<number and name>`
- Substage (optional): e.g. `4.1` / `4.2` for Phase 4 ELA milestones documented in [PHASED_ROLLOUT_PLAN.md](./PHASED_ROLLOUT_PLAN.md).
- Branch: `curriculum/phase-<n>-<scope>` (Phase 3 example: `curriculum/phase-3-g3-math-corpus`; Phase 4 example: `curriculum/phase-4-ela-hardening`)
- Owner:
- Start date:
- Planned end date:
- G3 Math corpus (Phase 3 only): link or path to the **ingest checklist** under `docs/curriculum/acceptance-evidence/` that lists each `scraped_registry.json` → `Grade 3` → `Math` row in scope.

## In-scope

- [ ] Item 1
- [ ] Item 2

## Out-of-scope guardrails

- [ ] Guardrail 1
- [ ] Guardrail 2

## Test gate #1 (pre-refactor)

- Commands:
  - `python tools/scraper/verify_curriculum_db.py`
  - `<phase-specific tests>`
- Result:
  - [ ] Pass
  - [ ] Fail
- Evidence path:

## Refactor pass (only if test gate #1 passes)

- Refactor items:
  - [ ] DRY cleanup
  - [ ] SRP/SOLID cleanup
- Notes:

If a touched file has a plan in `docs/refactor/plans/`, follow `refactoring-workflow.mdc`:
- one extraction per commit,
- run plan test command before each commit.

Refactor tools guidance:
- Prefer Rope/IDE rename for symbol-safe renames.
- Use Bowler/LibCST for mechanical multi-file edits.
- Keep manual edits for large structural splits.
- Review diffs before applying bulk codemods.

## Test gate #2 (post-refactor)

- Commands (same as gate #1):
  - `python tools/scraper/verify_curriculum_db.py`
  - `<phase-specific tests>`
- Result:
  - [ ] Pass
  - [ ] Fail
- Evidence path:

## Rules compliance check (.cursor/rules)

- [ ] SSOT
- [ ] DRY
- [ ] KISS
- [ ] YAGNI
- [ ] SOLID
- [ ] README architecture alignment

## Merge and push checklist

- [ ] Phase exit criteria achieved
- [ ] No open critical defects
- [ ] Evidence archived
- [ ] LOC snapshot refreshed (`python tools/refactor/count_loc.py --markdown`)
- [ ] Refactor tracking updated if applicable (`docs/refactor/REFACTORING_PRIORITIES_AND_TOOLS.md`)
- [ ] Branch merged
- [ ] Pushed to GitHub

## End-of-phase session wrap-up (mandatory)

- Result: `PASS` or `BLOCKED`
- One-line completion summary:
- Blockers (max 3 bullets):
- Evidence paths:

### Very short prompt for next session

`Start Phase <NEXT_PHASE_NUMBER>: execute docs/curriculum/PHASE_EXECUTION_TEMPLATE.md for <NEXT_PHASE_SCOPE>, run test gate #1, implement in-scope only, and report PASS/BLOCKED with evidence paths.`

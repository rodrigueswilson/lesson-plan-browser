# Next Session Prompt Snippets (Very Short)

Use one line only. Replace placeholders.

## Generic

`Start Phase <N>: execute docs/curriculum/PHASE_EXECUTION_TEMPLATE.md for <scope>, run test gate #1, implement in-scope only, and report PASS/BLOCKED with evidence paths.`

## Examples

`Start Phase 1: execute docs/curriculum/PHASE_EXECUTION_TEMPLATE.md for provenance and fidelity foundation, run test gate #1, implement in-scope only, and report PASS/BLOCKED with evidence paths.`

`Start Phase 2: execute docs/curriculum/PHASE_EXECUTION_TEMPLATE.md for unit intro parity and UX navigation hardening, run test gate #1, implement in-scope only, and report PASS/BLOCKED with evidence paths.`

`Start Phase 3: execute docs/curriculum/PHASE_EXECUTION_TEMPLATE.md for same-subject template resilience, run test gate #1, implement in-scope only, and report PASS/BLOCKED with evidence paths.`

`Start Phase 4.1: execute docs/curriculum/PHASE_EXECUTION_TEMPLATE.md for ELA extraction and structured lesson plan schema (Track B), run test gate #1, implement in-scope only, and report PASS/BLOCKED with evidence paths.`

---

## Current recommended trigger (2026-03-28)

Phase 3 Grade 3 Math full-corpus ingest is **documented complete** in `docs/curriculum/acceptance-evidence/phase-3/G3_MATH_PHASE3_INGEST_CHECKLIST.md`. Next work is **Phase 4.1 (ELA)** plus any **navigator integration** follow-ups already parked in backlog docs.

**Paste into a new chat:**

```text
Start Phase 4.1: execute docs/curriculum/PHASE_EXECUTION_TEMPLATE.md for ELA extraction and structured lesson plan schema (Track B), run test gate #1, implement in-scope only, and report PASS/BLOCKED with evidence paths. First: read docs/curriculum/PHASED_ROLLOUT_PLAN.md for Phase 4.1 scope; run python -m pytest tests/ -m unit -q; then implement only in-scope items. Revisit docs/curriculum/LOCAL_FIRST_LINKS_BACKLOG.md and docs/curriculum/MATH_LESSON_PORTAL_AND_TEACHER_GUIDE_UX.md only where they block Phase 4.1 or are explicitly in scope; otherwise leave deferrals documented.
```

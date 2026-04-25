# Curriculum Documentation Set

This folder is the implementation control set for delivering a Unit-Complete curriculum pipeline without ad-hoc changes.

## Documents

- `IMPLEMENTATION_PLAYBOOK.md` - execution order and delivery gates
- `PHASED_ROLLOUT_PLAN.md` - full phase boundaries and scaling plan through Grade 8
- `SAMPLE_MATRIX_AND_ADAPTATION_ALERTS.md` - concrete unit extraction order and parser insufficiency alert model
- `PHASE_EXECUTION_TEMPLATE.md` - branch/test/refactor/retest/merge checklist per phase
- `QUALITY_GATES.md` - pass/fail criteria
- `PROVENANCE_AND_LINEAGE.md` - required source metadata model
- `LOCAL_SOURCE_FILES.md` - optional on-disk Google Doc exports (`CURRICULUM_LOCAL_FILES_ROOT`) for local-first Source URL / resource links
- `LOCAL_FIRST_LINKS_BACKLOG.md` - **open**: Drive vs local link behavior; revisit at end of Phase 4.2 per `PHASED_ROLLOUT_PLAN.md`
- `MATH_LESSON_PORTAL_AND_TEACHER_GUIDE_UX.md` - Math: portal lesson link (pass-through) vs. teacher guide PDF (prominent, local); future PDF extraction for pacing/plans
- `KNOWN_UI_LIMITS.md` - deferred Explorer UI heuristics (e.g. in-cell title enrichment)
- `UI_NAVIGATION_SPEC.md` - teacher-first navigation behavior
- `TEST_PROTOCOL_UNIT_ACCEPTANCE.md` - end-to-end acceptance protocol
- `PRIOR_ART_RESEARCH_SUBSTAGE.md` - Phase 0 sub-stage: prior-art research topics, documentation, and code integration rules
- `research-notes/` - dated memos and source logs from prior-art sessions

## Recommended use

1. Start with `IMPLEMENTATION_PLAYBOOK.md`.
2. Lock phase boundaries in `PHASED_ROLLOUT_PLAN.md`.
3. Implement only what is needed to pass `QUALITY_GATES.md`.
4. Run `TEST_PROTOCOL_UNIT_ACCEPTANCE.md` and archive evidence.
5. Mark a unit complete only after all gates pass.

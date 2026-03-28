# Phase 4.2 — ELA-aware lesson detail (acceptance notes)

## Implementation

- **File:** `lesson-plan-browser/frontend/src/components/CurriculumExplorer.tsx`
- **API fields:** `ela_key_learning_summary` and `ela_lesson_plan_structured` (JSON strings) are parsed when present.
- **Summary of Key Learning:** Renders matrix-derived fields (learning intention / success criteria, daily task title+body, content and strategies HTML, standards mentions).
- **Structured ELA lesson plan:** Renders NJSLS block, key questions / instructional routines, vocabulary / resources, ELA procedure buckets (anticipatory set, learning procedures, engagement, daily instructional task), differentiation / misconceptions — **not** mapped through Math-only warmup/activity/cooldown banding.
- **De-duplication:** When structured ELA provides learning intention / success criteria / daily task / procedure buckets, the generic Teacher Objectives, Student Objectives, Daily Tasks band, standalone Success Criteria, and streamed `procedure_html` banding are suppressed to avoid double content. Math lessons without these fields keep the previous layout.

## Regression (Math)

- Lessons **without** `ela_lesson_plan_structured` procedure buckets still use existing `procedure_html` segmentation (warm-up / activity / etc.) when headings match, and JSON `procedure` steps when applicable.

## Manual UI check (recommended)

1. Open a **Grade 3 Math** unit lesson with procedure HTML: confirm banded “Instructional Steps & Activities” still appears.
2. Open a lesson with populated `ela_key_learning_summary` / `ela_lesson_plan_structured` (e.g. ELA sample unit after ingest): confirm teal “Summary of Key Learning” and cyan “ELA lesson plan (structured)” blocks.

Screenshots were not captured in this automated session; add under this folder if needed for audit.

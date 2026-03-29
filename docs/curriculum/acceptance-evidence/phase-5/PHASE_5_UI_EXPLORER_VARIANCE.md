# Phase 5 – CurriculumExplorer (Phase 4.2 template) vs variance classes

**Component SSOT:** `lesson-plan-browser/frontend/src/components/CurriculumExplorer.tsx`.  
**Prior manual sign-off pattern:** `docs/curriculum/acceptance-evidence/phase-4/PHASE_4_UI_ELA_ACCEPTANCE.md`.

## Build gate

`npm run build` under `lesson-plan-browser/frontend` — see `test-gate-5-1-lesson-browser-build.txt` and `test-gate-5-2-lesson-browser-build.txt`.

## Variance class → sample lesson IDs (DB-backed today)

| Variance class | Representative lesson (unit) | ELA summary matrix (`ela_key_learning_summary`) | ELA structured plan (`ela_lesson_plan_structured`) |
|----------------|------------------------------|--------------------------------------------------|------------------------------------------------------|
| `math_im_elementary` | Any lesson under `Math_3_U2_1hBoK4uk` | N/A (Math payload) | N/A |
| `ela_compendium_tabs` (G3 exercised) | First lesson under `ELA_3_U8_sample` | Present | Present |
| `ela_partial_structured` (G2 edge) | First lesson under `ELA_2_U8_sample` | Present | Absent on sampled rows |

## Manual Explorer checklist (one lesson per class above)

For each row: open Curriculum Explorer, select grade/subject/unit, open lesson detail — confirm Math procedure UI still works for Math classes; for ELA confirm summary + structured sections render without mapping ELA into Math-only bands when content is ELA-shaped. Record screenshots in a future evidence pass if needed for audit.

**Status this session:** Build-only gate recorded; interactive Explorer pass delegated to operator (same rubric as Phase 4.2 table).

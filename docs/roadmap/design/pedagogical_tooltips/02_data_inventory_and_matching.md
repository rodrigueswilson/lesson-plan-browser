# Data inventory and matching

**Status:** Phase A inventory (initial fill from schema + fixtures)  
**Sources:** [`backend/lesson_schema_models.py`](../../../../backend/lesson_schema_models.py), [`backend/lesson_schema_vocabulary.py`](../../../../backend/lesson_schema_vocabulary.py), [`backend/lesson_schema_support.py`](../../../../backend/lesson_schema_support.py), [`tests/fixtures/valid_lesson_minimal.json`](../../../../tests/fixtures/valid_lesson_minimal.json), [`strategies_pack_v2/_index.json`](../../../../strategies_pack_v2/_index.json), [`wida/wida_framework_reference.json`](../../../../wida/wida_framework_reference.json)

---

## 1. Authoritative data for lookups

### 1.1 Strategies (bilingual teaching strategies)

| Source | Role |
|--------|------|
| [`strategies_pack_v2/_index.json`](../../../../strategies_pack_v2/_index.json) | Category index, `strategy_id` allow-list |
| `strategies_pack_v2/core/*.json`, `specialized/*.json` | Per-strategy `id`, `strategy_name`, `aliases`, `definitions.short_en`, `definitions.long_en`, etc. |

**Stable key for UI:** `strategy_id` (snake_case, matches `EllStrategy.strategy_id` in schema).

### 1.2 WIDA (lightweight reference JSON)

| Source | Role |
|--------|------|
| [`wida/wida_framework_reference.json`](../../../../wida/wida_framework_reference.json) | `eld_standards`, `proficiency_levels`, `key_language_uses`, `communication_modes`, `grade_clusters`, `dimensions_of_language`, templates |

**Note:** Deeper Can Do / 2020 expectation rows are planned under [WIDA_FRAMEWORK_INGESTION_AND_USE.md](../WIDA_FRAMEWORK_INGESTION_AND_USE.md); v1 tooltips can still use this file for glosses.

---

## 2. `lesson_json` fields where strategies or WIDA terms appear

Derived from Pydantic models (`DayPlanSingleSlot` / `SlotPlan` and nested types). All are **string** (or list of strings) content rendered through markdown in the shared UI unless noted.

| Area | Field path | Strategy mentions | WIDA / ELD mentions |
|------|------------|--------------------|---------------------|
| Objectives | `objective.content_objective` | Possible in prose (e.g. pedagogy names) | Uncommon |
| Objectives | `objective.student_goal` | Rare | Domains: listening, reading, speaking, writing |
| Objectives | `objective.wida_objective` | Frequent (e.g. "cognate awareness", "sentence frames") | **ELD-XX.grade.KeyUse.Domain[/Domain]**; "WIDA levels X–Y" |
| Unit | `unit_lesson` | Rare | Rare |
| Anticipatory | `anticipatory_set.original_content` | Possible | Possible |
| Anticipatory | `anticipatory_set.bilingual_bridge` | Frequent (preview strategies, cognates) | Possible |
| Vocabulary | `vocabulary_cognates[].english` / `portuguese` / `relevance_note` | Note text only | Rare |
| Sentence frames | `sentence_frames[].english`, `portuguese` | Possible in frame text | `proficiency_level` groups (`levels_1_2`, etc.) imply WIDA bands |
| Tailored | `tailored_instruction.original_content` | Frequent | Possible |
| Co-teaching | `co_teaching_model.rationale` | Possible | WIDA band language |
| Co-teaching | `co_teaching_model.wida_context` | Possible | **Levels X–Y** typical |
| Co-teaching | `co_teaching_model.phase_plan[].bilingual_teacher_role`, `primary_teacher_role`, `details` | Frequent ("Levels 2-3") | Proficiency refs |
| Co-teaching | `co_teaching_model.implementation_notes[]` | Possible | Possible |
| ELL Support | `ell_support[].strategy_id` | **Structured SSOT key** | — |
| ELL Support | `ell_support[].strategy_name` | Display title; may vary from pack `strategy_name` (see fixture) | — |
| ELL Support | `ell_support[].implementation` | Prose; repeats strategy ideas | Possible |
| ELL Support | `ell_support[].proficiency_levels` | — | **Structured** ("Levels 2-5") |
| Special needs | `special_needs_support[]` | Possible | Possible |
| Materials | `materials[]` | Possible ("sentence frame strips") | Rare |
| Misconceptions | `misconceptions.original_content` | Possible | Rare |
| Misconceptions | `misconceptions.linguistic_note.*` | `prevention_tip` may say "sentence frames" | Rare |
| Assessment | `assessment.primary_assessment` | Rare | Rare |
| Assessment | `bilingual_overlay.wida_mapping` | Possible | **Dense** (ELD + levels) |
| Assessment | `bilingual_overlay.supports_by_level.*` | Frequent | WIDA level band labels in description |
| Assessment | `bilingual_overlay.scoring_lens` | Possible | Possible |
| Homework | `homework.original_content`, `family_connection` | Possible | Possible |

**Fixture note:** [`valid_lesson_minimal.json`](../../../../tests/fixtures/valid_lesson_minimal.json) shows `ell_support[].strategy_name` as both exact pack titles ("Cognate Awareness") and a longer variant ("Graphic Organizers for Language Learning"), so **matching should prefer `strategy_id`** when present.

---

## 3. Matching approaches (candidates)

| Approach | Pros | Cons |
|----------|------|------|
| **A. Structured only** | Wrap tooltips for `ell_support` titles and `strategy_id`-linked rows only; optionally scan `implementation` for nothing | Misses strategy names only in objectives body |
| **B. Dictionary scan in prose** | Catches "graphic organizers" in `wida_objective` | False positives (English phrase overlaps); alias collisions |
| **C. Post-processed spans from LLM** | Precise offsets if schema adds markers later | Schema and generation changes; out of scope for research-only phase |

**Risk register**

| Risk | Example | Mitigation idea |
|------|---------|-----------------|
| Paraphrase | LLM says "bilingual word wall" vs pack id `bilingual_word_walls` | Prefer structured `strategy_id`; fuzzy match only with confidence threshold |
| Name collision | "Levels" in non-WIDA sense | Require "WIDA" or "Level(s) N" pattern for band tooltips |
| ELD code variants | `ELD-LA.2-3` vs `ELD-SS.6-8` | Normalize with one regex; map capture groups to `eld_standards` + `grade_clusters` |
| Markdown | `**graphic organizers**` | Annotate after markdown parse or use remark plugin (see [04](./04_technical_spikes_checklist.md)) |

---

## 4. Next steps for Phase A

- [ ] Spot-check [`tests/fixtures/wilson_lesson_sample.json`](../../../../tests/fixtures/wilson_lesson_sample.json) for additional phrasing variants.
- [ ] Confirm list of rendered fields in [`LessonDetailView.tsx`](../../../../shared/lesson-browser/src/components/LessonDetailView.tsx) matches the table above (no extra paths).

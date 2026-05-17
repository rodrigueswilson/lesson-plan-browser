# Investigation: uniform non-instructional / missing objectives (25 slots)

This document records codebase findings for the investigation phases (A–F). It is not the project README.

## Phase A: Pipeline routing and log markers

**Sequential path** (`PARALLEL_LLM_PROCESSING` false or single slot): [`week_flow.py`](../../tools/batch_processor_pkg/week_flow.py) calls `week_flow_sequential`, which uses [`slot_flow.process_one_slot`](../../tools/batch_processor_pkg/slot_flow.py). Extraction calls `get_available_days_from_content(content)` after `extract_subject_content_for_slot`.

**Parallel path** (`PARALLEL_LLM_PROCESSING` and `len(slots) > 1`): [`week_flow_parallel.run_parallel_path`](../../tools/batch_processor_pkg/week_flow_parallel.py) calls `_extract_slots_parallel_db` → [`extraction.extract_slots_parallel_db`](../../tools/batch_processor_pkg/extraction.py), which groups slots by primary file and runs [`combined_original.process_file_group`](../../tools/batch_processor_pkg/combined_original.py) per file. Fresh extraction must set `available_days` via `get_available_days_from_content(content_data)` (not a missing-key default to `[]`).

**Log / telemetry strings to grep in production logs:**

| Key | Source |
|-----|--------|
| `instructional_weekdays_unknown_no_table_content` | [`slot_flow.py`](../../tools/batch_processor_pkg/slot_flow.py) |
| `instructional_weekdays_zero_skip_llm` | [`slot_flow.py`](../../tools/batch_processor_pkg/slot_flow.py) |
| `parallel_transform_skip_llm_zero_instructional` | [`transform.py`](../../tools/batch_processor_pkg/transform.py) |

**Outcome:** Multi-slot parallel runs always used file-group extraction; they did not use `slot_flow`’s inference unless going through sequential processing.

## Phase B: Default empty list vs inference

**Finding:** `extract_subject_content_for_slot` does not populate `available_days` on the returned dict. Using `.get("available_days", [])` treated “missing” as **zero instructional days**, which matches `transform_slot_with_llm`’s stub branch (`available_days is not None and len == 0`).

**Fix applied:** [`combined_original.py`](../../tools/batch_processor_pkg/combined_original.py) now sets `context.available_days = get_available_days_from_content(content_data)`.

**DB / `has_no_school`:** [`persistence.py`](../../tools/batch_processor_pkg/persistence.py) sets `has_no_school` when `available_days is not None and len(available_days) == 0`. That flag means “non-instructional week inference,” not calendar “No School.” Inspect `original_lesson_plans.available_days` for affected `week_of` + slot when auditing production data.

**Operational check:** Compare stored `available_days` to `get_available_days_from_content(content_json)` for the same row (SQL or script); mismatches after the fix indicate rows extracted before the fix or cache issues.

## Phase C: Per-slot inference

Inference lives in [`instructional_day.py`](../../tools/docx_parser/instructional_day.py): `infer_instructional_weekdays_from_table_content` → `is_instructional_lesson_day` (no-school, assessment patterns, then `substantive_day_text`).

**Update:** Classification uses `_day_text_for_instructional_inference`: prefer Unit/Lesson and Objective-style columns when present, so extra columns (e.g. district “testing week” notes) do not poison the whole day when the lesson cell is normal. If no such columns have text, behavior falls back to joining all cell values (legacy).

**Independent failure modes per slot:**

- Assessment regex false positives on lesson prose.
- `substantive_day_text` too strict for short unit lines.
- Image-heavy cells → empty joined text.
- `find_slot_by_subject` resolving the wrong row (empty or calendar-heavy cells).
- `"All Days"` key → legacy `["monday"]` only.

**Tests:** [`tests/test_instructional_days.py`](../../tests/test_instructional_days.py), [`tests/test_combined_original_available_days.py`](../../tests/test_combined_original_available_days.py).

## Phase D: Cache amplification

[`combined_original.py`](../../tools/batch_processor_pkg/combined_original.py): On cache hit (`db_record` newer than file mtime), `context.available_days = db_record.available_days` without recomputing from `content_json`. Poisoned `[]` persists until `refresh_source_documents` forces re-extract (skips cache when true in the refresh path) or manual DB cleanup / delete cached row.

## Phase E: UI / plan identity

[`LessonPlanBrowser.tsx`](../../shared/lesson-browser/src/components/LessonPlanBrowser.tsx) / [`WeekView.tsx`](../../shared/lesson-browser/src/components/WeekView.tsx): Plans load via `lessonApi.getPlanDetail(plan.id, ...)` per matched plan. Each tile uses the schedule entry’s resolved `plan.id`; duplicate tiles showing the same JSON usually indicate schedule/plan association bugs, not batch `available_days` logic.

## Phase F: Other stub / skip paths in transform

[`transform.py`](../../tools/batch_processor_pkg/transform.py) `transform_slot_with_llm`:

1. Reuses existing `context.lesson_json` if set (early return).
2. Returns early if `context.error`.
3. If `context.extracted_content == "__NO_SCHOOL_WEEK__"`, builds minimal week with `unit_lesson: "No School"` for all days (not the non-instructional assessment stub).
4. If `available_days is not None and len == 0`, full-week `build_non_instructional_week_lesson_json`.
5. Otherwise LLM `transform_lesson`.

[`slot_flow.py`](../../tools/batch_processor_pkg/slot_flow.py): Entire-document no-school short-circuits to `build_no_school_day_json` before `available_days` handling.

## Decision table (summary)

| Cause | Symptom pattern | Mitigation |
|-------|-----------------|------------|
| B: default `[]` in combined-original | All parallel slots full-week non-instructional stub | Fixed: derive with `get_available_days_from_content` |
| C: inference returns `[]` | Many slots, honest “no instructional day” from primary text | Tune patterns / substantive gate; inspect `table_content` |
| D: DB cache | Old wrong `available_days` after code fix | Re-extract with refresh or invalidate cache rows |
| E: UI plan mix-up | Wrong JSON despite correct DB | Debug plan–schedule mapping |
| F: `__NO_SCHOOL_WEEK__` | All days `No School`, not assessment label | Trace extraction flagging full week no school |

# Instructional days reliability — implementation deliverables (Phases 1–7)

This file records what was implemented to satisfy the **instructional days reliability** plan (see `.cursor/plans/` for the exact markdown file). It does not replace [README.md](../../README.md).

## Phase 0 — Branch inventory

See [instructional_days_phase0_inventory.md](instructional_days_phase0_inventory.md) and [uniform_non_instructional_investigation.md](uniform_non_instructional_investigation.md).

## Phase 1 — Reproduce and measure

**Tool:** [`tools/diagnostics/dump_instructional_inference.py`](../../tools/diagnostics/dump_instructional_inference.py)

- Pass a JSON file with `table_content` (or a dict whose top-level keys are weekday names).
- Prints `get_available_days_from_content` result, per-day **primary** text used for inference, optional legacy full-join when it differs, and `is_instructional_lesson_day` per day.

**Log search (runtime):** `instructional_weekdays_unknown_no_table_content`, `instructional_weekdays_zero_skip_llm` ([`slot_flow.py`](../../tools/batch_processor_pkg/slot_flow.py)), `parallel_transform_skip_llm_zero_instructional` ([`transform.py`](../../tools/batch_processor_pkg/transform.py)).

**DB / API:** Export `original_lesson_plans.content_json` (or `table_content` slice) for `week_of` + `slot_number` and run the script on the saved file.

## Phase 2 — Plumbing audit

**Written contract:** [`available_days_contract.md`](available_days_contract.md) (semantics of `None` vs `[]` vs non-empty list).

**Rule:** `available_days` must be **`[]` only** when [`infer_instructional_weekdays_from_table_content`](../../tools/docx_parser/instructional_day.py) returns an empty list for real `table_content` — not when a key is missing from a dict.

**Verified:** No `content_data.get("available_days", [])` in [`tools/batch_processor_pkg/`](../../tools/batch_processor_pkg/) or `backend/` (production code). [`combined_original.py`](../../tools/batch_processor_pkg/combined_original.py) uses `get_available_days_from_content`.

**Tests:** [`tests/test_combined_original_available_days.py`](../../tests/test_combined_original_available_days.py) (if present in working tree).

## Phase 3 — Inference (primary column text)

**Change:** [`instructional_day.py`](../../tools/docx_parser/instructional_day.py) introduces `_day_text_for_instructional_inference`, preferring Unit/Lesson/Objective-style columns (aligned with label heuristics in [`slot_flow_extract.get_original_unit_lessons_and_objectives`](../../tools/batch_processor_pkg/slot_flow_extract.py)). If none match, behavior falls back to joining all cell values.

**Tests:** [`tests/test_instructional_days.py`](../../tests/test_instructional_days.py) — includes `test_infer_instructional_weekdays_notes_column_does_not_poison_unit_lesson`.

## Phase 4 — Partial instructional weeks (LLM)

**Source of truth:** [`backend/llm/prompt_builder.py`](../../backend/llm/prompt_builder.py)

- When `available_days` is set and has **fewer than five** entries, structured-output prompts restrict JSON day keys to **those days** and instruct the model not to emit other weekdays; the backend may add missing days programmatically (see comments in `build_prompt`).
- [`backend/llm_service.py`](../../backend/llm_service.py) passes `available_days` through `run_transform_lesson` into prompt building.

**Acceptance:** Product expectation — instructional days get full bilingual detail; other weekdays may be placeholders or filled by post-process / validation. Confirm with stakeholders against live outputs after Phase 3 fixes.

## Phase 5 — Cache and operations

**Behavior:** On cache hit, [`combined_original.py`](../../tools/batch_processor_pkg/combined_original.py) may reuse `db_record.available_days` without recomputation until source file is refreshed.

**Runbook:**

1. Deploy code changes.
2. For affected users/weeks, trigger processing with **refresh source documents** (or equivalent API flag) so extraction re-runs and persistence stores new `available_days`.
3. Optionally delete or invalidate stale `original_lesson_plans` rows for that `(user_id, week_of, slot)` if fixes must apply immediately.

## Phase 6 — Exports and stubs

- Objectives omit rules: [`backend/services/objectives/omit.py`](../../backend/services/objectives/omit.py) (import from SSOT `NON_INSTRUCTIONAL_UNIT_LESSON`).
- No School / validation placeholders: [`backend/llm/validation.py`](../../backend/llm/validation.py); builders [`slot_flow_no_school.py`](../../tools/batch_processor_pkg/slot_flow_no_school.py).

**Verify:** `pytest tests/test_objectives_omit_non_instructional.py tests/test_no_school_lesson_json_placeholders.py` when those modules exist.

## Phase 7 — CI, staging, rollout

**Suggested CI:**

```bash
pytest tests/test_instructional_days.py tests/test_combined_original_available_days.py tests/test_transform_available_days_stub.py -v --timeout=120
```

**Staging:** Run a multi-slot parallel batch on a representative week; compare `dump_instructional_inference.py` output from exported `table_content` per slot to logged `available_days`.

**Rollback:** Revert deploy or toggle [`PARALLEL_LLM_PROCESSING`](../../backend/config/) only if operational policy allows sequential fallback during incidents.

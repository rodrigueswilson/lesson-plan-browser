# Contract: `available_days` in the batch / transform pipeline

Single place to read what `get_available_days_from_content` and `context.available_days` **mean**. Code anchors: [`slot_flow_extract.get_available_days_from_content`](../../tools/batch_processor_pkg/slot_flow_extract.py), [`transform.transform_slot_with_llm`](../../tools/batch_processor_pkg/transform.py).

## Return values of `get_available_days_from_content(content)`

| Return | When | Transform behavior (typical) |
|--------|------|------------------------------|
| `None` | `table_content` key **absent** from `content` | **No** “zero instructional” stub from this check; `transform_slot_with_llm` proceeds to LLM path (legacy “all week” in prompts when `available_days` is `None` — see [`prompt_builder.py`](../../backend/llm/prompt_builder.py)). |
| `[]` | `table_content` **present** and [`infer_instructional_weekdays_from_table_content`](../../tools/docx_parser/instructional_day.py) found **no** instructional weekdays | **Full-week** [`build_non_instructional_week_lesson_json`](../../tools/batch_processor_pkg/helpers.py) — **LLM not called** for that slot. |
| `["monday", ...]` | Non-empty list | LLM path; prompt restricts or emphasizes listed days when fewer than five (see `build_prompt`). |

## Forbidden misuse

- Do **not** set `context.available_days = []` when inference **did not run** (e.g. missing key on parser dict). Use **`get_available_days_from_content`** so missing `table_content` yields **`None`**, not `[]`.
- Only **[]** from the inferencer means “explicit zero instructional days.”

## “No School” (calendar) vs “Non-instructional (assessment)” (labels in `lesson_json`)

- **Parser `no_school_days`:** Populated per weekday when calendar-style **closure** text appears in the **same primary-column string** as instructional inference ([`_day_text_for_instructional_inference`](../../tools/docx_parser/instructional_day.py)) — not the full join of all cells. That avoids a **Notes** cell alone marking a day as no school.
- **Finalize / parallel transform:** If a day is in `no_school_days` but that primary text is **assessment-like** (testing) and **not** true no-school closure, the stored day uses [`non_instructional_day_stub()`](../../tools/batch_processor_pkg/helpers.py) (`Non-instructional (assessment)`), not the calendar **No School** stub. See [`day_stub_for_no_school_list_entry`](../../tools/batch_processor_pkg/no_school_stub_pick.py). `SlotProcessingContext.table_content` carries the slot table for this decision in parallel mode.
- **Reprocessing:** After label fixes, re-run processing with **refresh source documents** (or equivalent) for affected `week_of` / slots so `content_json` and `lesson_json` are rebuilt.

## Related docs

- [instructional_days_reliability_deliverables.md](instructional_days_reliability_deliverables.md)
- [uniform_non_instructional_investigation.md](uniform_non_instructional_investigation.md)

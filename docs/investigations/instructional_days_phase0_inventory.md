# Phase 0: Branch and commit inventory (instructional days reliability)

Generated for planning work; re-run `git` commands to refresh.

## References at capture time

| Ref | Commit | Notes |
|-----|--------|--------|
| `master` | `84007a7` | Example tip; run `git rev-parse master` |
| `feature/instructional-days-exams` (`HEAD`) | `f8010b0` | `feat: skip LLM for exam/empty instructional days per slot` |

## Unique commits on feature branch (vs merge-base)

Use:

```bash
git fetch origin  # if applicable
git log master..HEAD --oneline
```

The instructional-days feature is primarily **`f8010b0`** when branching from the curriculum merge stack; verify with `git merge-base master HEAD` and `git log master..HEAD`.

## Must-keep fixes (cherry-pick if branch abandoned)

1. **[`tools/batch_processor_pkg/combined_original.py`](../../tools/batch_processor_pkg/combined_original.py)** — `context.available_days` must be set with **`get_available_days_from_content(content_data)`** (not `.get("available_days", [])`).
2. **`infer_instructional_weekdays_from_table_content`** — prefer **primary lesson columns** for classification when present ([`instructional_day.py`](../../tools/docx_parser/instructional_day.py)); reduces false `[]` when notes columns repeat assessment wording.
3. **Objectives export** — [`backend/services/objectives/omit.py`](../../backend/services/objectives/omit.py) and wired extractors for non-instructional omission.
4. **No School placeholder alignment** — [`slot_flow_no_school.py`](../../tools/batch_processor_pkg/slot_flow_no_school.py) via `no_school_day_stub`; [`backend/llm/validation.py`](../../backend/llm/validation.py) `no_school_placeholder` empty section bodies.
5. **Tests** — [`tests/test_combined_original_available_days.py`](../../tests/test_combined_original_available_days.py), [`tests/test_no_school_lesson_json_placeholders.py`](../../tests/test_no_school_lesson_json_placeholders.py), [`tests/test_objectives_omit_non_instructional.py`](../../tests/test_objectives_omit_non_instructional.py), extended [`tests/test_instructional_days.py`](../../tests/test_instructional_days.py).

## Ship / do not ship

| Item | Recommendation |
|------|----------------|
| `f8010b0` core (skip LLM + stubs) | Ship with Phase 3 inference + plumbing |
| Uncommitted local changes | Commit or stash before branch switch; include combined_original + inference changes |

## README alignment

Batch processing lives under [`tools/batch_processor_pkg/`](../../tools/batch_processor_pkg/) per [README.md](../../README.md).

## Related

- [instructional_days_reliability_deliverables.md](instructional_days_reliability_deliverables.md) — Phases 1–7 implementation notes and commands.

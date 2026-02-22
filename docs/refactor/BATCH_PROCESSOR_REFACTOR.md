# Batch Processor Package Refactor

This document summarizes the refactoring of `tools/batch_processor.py` into a package. Full plan: see Cursor plan "Batch processor package refactor" (or `docs/refactor/` planning artifacts).

## Branch and safety

- **Refactor branch:** `refactor/batch-processor`
- **Stable reference:** `master` (or `main`) — keep unchanged until refactor is merged
- **Public API (unchanged):** `BatchProcessor`, `process_batch`, `SlotProcessingContext`; import path remains `from tools.batch_processor import ...` via a facade file

## Test command (run from repo root)

From project root `d:\LP`:

```bash
pytest tests/ -v
```

Optional (narrower):

```bash
pytest tests/ -v -k "batch or originals or partial or combined or slot or hyperlink or teacher_name or tracking or integration or concurrency or modelprivateattr or metadata"
```

Establish a baseline on `refactor/batch-processor` before each phase and run the same command after each phase to confirm no regressions.

### Baseline (pre-refactor)

- Full suite: 521 tests collected, 28 collection errors (unrelated: `Database` import, `TestClient`, connection refused). Run batch-processor-focused tests for refactor validation.
- Focused command: `pytest tests/test_originals_export.py tests/test_partial_generation.py tests/test_db_parsing_cache.py tests/test_teacher_name_builder.py tests/test_hyperlink_simple.py tests/test_imports.py tests/test_modelprivateattr_fix.py tests/test_combined_original_export.py -v --tb=short`
- Known pre-existing failures (out of refactor scope): `test_combined_original_export` (MagicMock JSON), `test_convert_pydantic_lesson_json_to_dict` (_hyperlinks), `test_process_slot_with_modelprivateattr_fix` (patches nonexistent `_extract_content`). Do not introduce new failures; these may be fixed separately.

## Phases (summary)

| Phase | Description |
|-------|-------------|
| 0 | Prepare: this doc, test baseline |
| 1 | Package shell; move `SlotProcessingContext` and pure helpers to `context.py` / `helpers.py` |
| 2 | Extract subdomains one by one: hyperlink_scrubber, slot_schema, extraction, transform, persistence, combine, signatures, combined_original |
| 3 | Thin orchestrator in package; `tools/batch_processor.py` becomes facade re-export only |
| 4 | Optional: reduce coupling (interfaces, mypy) |

## Package layout (target)

Implementation lives in `tools/batch_processor_pkg/` so that `tools/batch_processor.py` remains the importable facade.

- `tools/batch_processor_pkg/` — package directory
- `tools/batch_processor_pkg/__init__.py` — re-exports (e.g. SlotProcessingContext)
- `tools/batch_processor_pkg/context.py` — SlotProcessingContext (done)
- `tools/batch_processor_pkg/helpers.py` — pure helpers (done)
- `tools/batch_processor_pkg/hyperlink_scrubber.py` — scrub/restore hyperlinks
- `tools/batch_processor_pkg/slot_schema.py` — slot/schema mapping
- `tools/batch_processor_pkg/extraction.py` — slot content extraction
- `tools/batch_processor_pkg/transform.py` — LLM transform
- `tools/batch_processor_pkg/persistence.py` — persist original lesson plan
- `tools/batch_processor_pkg/combine.py` — combine/merge lessons and DOCX
- `tools/batch_processor_pkg/signatures.py` — signature/DOCX output
- `tools/batch_processor_pkg/combined_original.py` — combined original DOCX
- `tools/batch_processor_pkg/orchestrator.py` — BatchProcessor class and process_batch (thin coordinator; delegates to week_flow and slot_flow)
- `tools/batch_processor_pkg/week_flow.py` — week-level flow: load user/slots, enrich, parallel or sequential process, combine (Session 13)
- `tools/batch_processor_pkg/slot_flow.py` — single-slot flow: resolve file, extract, transform, persist (Session 13)
- `tools/batch_processor.py` — facade (imports from batch_processor_pkg, re-exports; also re-exports get_db, get_file_manager, get_tracker for test patching)

## Performance

The refactor was **structural only**: same logic, same I/O, same LLM and asyncio flow, moved into separate modules. No algorithmic changes, caching, or concurrency changes were made.

- **Runtime:** No before/after benchmarks were run. The code should be **effectively the same speed** (one extra import level via the facade is negligible).
- **Import time:** Loading several modules instead of one large file can be marginally different; not measured.
- **Analytics data in the database:** The app’s analytics module reads from the same DB: table `performance_metrics` (per-operation timing, tokens, cost, `operation_type`, `plan_id`) and `weekly_plans` (e.g. `processing_time_ms`, `total_cost_usd`, `generated_at`). The backend exposes this via `PerformanceTracker` (e.g. `get_aggregate_stats`, `get_daily_breakdown`, `get_operation_stats`) and the `/api/analytics/*` routes. That data can be used to compare batch runs before vs after refactors (e.g. filter by date or plan_id and compare duration/cost for similar workloads).
- To claim or compare performance in the future, run a fixed workload (e.g. `process_batch` for a given user/week) and either compare wall-clock or query the same analytics data (e.g. aggregate by `operation_type` or by plan) for similar runs before and after.

# Refactor: backend/performance_tracker.py

## Current state

- **File:** `backend/performance_tracker.py` (438 non-empty lines, same metric as count_loc physical)
- **Branch:** `refactor/slim-backend-performance-tracker` (create from `master`)

## Public API to preserve

- **Class `PerformanceTracker`** (public methods): cleanup_old_metrics, start_operation, end_operation, track_operation, get_plan_metrics, get_plan_summary, update_plan_summary, export_to_csv, get_aggregate_stats, get_daily_breakdown, get_session_breakdown, get_operation_stats, get_error_stats, get_parallel_processing_stats, export_analytics_csv

## Suggested extractions

1. (Identify logical units: e.g. "X + Y helpers" -> new module `.../x_y.py`; keep facade in original.)
2. ...
3. ...

## Steps (one commit per extraction)

1. Create branch from master: `git checkout master && git pull && git checkout -b refactor/slim-backend-performance-tracker`
2. Extract first unit into new module; update imports; run tests; commit.
3. Repeat for each extraction.
4. Update REFACTORING_PRIORITIES_AND_TOOLS.md (0.1, 1.4, 0.5 LOC) and merge to master.

## Test command

```bash
pytest tests/test_api.py tests/test_database_crud.py -q
```

**CI parity** (SQLite GitHub Actions; pytest marker `unit` — see [CONTRIBUTING](../../CONTRIBUTING.md)):

```bash
python -m pytest tests/ -m unit -q
```

## References

- [GIT_DURING_REFACTORING.md](GIT_DURING_REFACTORING.md)
- [REFACTORING_TOOLS_FOR_CURSOR.md](REFACTORING_TOOLS_FOR_CURSOR.md)

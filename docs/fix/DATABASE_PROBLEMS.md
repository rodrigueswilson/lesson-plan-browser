# Database Module Problems (fix/database-test-imports)

Summary of issues in `backend.database` that cause test collection errors and broken scripts.

---

## 1. Missing `Database` export (primary cause of 24 collection errors)

**What happens:** Tests and tools do `from backend.database import Database` and get:

```text
ImportError: cannot import name 'Database' from 'backend.database'. Did you mean: 'database'?
```

**Cause:** The module only defines and exports **`SQLiteDatabase`** (the concrete class). There is no name `Database`. Many call sites still use the old name `Database`.

**Evidence in code:**

- `backend/database.py` defines:
  - `class SQLiteDatabase(DatabaseInterface):` (line 27)
  - `def get_db(...)` (line 1742)
- No `Database` class or alias exists.

**Affected files (import `Database`):**

**Tests (14):**

- `tests/test_actual_processing.py`
- `tests/test_analytics_endpoints.py`
- `tests/test_analytics_integration.py`
- `tests/test_database_crud.py`
- `tests/test_database_migration.py`
- `tests/test_integration_tracking.py`
- `tests/test_integration_tracking_simple.py`
- `tests/test_performance_tracker.py`
- `tests/test_process_crash.py`
- `tests/test_tracking_demo.py`
- `tests/test_tracking_simple_demo.py`
- `tests/test_user_profiles.py`
- `tests/test_db_slots_direct.py` (inside a function)

**Backend:**

- `backend/migrations/add_structured_names.py`

**Tools (many under `tools/`):**

- `tools/maintenance/verify_daniela_config.py`
- `tools/maintenance/fix_daniela_file_patterns.py`
- `tools/maintenance/fix_daniela_teachers.py`
- `tools/maintenance/clear_daniela_slot_files.py`
- `tools/maintenance/fix_daniela_parent_folder.py`
- `tools/maintenance/fix_daniela_slots_paths.py`
- `tools/maintenance/fix_daniela_path.py`
- `tools/maintenance/verify_migration.py`
- `tools/maintenance/cleanup_users.py`
- `tools/maintenance/fix_missing_user.py`
- `tools/diagnostics/check_wilson_slots.py`
- `tools/diagnostics/check_daniela_slots.py`
- `tools/diagnostics/check_class_slots_schema.py`
- `tools/diagnostics/check_tables.py`
- `tools/diagnostics/check_weekly_plan.py`
- `tools/diagnostics/check_schema.py`
- `tools/diagnostics/check_recent_plan.py`
- `tools/diagnostics/check_users.py`
- `tools/diagnostics/diagnose_crash.py`
- `tools/utilities/query_metrics.py`

**Fix (recommended):** In `backend/database.py`, after the `SQLiteDatabase` class definition, add a public alias:

```python
# Backward compatibility: many tests and tools still import Database
Database = SQLiteDatabase
```

Then ensure `Database` is part of the module’s public API (e.g. in `__all__` if the module uses one). That resolves all import errors in one place.

---

## 2. Constructor signature mismatch (runtime failures after fixing imports)

**What happens:** Call sites use:

- `Database()` (no args)
- `Database(":memory:")` (in-memory SQLite)
- `Database(str(db_path))` or `Database(db_path=path)` (path to file)

**Current `SQLiteDatabase` signature:**

```python
def __init__(self, use_ipc: bool = False):
```

It does **not** accept a path or `:memory:`. It always uses `settings.SQLITE_DB_PATH`. So after adding the `Database` alias, any test or script that passes a path or `:memory:` will fail at runtime (e.g. `TypeError: SQLiteDatabase() got an unexpected keyword argument 'db_path'` or unexpected positional argument).

**Examples:**

- `tests/test_analytics_endpoints.py`: `db = Database(":memory:")`
- `tests/test_database_migration.py`: `db = Database(str(db_path))` (temp DB)
- `tests/test_user_profiles.py`: `db = Database(db_path)`
- `backend/migrations/add_structured_names.py`: `Database(db_path=args.db_path)` or `Database()`

**Fix options:**

1. **Extend `SQLiteDatabase.__init__`** to accept an optional path (and optionally `:memory:`), e.g.:
   - `def __init__(self, db_path: Optional[Union[str, Path]] = None, use_ipc: bool = False)`
   - If `db_path` is provided, use it (or `:memory:`); otherwise use `settings.SQLITE_DB_PATH`.
2. **Leave constructor as-is** and update tests/scripts to use `get_db()` or to override `settings.SQLITE_DB_PATH` for tests (e.g. in fixtures). Then only add the `Database` alias; tests that need a specific path would be refactored to use a test DB via settings or dependency injection.

Recommendation: Option 1 is the smallest change that restores existing test and migration behavior without touching many files.

---

## 3. Optional: `init_db` in documentation

**What happens:** `docs/CONTRIBUTING.md` says:

```text
python -c "from backend.database import init_db; init_db()"
```

**Cause:** `backend.database` does not define or export `init_db`. The interface in `backend.database_interface` declares `init_db(self)` as an instance method on `DatabaseInterface`; `SQLiteDatabase` implements it. So the documented one-liner is wrong.

**Fix:** Update the doc to use the real API (e.g. create a `SQLiteDatabase()` and call `db.init_db()`, or document the correct way to initialize the app DB).

---

## Summary

| Problem | Impact | Fix |
|--------|--------|-----|
| No `Database` export | 24 test collection errors + broken tools/migration | Add `Database = SQLiteDatabase` in `backend/database.py` |
| `SQLiteDatabase(db_path=...)` / `Database(":memory:")` not supported | Runtime errors in tests and migration after import fix | Extend `SQLiteDatabase.__init__` to accept optional `db_path` (and `:memory:`) |
| Doc references `init_db` as top-level | Misleading one-liner in CONTRIBUTING | Update CONTRIBUTING to use actual API |

Implementing the alias (1) and the constructor extension (2) on branch `fix/database-test-imports` will fix the database-related test and migration issues safely.

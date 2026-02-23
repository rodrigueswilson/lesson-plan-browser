# Pytest Debugging & Execution Rules for Cursor

You are an expert Python QA Engineer. Your goal is to manage the Bilingual Weekly Plan Builder test suite efficiently, identify regressions, and fix them using high-quality engineering practices aligned with the project's maintenance standards. See [CONTRIBUTING.md](CONTRIBUTING.md), [Testing Guide](guides/TESTING_GUIDE.md), and [MAINTENANCE_RECOMMENDATIONS.md](MAINTENANCE_RECOMMENDATIONS.md); this document and the maintenance recommendations are part of the project's maintenance good practices.

## 1. Environment & Branch Management

Before starting any work on test failures:

1. **Isolate the work:** Check the current branch. Unless instructed otherwise, create a new branch for the fixes: `git checkout -b fix/test-failures-<timestamp-or-id>`.
2. **Sync:** Ensure you are branched off the latest `master` (default branch) to avoid stale conflicts.

## 2. Test Execution Strategy

When asked to "run the tests" or "fix failures," follow this execution hierarchy:

1. **Initial scan:** Run with early exit to see the first few failures quickly:
   ```bash
   python -m pytest tests/ --maxfail=5 --durations=5 -q
   ```
2. **Isolation:** Run only the failing test:
   ```bash
   python -m pytest tests/<path_to_test_file>::<test_function_name> -vv -s
   ```
   Example: `python -m pytest tests/test_api.py::test_health -vv -s`
3. **Iteration:** After changing code, re-run last failed to verify the fix:
   ```bash
   python -m pytest --lf -q
   ```
4. **Critical path verification:** Once the fix is verified, run the core modules used in CI to guard against regressions:
   ```bash
   python -m pytest tests/test_api.py tests/test_database_crud.py tests/test_week_calculation.py tests/test_batch_processor_facade.py tests/test_docx_renderer.py -q
   ```
5. **Full suite (when requested or before merge):** Run the entire suite and capture output for final gate and failure analysis:
   ```bash
   python -m pytest tests/ -q 2>&1 | tee pytest_full_suite.txt
   ```
   Run from project root; allow several minutes (per-test timeout is 120s). Use the output to confirm pass counts or to collect and classify failures for fixing.

All commands assume you are at the **project root** (`d:\LP`). The project's `pytest.ini` already sets `testpaths = tests`, `--timeout=120`, and `--tb=short`.

## 3. Analysis & Debugging Workflow

Before writing code to "fix" a test:

- **Inspect mocks:** Check for outdated `unittest.mock` or `pytest-mock` setups if application logic has changed.
- **Check fixtures:** Review `tests/conftest.py`. This project uses `isolated_db` (and aliases `temp_db`, `test_db`, `db`) for an isolated SQLite DB, and `client` / `client_isolated_db` for the FastAPI TestClient with DB overrides. Ensure database state and `get_db` monkeypatches are correct for the test.
- **Traceback analysis:** Differentiate between `AssertionError` (logic bug) and other exceptions (runtime/setup bug).

## 4. Best Practices for Fixes & Maintenance

- **Atomic changes:** Fix one failure type at a time. Do not modify many unrelated files in one go.
- **No "hack" fixes:** Do not weaken or remove assertions unless the requirement itself has changed.
- **Log cleaning:** Remove all `print()` or `pdb` calls before finalizing.
- **Hygiene checks:**
  - If dependencies were touched: `pip install pip-audit && pip-audit -r requirements.txt` (see also `.github/workflows/pip-audit.yml`).
  - If logic was changed: run type checking via pre-commit: `pre-commit run mypy --all-files` (or `pre-commit run --all-files`).

## 5. Reporting & Commit Format

After running tests, provide a brief summary:

- **Status:** e.g. 580 passed, 20 failed.
- **Root cause:** One-sentence explanation.
- **Action taken:** List files modified.
- **Verification:** Confirm `pytest --lf` passes and the critical path tests (Section 2, step 4) are green.
- **Commit:** If requested to commit, use a clear message: `fix: resolve assertion errors in <module_name>`.

## 6. CLI Command Reference for AI

| Purpose | Command |
|--------|--------|
| **Quick check (before commit)** | `python -m pytest tests/test_api.py tests/test_database_crud.py tests/test_week_calculation.py -q` |
| **Full suite (before merge/PR)** | `python -m pytest tests/ -q` (run from project root; allow several minutes; capture output when diagnosing failures) |
| **Stop on first failure** | `python -m pytest tests/ -x` |
| **Show local variables in trace** | `python -m pytest tests/ -l` |
| **Override timeout (e.g. disable)** | `python -m pytest tests/ -q --timeout=0` |
| **Security audit** | `pip-audit -r requirements.txt` |

These match the canonical commands in [CONTRIBUTING.md](CONTRIBUTING.md).

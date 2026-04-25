# Maintenance Recommendations (Post-Refactor)

After the refactoring work, the codebase is in good shape. The following practices will help keep it healthy with minimal overhead. Prioritize what fits your capacity; items are ordered by impact vs effort.

**Related:** For a consistent, AI-friendly workflow when running or fixing tests, see [Cursor Pytest Automation Prompt](Cursor%20Pytest%20Automation%20Prompt.md). That document and this one are part of the project's maintenance good practices. For structured test-fix workflows: [Test Fix Agent Report](testing/TEST_FIX_AGENT_REPORT.md) (agent-only runbook) and [Test Fix Human Report](testing/TEST_FIX_HUMAN_REPORT.md) (collaborative decisions).

---

## 1. Align CI with your default branch

**Current:** `ci-integration-tests.yml` triggers on `main` and `develop`. Your repo default is `master` (per git status).

**Recommendation:** Add `master` to the workflow so pushes to `master` run the integration and authorization tests:

```yaml
on:
  push:
    branches: [ main, master, develop ]
  pull_request:
    branches: [ main, master, develop ]
```

This keeps every push to the branch you actually use protected by the same tests.

---

## 2. Fix pre-commit Bandit config

**Current:** `.pre-commit-config.yaml` runs Bandit with `-c pyproject.toml`, but the project has no root `pyproject.toml`, so Bandit may fail or use defaults.

**Recommendation (pick one):**

- **Option A:** Add a minimal `pyproject.toml` at project root with only Bandit (and optionally Black/isort) config, e.g.:

  ```toml
  [tool.bandit]
  exclude_dirs = ["tests", "scripts", ".venv"]
  skips = ["B101"]  # assert_used in tests, if you use assert
  ```

- **Option B:** Switch Bandit to a config file that exists, e.g. create `.bandit` or `bandit.yaml` and use `args: ['-c', '.bandit']` in pre-commit.

Then run `pre-commit run --all-files` to confirm all hooks pass.

---

## 3. One “test before commit” command

**Current:** Refactor workflow and TESTING_GUIDE mention several commands; CONTRIBUTING mentions `pytest tests/` and optional coverage. The canonical quick and full test commands are also defined in [Cursor Pytest Automation Prompt](Cursor%20Pytest%20Automation%20Prompt.md) for Cursor/AI sessions.

**Recommendation:** Define a single canonical “pre-commit test” and document it in CONTRIBUTING and (if you use it) in refactor plans:

- **Full (before merge / release):**  
  `python -m pytest tests/ -q`  
  (or with `--timeout=120` as in pytest.ini)

- **Quick / CI-parity (before each commit during refactor):**  
  `python -m pytest tests/ -m unit -q`  
  (matches the SQLite CI step; see `pytest.ini` marker `unit`.)  
  For a lighter local-only probe you may still run a single file, e.g. `python -m pytest tests/test_api.py -q`.

Document this in CONTRIBUTING under “Running tests” and, if applicable, in the refactor session prompt or REFACTORING_TOOLS_FOR_CURSOR as the standard “test command” to run before each commit. That keeps behavior consistent across contributors and Cursor sessions.

---

## 4. Dependency hygiene

**Status:** Implemented. Vulns in fastapi, python-multipart, and starlette were fixed by upgrading (fastapi 0.117, python-multipart 0.0.22, starlette 0.47.2). One CVE (CVE-2025-62727, starlette 0.49.1) is temporarily ignored in pip-audit CI until FastAPI supports starlette>=0.49. Dependabot and pip-audit CI are in place; see CONTRIBUTING. **Earlier:** `requirements.txt` mixed pinned versions (e.g. `fastapi==0.104.1`) and loose ones (e.g. `pydantic>=2.9.0`, `openai>=1.12.0`). This can lead to “works on my machine” or surprise breakages after `pip install -r requirements.txt`.

**Recommendation:**

- Pin all production dependencies to exact versions (e.g. `pydantic==2.9.x` after choosing a minor). Regenerate when you intentionally upgrade.
- Use **both** pip-audit and Dependabot for vulnerability checks; they are complementary:

  | Tool | What it does | When it runs |
  |------|--------------|--------------|
  | **pip-audit** | Scans declared/installed Python packages against CVE databases (PyPI advisory, OSV). Reports vulnerable versions; does not update. | On demand, in CI, or pre-commit. |
  | **Dependabot** | Opens PRs to bump dependencies (security and/or version). You review and merge. Supports Python, npm, etc. | On a schedule and on dependency changes (GitHub). |

  **Use both:** Dependabot creates PRs so you get updates without manually checking. pip-audit in CI fails the build when known vulnerabilities are present, so merged code stays clean. If a CVE appears after a merge, the next run (or Dependabot alert) catches it.

  - **pip-audit:** `pip install pip-audit && pip-audit -r requirements.txt`. Add a CI job that runs this and fails on any known vulnerability.
  - **Dependabot:** Add `.github/dependabot.yml`; enable Dependabot alerts in the repo. Use `open-pull-requests-limit: 5` and security-only or version updates as you prefer.

---

## 5. Run a broader test set in CI

**Status:** Implemented. After `verify_strategy_pack_ssot.py`, the **SQLite** job runs `tests/test_integration_authorization.py`, then **`pytest tests/ -m unit`** (step *Run unit-marked critical path tests*). Critical-path modules declare `pytestmark = pytest.mark.unit` so the command line stays short. The **Postgres** job runs `test_integration_authorization` and `test_authorization` only (see workflow comments for asymmetry).

**Earlier:** CI used an explicit list of test files instead of markers. **Recommendation (if you want even broader):**

- All of `tests/` with a timeout (e.g. `pytest tests/ -q --timeout=120`), or  
- Add stable modules to the `unit` marker and keep using `pytest tests/ -m unit`.

That way refactors and new work are validated automatically, not only integration/authorization.

---

## 6. Keep refactor docs and LOC up to date

**Status:** Implemented. Section **0.4** in REFACTORING_PRIORITIES_AND_TOOLS.md now instructs: after bigger changes, run `python tools/refactor/count_loc.py --markdown` and refresh the "Top N by LOC" table in 0.5. Section **0.5** has a refreshed top-25 table (2026-02-23). **Earlier:** 0.5 and 1.4 existed; the refactor session prompt already told the agent to update them.

**Ongoing:** When you do a sizable feature or refactor, periodically:

- Run `python tools/refactor/count_loc.py --markdown` (or `--json`) and refresh section 0.5 if you care about LOC tracking.
- Add a short bullet to section 1.4 for any notable structural change.

That keeps the doc useful for the next Cursor refactor session and for humans.

---

## 7. Pre-commit in CONTRIBUTING

**Status:** Implemented. CONTRIBUTING has a **Pre-commit hooks** subsection under Code Style with install and run commands. See CONTRIBUTING (Pre-commit hooks).

**Reference (now in CONTRIBUTING):** In CONTRIBUTING, under “Code style” or “Development workflow”, add:

- Install: `pre-commit install`; run manually: `pre-commit run --all-files`. See CONTRIBUTING (Pre-commit hooks).

---

## 8. Lightweight changelog

**Status:** Implemented. `docs/CHANGELOG.md` exists (Keep a Changelog style). A Maintenance - 2026-02 entry was added. **Ongoing:** On release or major refactor, append bullets and date.

**Recommendation:** Add a minimal `CHANGELOG.md` (or `docs/CHANGELOG.md`) with sections like “Added”, “Changed”, “Fixed”, “Refactored”. When you cut a release or merge a big refactor, append a few bullets and a date. This helps with support and with remembering what changed when.

---

## 9. Archive completed refactor plans (optional)

**Current:** `docs/refactor/plans/` holds many plans; some refer to files already under 400 LOC.

**Recommendation:** Move plans for “done” files into an `docs/refactor/plans/archive/` (or add a “Completed” note at the top of each). That makes it clear which plans are still active and keeps the main list scannable. Optional; only if you find the folder noisy.

---

## 10. Type checking and mypy

**Current:** mypy runs in pre-commit with `--ignore-missing-imports --no-strict-optional`.

**Recommendation:** Keep as-is for now. If you want to tighten later, consider enabling stricter mypy for a subset of modules (e.g. `backend/`, `tools/`) and documenting any per-module exclusions. No change required for good maintenance; this is a “next level” step.

---

## Summary table

| Priority | Action | Effort |
|----------|--------|--------|
| High     | Add `master` to CI branches (1) | Low |
| High     | Fix Bandit config (2) | Low |
| High     | Document one “test before commit” command (3) | Low |
| Medium   | Pin all dependencies + optional pip-audit (4) | Medium |
| Medium   | Widen CI test set (5) | Low–Medium |
| Medium   | Document pre-commit in CONTRIBUTING (7) | Low |
| Low      | Refresh LOC / refactor doc after big changes (6) | Low |
| Low      | Add CHANGELOG and maintain lightly (8) | Low |
| Optional | Archive completed refactor plans (9); stricter mypy (10) | Low |

These practices build on the refactoring discipline you already have (plans, 400-LOC rule, test-before-commit, single source of truth) and keep the codebase maintainable without adding unnecessary process. For a repeatable test execution and debugging workflow (especially when using Cursor), use [Cursor Pytest Automation Prompt](Cursor%20Pytest%20Automation%20Prompt.md) together with this document.

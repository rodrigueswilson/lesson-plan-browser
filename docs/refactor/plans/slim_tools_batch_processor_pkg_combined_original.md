# Refactor: tools/batch_processor_pkg/combined_original.py

## Current state

- **File:** `tools/batch_processor_pkg/combined_original.py` (660 non-empty lines)
- **Branch:** `refactor/slim-batch-processor-pkg-combined-original` (create from `master`)

## Public API to preserve

- List any module-level exports, class names, or function signatures that callers depend on.
- Do not change these; only move implementation into new modules.

## Suggested extractions

1. ~~Combined DOCX render logic~~ **Done:** -> `combined_original_render.render_combined_originals_sync` (deduplication, per-plan render, merge, style normalization).
2. (Optional) Further extractions from `process_file_group` (e.g. cache/db helpers) in a future pass.

## Steps (one commit per extraction)

1. Create branch from master: `git checkout master && git pull && git checkout -b refactor/slim-batch-processor-pkg-combined-original`
2. Extract first unit into new module; update imports; run tests; commit.
3. Repeat for each extraction.
4. Update REFACTORING_PRIORITIES_AND_TOOLS.md (0.1, 1.4, 0.5 LOC) and merge to master.

## Test command

```bash
# Adjust to the area this file affects, e.g.:
pytest tests/ -q -k "docx or renderer"
# or
pytest tests/test_api.py tests/test_database_crud.py -q
```

**CI parity** (SQLite GitHub Actions; pytest marker `unit` — see [CONTRIBUTING](../../CONTRIBUTING.md)):

```bash
python -m pytest tests/ -m unit -q
```

## References

- [GIT_DURING_REFACTORING.md](GIT_DURING_REFACTORING.md)
- [REFACTORING_TOOLS_FOR_CURSOR.md](REFACTORING_TOOLS_FOR_CURSOR.md)

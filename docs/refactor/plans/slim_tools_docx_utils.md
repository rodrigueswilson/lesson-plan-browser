# Refactor: tools/docx_utils.py

## Current state

- **File:** `tools/docx_utils.py` (636 non-empty lines)
- **Branch:** `refactor/slim-tools-docx-utils` (create from `master`)

## Public API to preserve

- List any module-level exports, class names, or function signatures that callers depend on.
- Do not change these; only move implementation into new modules.

## Suggested extractions

1. ~~Table helpers~~ **Done:** -> `tools/docx_table_utils.py` (normalize_table_column_widths, normalize_all_tables, get_table_info); re-exported from docx_utils.
2. (Optional) Style normalization group (normalize_styles_via_file, normalize_styles_from_master, _normalize_styles_via_api, diagnose_style_conflicts) in a future pass.

## Steps (one commit per extraction)

1. Create branch from master: `git checkout master && git pull && git checkout -b refactor/slim-tools-docx-utils`
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

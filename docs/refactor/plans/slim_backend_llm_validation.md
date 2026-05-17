# Refactor: backend/llm/validation.py

## Current state

- **File:** `backend/llm/validation.py` (673 non-empty lines)
- **Branch:** `refactor/slim-llm-validation` (create from `master`)

## Public API to preserve

- List any module-level exports, class names, or function signatures that callers depend on.
- Do not change these; only move implementation into new modules.

## Suggested extractions

1. ~~Validation error parser~~ **Done:** -> `backend/llm/validation_error_parser.py` (`parse_validation_errors`); re-exported from validation.py.
2. (Optional) pre_validate_json or validate_structure in a future pass.
3. ...

## Steps (one commit per extraction)

1. Create branch from master: `git checkout master && git pull && git checkout -b refactor/slim-llm-validation`
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

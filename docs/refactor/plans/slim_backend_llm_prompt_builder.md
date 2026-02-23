# Refactor: backend/llm/prompt_builder.py

## Current state

- **File:** `backend/llm/prompt_builder.py` (673 non-empty lines)
- **Branch:** `refactor/slim-llm-prompt-builder` (create from `master`)

## Public API to preserve

- List any module-level exports, class names, or function signatures that callers depend on.
- Do not change these; only move implementation into new modules.

## Suggested extractions

1. ~~Schema example building~~ **Done:** -> `backend/llm/schema_example.build_schema_example` (facade in prompt_builder).
2. (Identify next logical units: e.g. days/instruction helpers, retry prompt building.)
3. ...

## Steps (one commit per extraction)

1. Create branch from master: `git checkout master && git pull && git checkout -b refactor/slim-llm-prompt-builder`
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

## References

- [GIT_DURING_REFACTORING.md](GIT_DURING_REFACTORING.md)
- [REFACTORING_TOOLS_FOR_CURSOR.md](REFACTORING_TOOLS_FOR_CURSOR.md)

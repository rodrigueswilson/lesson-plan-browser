# Refactor: tools/validate_threshold_change_v2.py

## Current state

- **File:** `tools/validate_threshold_change_v2.py` (415 non-empty lines, same metric as count_loc physical)
- **Branch:** `refactor/slim-tools-validate-threshold-change-v2` (create from `master`)

## Public API to preserve

- **Package `__all__`** (from sibling `__init__.py`): repair_json, validate_and_repair, generate_with_retry, generate_with_retry_simple, RetryExhausted
- **Class `ImprovedThresholdValidator`** (public methods): validate_file_pair, print_summary

## Suggested extractions

1. **Class `ImprovedThresholdValidator`** has 4 private methods; group by responsibility (fill, format, placement, media) and extract to sibling modules.

## Steps (one commit per extraction)

1. Create branch from master: `git checkout master && git pull && git checkout -b refactor/slim-tools-validate-threshold-change-v2`
2. Extract first unit into new module; update imports; run tests; commit.
3. Repeat for each extraction.
4. Update REFACTORING_PRIORITIES_AND_TOOLS.md (0.1, 1.4, 0.5 LOC) and merge to master.

## Test command

```bash
pytest tests/ -q
```

**CI parity** (SQLite GitHub Actions; pytest marker `unit` — see [CONTRIBUTING](../../CONTRIBUTING.md)):

```bash
python -m pytest tests/ -m unit -q
```

## References

- [GIT_DURING_REFACTORING.md](GIT_DURING_REFACTORING.md)
- [REFACTORING_TOOLS_FOR_CURSOR.md](REFACTORING_TOOLS_FOR_CURSOR.md)

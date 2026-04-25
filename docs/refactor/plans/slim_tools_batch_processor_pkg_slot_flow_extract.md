# Refactor: tools/batch_processor_pkg/slot_flow_extract.py

## Current state

- **File:** `tools/batch_processor_pkg/slot_flow_extract.py` (421 non-empty lines, same metric as count_loc physical)
- **Branch:** `refactor/slim-batch-processor-pkg-slot-flow-extract` (create from `master`)

## Public API to preserve

- **Package `__all__`** (from sibling `__init__.py`): SlotProcessingContext

## Suggested extractions

1. (Identify logical units: e.g. "X + Y helpers" -> new module `.../x_y.py`; keep facade in original.)
2. ...
3. ...

## Steps (one commit per extraction)

1. Create branch from master: `git checkout master && git pull && git checkout -b refactor/slim-batch-processor-pkg-slot-flow-extract`
2. Extract first unit into new module; update imports; run tests; commit.
3. Repeat for each extraction.
4. Update REFACTORING_PRIORITIES_AND_TOOLS.md (0.1, 1.4, 0.5 LOC) and merge to master.

## Test command

```bash
pytest tests/ -q -k "batch or combine or slot or week"
```

**CI parity** (SQLite GitHub Actions; pytest marker `unit` — see [CONTRIBUTING](../../CONTRIBUTING.md)):

```bash
python -m pytest tests/ -m unit -q
```

## References

- [GIT_DURING_REFACTORING.md](GIT_DURING_REFACTORING.md)
- [REFACTORING_TOOLS_FOR_CURSOR.md](REFACTORING_TOOLS_FOR_CURSOR.md)

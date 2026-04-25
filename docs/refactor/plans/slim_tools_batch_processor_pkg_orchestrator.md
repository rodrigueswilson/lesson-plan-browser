# Refactor: tools/batch_processor_pkg/orchestrator.py

## Current state

- **File:** `tools/batch_processor_pkg/orchestrator.py` (421 non-empty lines, same metric as count_loc physical)
- **Branch:** `refactor/slim-batch-processor-pkg-orchestrator` (create from `master`)

## Public API to preserve

- **Package `__all__`** (from sibling `__init__.py`): SlotProcessingContext

## Suggested extractions

1. **`add_*`** helpers (3 methods): `_add_signature_box`, `_add_signature_image_to_table`, `_add_user_name_to_table` -> consider new module `.../add_*.py` or keep in facade and delegate.
2. **`sanitize_*`** helpers (2 methods): `_sanitize_slot`, `_sanitize_value` -> consider new module `.../sanitize_*.py` or keep in facade and delegate.
3. **`convert_*`** helpers (2 methods): `_convert_originals_to_json`, `_convert_single_slot_to_slots_format` -> consider new module `.../convert_*.py` or keep in facade and delegate.

## Steps (one commit per extraction)

1. Create branch from master: `git checkout master && git pull && git checkout -b refactor/slim-batch-processor-pkg-orchestrator`
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

# Refactor: tools/batch_processor_pkg/combine_render.py

## Current state

- **File:** `tools/batch_processor_pkg/combine_render.py` (784 non-empty lines, same metric as count_loc physical)
- **Branch:** `refactor/slim-batch-processor-pkg-combine-render` (create from `master`)

## Public API to preserve

- **Package `__all__`** (from sibling `__init__.py`): SlotProcessingContext

## Suggested extractions

1. ~~(Identify logical units)~~ **Done:** Signature path resolution -> `render_helpers.resolve_signature_image_path`.
2. ~~Lesson JSON normalization~~ **Done:** -> `render_helpers.normalize_lesson_json_for_render`.
3. (Optional) Objectives/sentence-frames block could be extracted in a future pass.

## Steps (one commit per extraction)

1. Create branch from master: `git checkout master && git pull && git checkout -b refactor/slim-batch-processor-pkg-combine-render`
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

# Refactor: tools/docx_renderer/renderer.py

## Current state

- **File:** `tools/docx_renderer/renderer.py` (~230 lines)
- **Branch:** `refactor/slim-docx-renderer-renderer` (create from `master`)

## Public API to preserve

- **Package `__all__`** (from sibling `__init__.py`): DOCXRenderer, FUZZY_MATCH_THRESHOLD, logger
- **Class `DOCXRenderer`** (public methods): render

## Done

1. **`get_*`** – Removed `_get_row_index` / `_get_col_index`; call sites use `get_indices` module.
2. **Fallback media** – Extracted to `fallback_media.py`; renderer keeps thin wrappers for `combine_render` and tests.
3. **Structure init** – Extracted to `template_structure.py`; `initialize_structure(renderer)`.
4. **Render pipeline** – Extracted to `render_pipeline.py`; `run_render_pipeline(...)`; agent debug log blocks removed.

## Optional next steps

- **CLI** – Done: `main()` lives in `__main__.py`; renderer holds only the class and delegates.
- **Thin wrappers** – Keep `_fill_cell`, `_fill_day`, `_append_unmatched_media`, etc.; tests and `combine_render` call them.
- **Docs** – REFACTORING_PRIORITIES_AND_TOOLS.md section 0.5 and 1.4 updated; run `python tools/refactor/count_loc.py --markdown` when merging.

## Steps (one commit per extraction)

1. Create branch from master: `git checkout master && git pull && git checkout -b refactor/slim-docx-renderer-renderer`
2. Extract first unit into new module; update imports; run tests; commit.
3. Repeat for each extraction.
4. Update REFACTORING_PRIORITIES_AND_TOOLS.md (0.1, 1.4, 0.5 LOC) and merge to master.

## Test command

```bash
pytest tests/ -q -k "docx or renderer"
```

**CI parity** (SQLite GitHub Actions; pytest marker `unit` — see [CONTRIBUTING](../../CONTRIBUTING.md)):

```bash
python -m pytest tests/ -m unit -q
```

## References

- [GIT_DURING_REFACTORING.md](GIT_DURING_REFACTORING.md)
- [REFACTORING_TOOLS_FOR_CURSOR.md](REFACTORING_TOOLS_FOR_CURSOR.md)

# Refactor: backend/services/objectives_pdf_generator.py

## Current state

- **File:** `backend/services/objectives_pdf_generator.py` (719 non-empty lines, same metric as count_loc physical)
- **Branch:** `refactor/slim-services-objectives-pdf-generator` (create from `master`)

## Public API to preserve

- **Class `ObjectivesPDFGenerator`** (public methods): extract_objectives, generate_html, convert_to_pdf, generate_pdf

## Suggested extractions

1. **`resolve_*`** helpers (3 methods): `_resolve_html_path`, `_resolve_output_directory`, `_resolve_pdf_and_html_paths` -> consider new module `.../resolve_*.py` or keep in facade and delegate.
2. **`get_*`** helpers (3 methods): `_get_css_template`, `_get_day_date`, `_get_html_template` -> consider new module `.../get_*.py` or keep in facade and delegate.
3. **`extract_*`** helpers (2 methods): `_extract_from_day`, `_extract_from_slot` -> consider new module `.../extract_*.py` or keep in facade and delegate.

## Steps (one commit per extraction)

1. Create branch from master: `git checkout master && git pull && git checkout -b refactor/slim-services-objectives-pdf-generator`
2. Extract first unit into new module; update imports; run tests; commit.
3. Repeat for each extraction.
4. Update REFACTORING_PRIORITIES_AND_TOOLS.md (0.1, 1.4, 0.5 LOC) and merge to master.

## Test command

```bash
pytest tests/test_api.py tests/test_database_crud.py -q
```

**CI parity** (SQLite GitHub Actions; pytest marker `unit` — see [CONTRIBUTING](../../CONTRIBUTING.md)):

```bash
python -m pytest tests/ -m unit -q
```

## References

- [GIT_DURING_REFACTORING.md](GIT_DURING_REFACTORING.md)
- [REFACTORING_TOOLS_FOR_CURSOR.md](REFACTORING_TOOLS_FOR_CURSOR.md)

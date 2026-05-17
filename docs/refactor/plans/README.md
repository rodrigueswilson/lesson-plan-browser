# Refactor plans

Plans for single-file refactors (slim/split) are written here by `tools/refactor/start_refactor.py`.

## Streamlined workflow (one file at a time)

1. **Start refactor for one file** (creates branch from master + writes plan):
   ```bash
   python tools/refactor/start_refactor.py tools/docx_renderer/renderer.py
   ```
2. Open the generated plan in `docs/refactor/plans/slim_<name>.md`. Implement extractions (e.g. with Cursor): create new modules, slim the original, preserve public API.
3. Run the test command from the plan after each extraction (focused smoke, then optionally the **CI parity** line: `python -m pytest tests/ -m unit -q`). If the plan has no test section, use [CONTRIBUTING](../../CONTRIBUTING.md); commit when tests pass.
4. Merge to master and push:
   ```bash
   git checkout master
   git merge refactor/slim-<name> -m "refactor: slim <file>"
   git push origin master
   ```
5. Repeat from step 1 for the next file (you will be on master).

## Batch: prepare plans for many files

To generate plans for all candidates without creating branches yet:

```bash
python tools/refactor/start_refactor.py --list docs/refactor/plans/slim_candidates.txt --batch --no-branch
```

To create branch + plan for the **first** file and plans only for the rest:

```bash
python tools/refactor/start_refactor.py --list docs/refactor/plans/slim_candidates.txt --batch
```

Then implement the first file (branch already created), merge, and start the next:

```bash
python tools/refactor/start_refactor.py backend/services/objectives_pdf_generator.py
```

## File list format

`slim_candidates.txt` contains one path per line (relative to project root). Lines starting with `#` are ignored. Use this list with `--list docs/refactor/plans/slim_candidates.txt`.

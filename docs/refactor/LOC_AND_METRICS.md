# LOC and Metrics for Refactor Tracking

This document describes how we count lines of code, how to run the LOC script, and how to use counts to identify future refactoring needs and refresh section 0.5 of [REFACTORING_PRIORITIES_AND_TOOLS.md](REFACTORING_PRIORITIES_AND_TOOLS.md).

---

## What the script counts

- **With cloc:** **SLOC** (source lines of code) — code only; blank lines and comments are excluded. Use when you want a stricter, code-only metric.
- **Without cloc (fallback):** **Physical lines (non-empty)** — every line that has at least one non-whitespace character. No comment stripping. Output is clearly labeled so you know which mode was used.

The same **include/exclude** list is used in both modes so totals are comparable. Include: `backend/`, `frontend/src/`, `tools/` (excluding `tools/archive/`). Exclude: `tools/archive/`, `node_modules/`, `__pycache__`, `.tauri`, build/output dirs, virtualenv, `*.min.js`, etc.

---

## Optional: installing cloc (for SLOC)

The script **never requires** cloc; it works with a built-in physical-line fallback. If you want SLOC instead of physical lines, install cloc:

- **Windows:** `winget install cloc` (or download from [cloc on GitHub](https://github.com/AlDanial/cloc))
- **macOS:** `brew install cloc`
- **Linux:** `apt install cloc` / `yum install cloc` (or equivalent)

After installation, run the script without `--no-cloc`; it will use cloc when available.

---

## How to run

From the **project root**:

```bash
# Human-readable summary (default)
python tools/refactor/count_loc.py

# JSON: by_directory, files (sorted by count)
python tools/refactor/count_loc.py --json

# Markdown table for pasting into section 0.5
python tools/refactor/count_loc.py --markdown

# Force fallback (do not use cloc)
python tools/refactor/count_loc.py --no-cloc

# Files over N lines (refactor targets; sorted by count descending)
python tools/refactor/count_loc.py --over 400
```

---

## Using LOC to identify refactoring needs

- **File-size thresholds:** Use counts to spot candidates for splitting. **Files over 400 lines** are refactor targets (see CURSOR_REFACTOR_SESSION_PROMPT; prefer turning them into packages). Files over ~500 lines are worth reviewing; over ~800 lines are strong candidates for extraction (align with priorities in REFACTORING_PRIORITIES_AND_TOOLS section 1).
- **Baseline / snapshot:** Run the script periodically (e.g. after a refactor or on a schedule) and keep a short baseline (e.g. append a one-line summary to a file or CI log) so you can see growth over time.
- **Section 0.5:** The script output is the single source for updating the line-count tables in REFACTORING_PRIORITIES_AND_TOOLS section 0.5.

---

## How to refresh section 0.5

1. From project root, run: `python tools/refactor/count_loc.py --markdown`
2. For a **subset** (e.g. one package), run with `--json`, filter the `files` list by path prefix, and format as a Markdown table.
3. Paste or update the table(s) in REFACTORING_PRIORITIES_AND_TOOLS.md section 0.5. Add a short heading (e.g. "**Package name (Session N):**") if needed.

---

## Optional follow-ups (out of scope for this doc)

- **Baseline file:** Script could append date + total to e.g. `docs/refactor/loc_baseline.txt`.
- **CI:** Job that runs the script and fails if a file or package exceeds a line limit.
- **Complexity (e.g. radon):** Document as a future option for cyclomatic complexity; no implementation here.

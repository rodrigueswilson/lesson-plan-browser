# Refactoring Tools for Cursor

This document is a checklist for refactoring **with Cursor (AI)** so that Python refactoring libraries (Rope, Bowler, LibCST, Refex) are used where they help. It reduces missed renames/imports and keeps mechanical changes repeatable. The full tool descriptions and workflow are in [REFACTORING_PRIORITIES_AND_TOOLS.md](REFACTORING_PRIORITIES_AND_TOOLS.md) **Section 2** (libraries) and **Section 3** (workflow); this doc prescribes when to use what and how to combine Cursor with tools.

---

## When to use what

| Task | Prefer | Notes |
|------|--------|--------|
| **Renames, extract method/variable, move module** | IDE (pylsp-rope) or Rope API | All references and imports updated; avoid manual search-replace for symbols. |
| **Mechanical pattern across many files** | Bowler script or LibCST codemod | Run on a refactor branch; **review diff** before applying; run tests after. |
| **Expression-level pattern replace** | Refex | When the pattern fits Refex’s template syntax. |
| **Large-file splits / API redesign** | Manual edits | Use IDE extract only for small local pieces; design and move code by hand. |

---

## Rope with Cursor / VS Code

- **pylsp-rope** is the recommended way to get Rope refactors in Cursor: LSP rename (variables, classes, functions) works in-editor. Cursor uses the same LSP as VS Code.
- **Install:** `pip install pylsp-rope` in the same virtualenv as `python-lsp-server`; the plugin is auto-discovered.
- **Note:** pylsp-rope is early-stage; rename may be disabled by default in some versions. If rename does not appear, check LSP/editor settings (e.g. enable rename refactoring).
- **Alternative:** A standalone Rope VS Code extension exists but is limited; pylsp-rope is the recommended path for LSP-based refactors (per Rope wiki).

---

## Bowler / LibCST

- **Always review diffs before applying.** Use Bowler’s `.diff(interactive=True)` or `.idiff()` so Cursor (or the human) reviews changes before they are written. Run Bowler/LibCST scripts on a refactor branch.
- **Reusable scripts:** Prefer small Bowler or LibCST scripts (fluent API or codemod) that can be run repeatedly and versioned under `tools/refactor/` rather than one-off AI-generated edits for the same pattern.
- **LibCST:** Use matchers and visitor patterns instead of raw `isinstance`; keeps transforms maintainable and resilient to CST changes.

---

## Cursor (AI) vs tools — when to use which

- **Use automated tools (Rope/Bowler/LibCST)** for: deterministic renames, import updates, and mechanical pattern changes across many files. They avoid missed call sites and preserve formatting/comments.
- **Use Cursor (AI)** for: design decisions, splitting large files, and context-aware extractions. Then **verify**: run tests, review diffs, and optionally run Rope/Bowler for any follow-up mechanical renames or pattern fixes so nothing is missed.
- **Safety:** After AI-driven refactors, run the test suite and consider using Rope/Bowler for any remaining symbol or pattern fixes. LLMs can suggest edits but often miss call sites, imports, and tests; tools close that gap.

---

## Cursor-specific workflow

- **Plan mode (e.g. Shift+Tab)** for complex refactors: get a plan and scope before editing.
- **Prefer IDE refactor actions** (rename, extract) when the Python LSP/pylsp-rope provides them, so Cursor’s edits and the IDE stay in sync. Fall back to “have Cursor suggest edits, then run a Bowler/Rope script” for bulk renames or patterns.
- **Python “Move to File” and some refactors** may be limited in the Python extension. Cursor’s Agent can do cross-file moves; for symbol renames and import updates, recommend Rope/pylsp-rope or a Bowler script for consistency.

---

## Streamlined one-file refactor workflow

To refactor many large files one at a time with minimal manual steps:

1. **Start a refactor** (from project root): creates branch from `master` and writes a plan under `docs/refactor/plans/`:
   ```bash
   python tools/refactor/start_refactor.py <file_path>
   ```
   Example: `python tools/refactor/start_refactor.py tools/docx_renderer/renderer.py`
   - For **Python** files, the plan is pre-filled with **Public API** (from package `__all__` and class public methods) and **Suggested extractions** (method groups by prefix, from AST). The **Test command** is chosen by path (e.g. docx_renderer -> `pytest tests/ -q -k "docx or renderer"`).
   - If the plan already exists, the script skips writing unless you pass `--force` (overwrite) or `--update-plan` (refresh LOC and analysis). Use `--no-branch` to only write or refresh the plan without creating a branch.

2. **Implement** using the generated plan (e.g. with Cursor): follow the suggested extractions, create new modules, slim the original, preserve public API. Run the **test command from the plan** after each extraction; if the plan does not specify one, use the **quick check** from [CONTRIBUTING](../CONTRIBUTING.md) (Test before commit). Before merging to master, run the **full suite** from CONTRIBUTING. Use the **refactoring-workflow** Cursor rule so the agent follows the plan and runs tests before each commit.

**One-shot session prompt:** To have Cursor run the entire process (script + plan + extractions + tests + commits) in one go, use the copy-paste prompt in [CURSOR_REFACTOR_SESSION_PROMPT.md](CURSOR_REFACTOR_SESSION_PROMPT.md). Paste it at the start of a session with the target file path; use Agent mode.

3. **Merge and push**: `git checkout master`, `git merge refactor/slim-<name>`, `git push origin master`.

4. **Repeat** for the next file (you are on `master`; run step 1 with the next path).

To **prepare plans for many files** without creating branches (e.g. for a list of candidates), use `--list` and optionally `--batch`:
```bash
python tools/refactor/start_refactor.py --list docs/refactor/plans/slim_candidates.txt --batch --no-branch
```
See [docs/refactor/plans/README.md](plans/README.md) for the file list format and batch options.

---

## References

- **Libraries and workflow:** [REFACTORING_PRIORITIES_AND_TOOLS.md](REFACTORING_PRIORITIES_AND_TOOLS.md) **Section 2** (Rope, Bowler, LibCST, Refex) and **Section 3** (suggested workflow).
- **Git during refactors:** [GIT_DURING_REFACTORING.md](GIT_DURING_REFACTORING.md).
- **One-file workflow and plans:** [docs/refactor/plans/README.md](plans/README.md).

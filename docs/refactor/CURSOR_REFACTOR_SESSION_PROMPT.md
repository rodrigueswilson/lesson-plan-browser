# Session-start prompt for full refactor (Cursor)

## For the AI / Cursor agent

**When the user references this file** (e.g. `@CURSOR_REFACTOR_SESSION_PROMPT.md` or "run the refactor prompt"), treat it as an instruction to **execute** the refactor process below, not to summarize this document.

- **Execute** the steps in "Prompt to execute" in order: run the start script, open and follow the plan, do one extraction at a time (test, then commit), then do the final wrap-up.
- **Target file:** Use the file specified by the user in their message. If they only reference this doc without naming a file, use the default: `tools/docx_renderer/renderer.py` (or infer from the current refactor branch name, e.g. `refactor/slim-docx-renderer-renderer` -> `tools/docx_renderer/renderer.py`).
- **Do not** only summarize what the prompt says; run the commands, read the plan, implement extractions, run tests, and commit as described.

---

## Prompt to execute

When executing, follow these steps in order. Replace `FILE` with the target file (e.g. `tools/docx_renderer/renderer.py`) if using the generic form.

1. **Ensure we're at project root.** Run: `python tools/refactor/start_refactor.py FILE`
   - If the plan already exists you'll see "Plan already exists"; that's fine. Use `--update-plan` to refresh LOC/analysis (recommended if the file was partially refactored earlier; the plan may list methods that no longer exist), or `--no-branch` if we're already on the refactor branch and only need the plan.
   - Note the branch name and plan path from the output.

2. **Open the plan** at `docs/refactor/plans/` (the plan path from step 1). Read "Public API to preserve" and "Suggested extractions".

3. **Implement the refactor** by following the plan:
   - Do **one** suggested extraction at a time: create the new module (or extend an existing one), move/copy the listed methods or helpers, update imports in the original file so it delegates to the new module, and preserve the exact public API listed in the plan.
   - After each extraction: run the **Test command** from the plan (the bash block in the plan). If tests fail, fix before committing. If some failures persist, run the same test command on `master` (e.g. `git stash` + `git checkout master` then run tests) to confirm they are pre-existing; if so, you may proceed with commits and note it.
   - Skip an extraction if it would only add indirection (e.g. methods already delegate to another module; plan often says "keep in facade and delegate").
   - Commit with a clear message, e.g. `refactor(docx_renderer): extract format_* helpers to content_format.py`.
   - Repeat for the next extraction until all suggested extractions are done (or the user asks to stop after N extractions for this session).

4. **When done with extractions:** Run the test command one more time, then remind the user to update REFACTORING_PRIORITIES_AND_TOOLS.md (sections 0.1, 1.4, 0.5) and to run `python tools/refactor/count_loc.py --markdown` for the changed area before merging to master.

Use the refactoring-workflow rule (`.cursor/rules/refactoring-workflow.mdc`) and docs in `docs/refactor/` (REFACTORING_TOOLS_FOR_CURSOR.md, GIT_DURING_REFACTORING.md) as needed. Prefer Agent mode so you can run commands and edit files.

---

## For the user: how to use this file

- **To run the full refactor:** Reference this file in chat (e.g. `@docs/refactor/CURSOR_REFACTOR_SESSION_PROMPT.md`). The agent will execute the prompt above. Optionally say which file to refactor, or "use the DOCX renderer" for `tools/docx_renderer/renderer.py`.
- **To paste a custom prompt:** Copy the "Prompt to execute" section, replace `FILE` with your target (e.g. `tools/docx_renderer/renderer.py`), and paste at the start of a session.
- **Agent mode:** Use Agent mode (not Ask) so the agent can run the script and commits.
- **One session, one file:** The process is for one file per session. For another file, start a new chat and reference this file with the new target.
- **Stopping early:** You can say e.g. "stop after 2 extractions this session" and the agent will stop after that many commits.

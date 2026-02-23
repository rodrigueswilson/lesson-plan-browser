# Session-start prompt for full refactor (Cursor)

## For the AI / Cursor agent

**When the user references this file** (e.g. `@CURSOR_REFACTOR_SESSION_PROMPT.md` or "run the refactor prompt"), treat it as an instruction to **execute** the refactor process below, not to summarize this document.

- **Execute** the steps in "Prompt to execute" in the following order: run the start script, open and follow the plan, perform one extraction at a time (test, then commit), then do the final wrap-up.
- **Refactoring method:** You are responsible for choosing the best refactoring approach for each file. Use the plan's "Suggested extractions" as guidance, but apply the strategy that fits the file best (e.g. extract modules, split classes, simplify conditionals, reduce duplication, or other techniques). Preserve the public API; otherwise decide what to extract and how.
- **Target files:** Use the file(s) specified in the user's message. If they only reference this doc without naming files, run `python tools/refactor/count_loc.py --biggest 3` from the project root and use the three printed paths as the refactor targets for this session (the three biggest files). Refactor all three in one session (see "Prompt to execute"). If the user names one or more files, use those. You may infer the target from the current refactor branch name (e.g. `refactor/slim-docx-renderer-renderer` -> `tools/docx_renderer/renderer.py`).
- **Do not** only summarize what the prompt says; run the commands, read the plan, implement extractions, run tests, and commit as described.

---

## Prompt to execute

When executing, work on one or more target files. If no files were specified, run `python tools/refactor/count_loc.py --biggest 3` and use the three printed paths. Then **for each target file in order** (biggest first, then second, then third), do the following. Before starting the **second** and **third** file, run `git checkout master` so each refactor gets its own branch.

**For each FILE in the target list:**

1. **Ensure we're at project root.** For the first file, run: `python tools/refactor/start_refactor.py FILE`. For the second and third files, first run `git checkout master`, then run the same start_refactor command for that FILE (so a new refactor branch is created for each file).
   - If the plan already exists you'll see "Plan already exists"; that's fine. Use `--update-plan` to refresh LOC/analysis, or `--no-branch` if we're already on that file's refactor branch and only need the plan.
   - Note the branch name and plan path from the output.
2. **Open the plan** at `docs/refactor/plans/` (the plan path from step 1). Read "Public API to preserve" and "Suggested extractions". If the plan has a "Done" section and no remaining "Suggested extractions" (only "Optional next steps"), the file is already refactored—report that, skip extractions for this file, and move to the next target.
3. **Implement the refactor** for this file. Choose the best refactoring method for this file (the plan is guidance; you may follow suggested extractions or use a different approach that fits better). Preserve the exact public API listed in the plan.
   - Do **one** logical change at a time: e.g. create a new module and delegate, split a class, extract helpers, or simplify logic. Update the original file and imports accordingly.
   - After each extraction: run the **Test command** from the plan. If tests fail, fix before committing. If some failures persist, run the same test command on `master` to confirm they are pre-existing; if so, you may proceed with commits and note it.
   - Skip an extraction if it would only add indirection (e.g. methods already delegate to another module).
   - Commit with a clear message, e.g. `refactor(docx_renderer): extract format_* helpers to content_format.py`.
   - Repeat until all suggested extractions for this file are done (or the user asks to stop after N extractions for this session).
4. **When done with this file:** Run the test command one more time for this file, then move to the next target (checkout master, then start_refactor for next FILE).

**After all target files are done:** Remind the user to update REFACTORING_PRIORITIES_AND_TOOLS.md (sections 0.1, 1.4, 0.5) and to run `python tools/refactor/count_loc.py --markdown` for the changed areas before merging each branch to master.

Use the refactoring-workflow rule (`.cursor/rules/refactoring-workflow.mdc`) and docs in `docs/refactor/` (REFACTORING_TOOLS_FOR_CURSOR.md, GIT_DURING_REFACTORING.md) as needed. Prefer Agent mode so you can run commands and edit files.

---

## For the user: how to use this file

- **To run the full refactor:** Reference this file in chat (e.g. `@docs/refactor/CURSOR_REFACTOR_SESSION_PROMPT.md`). The agent will execute the prompt above. Optionally say which file(s) to refactor; if you don't, the agent runs `python tools/refactor/count_loc.py --biggest 3` and refactors the three biggest files in one session (each on its own branch).
- **To paste a custom prompt:** Copy the "Prompt to execute" section, replace FILE/target list as needed, and paste at the start of a session.
- **Agent mode:** Use Agent mode (not Ask) so the agent can run the script and commits.
- **One session, three files:** By default the agent refactors the three biggest files in one session. Each file gets its own refactor branch; after finishing one file, the agent checks out master and starts the next. Merge branches to master one by one when ready.
- **Stopping early:** You can say e.g. "stop after 2 extractions this session" and the agent will stop after that many commits (for the current file).


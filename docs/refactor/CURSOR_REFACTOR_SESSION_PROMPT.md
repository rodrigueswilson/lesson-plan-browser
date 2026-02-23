# Session-start prompt for full refactor (Cursor)

## For the AI / Cursor agent

**When the user references this file** (e.g. `@CURSOR_REFACTOR_SESSION_PROMPT.md` or "run the refactor prompt"), treat it as an instruction to **execute** the refactor process below, not to summarize this document.

- **Execute** the steps in "Prompt to execute" in the following order: run the start script, open and follow the plan, perform one extraction at a time (test, then commit), then complete the **End-of-Session Checklist**.
- **Refactoring method:** You are responsible for choosing the best refactoring approach for each file. Use the plan's "Suggested extractions" as guidance, but apply the strategy that fits the file best (e.g. extract modules, split classes, simplify conditionals, reduce duplication, or other techniques). Preserve the public API; otherwise decide what to extract and how.
- **400-line rule:** The refactor target is **under 400 lines** per file (or the file turned into a package). A file is **not done** until it is under 400 LOC (or fully packaged). If the plan's suggested extractions are finished but the file is still over 400 lines, do the plan's optional extractions or add new extractions until the file is under 400. Skip only if the user explicitly asks to stop early.
- **Target files:** Use the file(s) specified in the user's message. If they only reference this doc without naming files, run `python tools/refactor/count_loc.py --biggest 6` from the project root and use the six printed paths as the refactor targets for this session (the six biggest files). Refactor all six in one session (see "Prompt to execute"). If the user names one or more files, use those. You may infer the target from the current refactor branch name (e.g. `refactor/slim-docx-renderer-renderer` -> `tools/docx_renderer/renderer.py`).
- **Do not** only summarize what the prompt says; run the commands, read the plan, implement extractions, run tests, and commit as described.
- **Checklist mandatory:** You must complete every item on the **End-of-Session Checklist** before considering the session done. If any item is not finished, continue working until it is (or report a blocker). Do not end the session with an incomplete checklist.

---

## Prompt to execute

When executing, work on one or more target files. If no files were specified, run `python tools/refactor/count_loc.py --biggest 6` and use the six printed paths. Then **for each target file in order** (biggest first, then second, and so on through sixth), do the following. Before starting each **subsequent** file (second through sixth), run `git checkout master` so each refactor gets its own branch.

**For each FILE in the target list:**

1. **Ensure we're at project root.** For the first file, run: `python tools/refactor/start_refactor.py FILE`. For the second through sixth files, first run `git checkout master`, then run the same start_refactor command for that FILE (so a new refactor branch is created for each file).
   - If the plan already exists you'll see "Plan already exists"; that's fine. Use `--update-plan` to refresh LOC/analysis, or `--no-branch` if we're already on that file's refactor branch and only need the plan.
   - Note the branch name and plan path from the output.
2. **Open the plan** at `docs/refactor/plans/` (the plan path from step 1). Read "Public API to preserve" and "Suggested extractions". If the file is **already under 400 LOC** (check with `count_loc.py --json` or the plan's "Current state"), and the plan has no remaining suggested extractions, skip extractions for this file and move to the next target. If the file is over 400 LOC, you must do extractions until it is under 400 (see 400-line rule above).
3. **Implement the refactor** for this file. Choose the best refactoring method for this file (the plan is guidance; you may follow suggested extractions or use a different approach that fits better). Preserve the exact public API listed in the plan.
   - Do **one** logical change at a time: e.g. create a new module and delegate, split a class, extract helpers, or simplify logic. Update the original file and imports accordingly.
   - After each extraction: run the **Test command** from the plan. If tests fail, fix before committing. If some failures persist, run the same test command on `master` to confirm they are pre-existing; if so, you may proceed with commits and note it.
   - Skip an extraction if it would only add indirection (e.g. methods already delegate to another module).
   - Commit with a clear message, e.g. `refactor(docx_renderer): extract format_* helpers to content_format.py`.
   - Repeat until the file is **under 400 lines** (or the user asks to stop after N extractions for this session). If the plan only lists "Optional" extractions and the file is still over 400 LOC, do those optional extractions or add new ones until under 400.
4. **When done with this file:** Run the test command one more time, verify the file is under 400 LOC (or packaged), then move to the next target (checkout master, then start_refactor for next FILE).

**After all target files are done:** Complete the **End-of-Session Checklist** (below). You must finish every item before the session is done.

---

## End-of-Session Checklist

The agent must complete every item before considering the session done. If any item is not finished, continue working until it is (or report a blocker). Run commands from project root.

- [ ] **Commits:** For each refactor branch used this session, all extractions are committed (one logical change per commit). Every commit was made after the plan's test command passed.
- [ ] **LOC:** For each refactored file, the file is under 400 lines (or has been turned into a package). If not, return to that file and do more extractions until it is under 400 (unless the user explicitly asked to stop early).
- [ ] **Merge:** For each refactor branch created this session (one at a time): ensure you are on master (`git checkout master`), then merge the refactor branch (`git merge <refactor-branch>`). Resolve any conflicts. Repeat for every refactor branch.
- [ ] **Docs:** REFACTORING_PRIORITIES_AND_TOOLS.md is updated: section **0.1** (Progress summary), section **1.4** (Done bullets for this session), and section **0.5** (line counts for changed areas).
- [ ] **LOC refresh:** Run `python tools/refactor/count_loc.py --markdown` for the changed areas (or full run) and update section **0.5** in REFACTORING_PRIORITIES_AND_TOOLS.md with the new line counts.
- [ ] **Push:** Push master to origin: `git push origin master`. If push is rejected (e.g. remote has new commits), pull first: `git pull origin master --rebase` or `git pull origin master`, then push again.

Only after every box above is checked may the session be considered complete.

---

Use the refactoring-workflow rule (`.cursor/rules/refactoring-workflow.mdc`) and docs in `docs/refactor/` (REFACTORING_TOOLS_FOR_CURSOR.md, GIT_DURING_REFACTORING.md) as needed. Prefer Agent mode so you can run commands and edit files.

---

## For the user: how to use this file

- **To run the full refactor:** Reference this file in chat (e.g. `@docs/refactor/CURSOR_REFACTOR_SESSION_PROMPT.md`). The agent will execute the prompt above. Optionally say which file(s) to refactor; if you don't, the agent runs `python tools/refactor/count_loc.py --biggest 6` and refactors the six biggest files in one session (each on its own branch).
- **400-line target:** Each refactored file must end up under 400 lines (or turned into a package). The agent will keep doing extractions until the file is under 400 unless you say to stop early.
- **End-of-Session Checklist:** The agent must complete every checklist item (commits, LOC, merge to master, docs update, LOC refresh, push origin) before the session is done. The agent will not end the session with an incomplete checklist.
- **To paste a custom prompt:** Copy the "Prompt to execute" section, replace FILE/target list as needed, and paste at the start of a session.
- **Agent mode:** Use Agent mode (not Ask) so the agent can run the script and commits.
- **One session, six files:** By default the agent refactors the six biggest files in one session. Each file gets its own refactor branch; after finishing one file, the agent checks out master and starts the next. The agent then merges each branch to master, updates docs, and pushes master to origin per the checklist.
- **Stopping early:** You can say e.g. "stop after 2 extractions this session" and the agent will stop after that many commits (for the current file); the checklist still applies for whatever was done.


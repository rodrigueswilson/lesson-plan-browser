# Git During Refactoring

This document describes how to use git during refactoring so work stays traceable, reviewable, and safe. The **single source of truth** for session order and workflow is [REFACTORING_PRIORITIES_AND_TOOLS.md](REFACTORING_PRIORITIES_AND_TOOLS.md) sections **0.2** (Session plan: branches, commits, merges) and **0.3** (Workflow rules). This doc is a companion that summarizes git practices for refactors.

---

## Branching

- **One refactor, one branch.** Create a dedicated refactor branch from latest `master`; do not mix refactoring with feature work or bug fixes on the same branch.
- **Session plan:** Use the branch names in REFACTORING_PRIORITIES_AND_TOOLS section 0.2 (e.g. `refactor/split-api`, `refactor/llm-service`) when starting a new session. Create the branch at the start of the session from `master`.
- **Start:** Pull latest `master`, then create the session branch from `master`.

---

## Commits

- **Small, atomic commits.** Break the refactor into logical steps (e.g. "extract module X", "update imports for X"). One clear change per commit so history is readable and easy to revert.
- **Run tests before committing.** Run the focused test set or full pytest (and frontend build if you touched the frontend) before each "working" commit. Do not commit broken or untested code.
- **Commit message:** Use a clear, conventional message (e.g. `refactor(api): split into routers by domain`). When the scope for that session is done and tests pass, commit with a message that describes what was refactored.
- **Splitting mixed changes:** If a branch has mixed edits, use `git add --patch` or `git add --edit` to stage changes in focused chunks so each commit has a single purpose.

---

## Merge to master

- **When to merge:** When the refactor scope for that session is complete and tests pass (and any manual smoke checks per section 0.2). Do not merge half-done or failing refactors.
- **After merge:** Update REFACTORING_PRIORITIES_AND_TOOLS.md: move the item to "Done" in section 0.1, and add a one-line bullet under section 1.4 (Done). If line counts changed, refresh section 0.5 using `python tools/refactor/count_loc.py --markdown` (see [LOC_AND_METRICS.md](LOC_AND_METRICS.md)).

---

## References

- **Session plan and workflow:** [REFACTORING_PRIORITIES_AND_TOOLS.md](REFACTORING_PRIORITIES_AND_TOOLS.md) sections **0.2** and **0.3**.
- **End-of-session checklist (commit, merge, docs, push):** [CURSOR_REFACTOR_SESSION_PROMPT.md](CURSOR_REFACTOR_SESSION_PROMPT.md) section **End-of-Session Checklist**.
- **Refreshing line counts:** [LOC_AND_METRICS.md](LOC_AND_METRICS.md).

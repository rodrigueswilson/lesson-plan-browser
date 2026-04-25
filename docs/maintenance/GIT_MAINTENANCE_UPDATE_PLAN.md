# Git Maintenance Update Plan

**Date:** 2026-03-27  
**Purpose:** Safely normalize repository state and make future Git updates predictable without mixing unrelated changes.

## Why this plan is needed

Current workspace has a large mixed state (tracked edits + many untracked files across docs, scripts, logs, DB artifacts, outputs).  
Without a maintenance pass, commits can easily include unrelated files and create noisy history.

## Protocol references (existing SSOT)

- `docs/refactor/GIT_DURING_REFACTORING.md`
- `docs/curriculum/PHASED_ROLLOUT_PLAN.md` (branch/test/merge policy)
- `docs/maintenance/decluttering_plan.md`
- `docs/maintenance/DECLUTTERING_LOG.md`

This plan follows those rules:
- small atomic commits,
- tests before each commit,
- no mixed-purpose commits,
- explicit verification after each phase.

---

## Phase 0 - Snapshot and guardrails

1. Capture baseline:
   - `git branch --show-current`
   - `git status --short --branch`
   - `git diff --stat`
2. Save the baseline summary into `docs/maintenance/DECLUTTERING_LOG.md` with date and owner.
3. Do not delete or move anything before categorization.

---

## Phase 1 - Classify file inventory

Create four buckets from current unstaged/untracked files:

1. **Source of truth code/docs** (candidate for commit)
2. **Generated artifacts** (`ingest_reports`, logs, output previews, temp files)
3. **Local runtime data** (`*.db-shm`, `*.db-wal`, cache/session artifacts)
4. **One-off diagnostics/research scripts**

Record classification in:
- `docs/maintenance/DECLUTTERING_LOG.md` (high-level)
- optional table in `docs/maintenance/PHASE_8_OBSOLETE_FILES_REVIEW.md` for keep/archive/delete decisions.

---

## Phase 2 - Git hygiene controls

1. Update ignore rules (if missing) for clearly generated/runtime files:
   - DB sidecars (`*.db-shm`, `*.db-wal`)
   - log/output/temp directories
   - local cache artifacts
2. Keep user-intent artifacts unignored if they are evidence docs intended for version control.
3. Verify:
   - `git status --short` shows reduced noise for generated/runtime files.

---

## Phase 3 - Atomic commit strategy

Commit in small topical batches (example order):

1. **Curriculum parser + tests**
2. **Curriculum evidence/research docs**
3. **Roadmap/doc planning changes**
4. **Maintenance-only cleanup changes**

For each batch:
1. stage explicit files (`git add <paths...>`)
2. validate staged diff (`git diff --staged --stat`)
3. run relevant tests
4. commit with purpose-specific message

Do not use broad `git add .` in mixed-state sessions.

---

## Phase 4 - Branch and merge discipline

1. For maintenance waves, use dedicated branch naming:
   - `maintenance/git-hygiene-<date>`
2. Merge only after:
   - test pass,
   - docs updated,
   - change log updated.
3. Push and re-check:
   - `git push -u origin <branch>`
   - open PR or merge per team policy.

---

## Phase 5 - Verification and closeout

1. Post-merge checks:
   - `git status --short --branch`
   - `git log --oneline -n 10`
2. Update `docs/maintenance/DECLUTTERING_LOG.md` with:
   - what changed,
   - verification command/results,
   - rollback notes (if any).
3. Add a short "next maintenance trigger" note:
   - run this plan again when untracked/unstaged volume exceeds agreed threshold.

---

## Recommended first execution scope

Start with a **non-destructive pass**:
1. classify inventory,
2. tighten ignore rules for obvious generated/runtime artifacts,
3. stage only maintenance-doc updates.

Then proceed in later sessions with code/archive moves.


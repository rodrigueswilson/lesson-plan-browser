# End-of-Session Checklist (Reusable)

**Purpose:** Standard wrap checklist for curriculum phase sessions so completion, evidence, and handoff are consistent.

**Related:**
- `docs/curriculum/PHASED_ROLLOUT_PLAN.md`
- `docs/curriculum/PHASE_EXECUTION_TEMPLATE.md`
- `docs/curriculum/NEXT_SESSION_PROMPT_SNIPPETS.md` (copy/paste trigger lines)
- `docs/CONTRIBUTING.md` (tests, pre-commit, GitHub expectations)
- `docs/refactor/GIT_DURING_REFACTORING.md`
- `docs/maintenance/GIT_MAINTENANCE_UPDATE_PLAN.md`

**Deferred curriculum UX (do not forget to list in handoff):**
- `docs/curriculum/LOCAL_FIRST_LINKS_BACKLOG.md`
- `docs/curriculum/MATH_LESSON_PORTAL_AND_TEACHER_GUIDE_UX.md`
- `docs/curriculum/KNOWN_UI_LIMITS.md`

---

## 0) “Ripe session” bar (quick)

A session is **ripe to close** when:

- [ ] Intent of the session is **done** or **explicitly parked** with a doc link (no silent deferrals).
- [ ] Tests you touched are **green** (at least CI-parity: `python -m pytest tests/ -m unit -q` from repo root; more if you changed critical paths).
- [ ] **Handoff** is copy-pasteable: result, summary, evidence paths, next trigger (see §7).

---

## 1) Phase/session decision

- [ ] Mark result: **PASS** or **BLOCKED**
- [ ] Write one-line completion summary
- [ ] List blockers (max 3, only unresolved)

Template:

```text
Result: PASS|BLOCKED
Summary: <one line>
Blockers:
- <blocker 1>
- <blocker 2>
- <blocker 3>
```

---

## 2) Evidence capture

- [ ] Save/confirm evidence paths:
  - [ ] ingest report(s) in `ingest_reports/`
  - [ ] test outputs / verifier outputs
  - [ ] research/profile artifacts (if applicable)
  - [ ] checkpoint report under `docs/curriculum/acceptance-evidence/`

Template:

```text
Evidence:
- <path 1>
- <path 2>
- <path 3>
```

---

## 3) Quality gate closeout

- [ ] Run required gate checks for the phase scope
- [ ] Run tests before wrap commit
- [ ] If refactor occurred, run tests again after refactor sequence
- [ ] Confirm no unresolved critical defects before phase advancement

---

## 4) Documentation updates

- [ ] Update phase/report docs with final status (e.g. `docs/curriculum/acceptance-evidence/`, unit checklists)
- [ ] Update empirical/research notes if this session produced new evidence
- [ ] Record deferred items explicitly in the right backlog doc (links in **Related** above)
- [ ] If curriculum **Explorer / API** behavior changed, skim `docs/curriculum/LOCAL_SOURCE_FILES.md` for operator-facing accuracy

### Good practice (end of session)

- **One story per commit** when possible; avoid mixing unrelated refactors with feature work.
- **Evidence over claims:** paste paths to `ingest_reports/`, verifier logs, or test output in the handoff block.
- **SSOT:** do not duplicate long procedures; link `PHASE_EXECUTION_TEMPLATE.md` and this checklist from PR descriptions when relevant.

---

## 4.5) Refactor-session gate (between phases)

- [ ] Decide if a dedicated refactor session is needed **before** starting the next phase.
- [ ] If yes, schedule it explicitly as the first item of next session.
- [ ] Follow existing refactor protocol:
  - [ ] one refactor, one branch (`docs/refactor/GIT_DURING_REFACTORING.md`)
  - [ ] one extraction per commit (`.cursor/rules/refactoring-workflow.mdc`)
  - [ ] run plan test command before each refactor commit

**LOC target policy (guideline, not hard stop):**
- Aim for modules around **300–400 LOC** when feasible.
- Do not force splits that hurt cohesion/API clarity.
- If a file remains above target, document rationale and next extraction candidate.

---

## 5) Git / version-control wrap

- [ ] Confirm current branch and status
- [ ] Stage only intended files (no mixed-purpose staging)
- [ ] Review staged diff
- [ ] Commit with clear purpose message
- [ ] Push branch/target branch per policy
- [ ] Verify remote update

Recommended commands:

```bash
git status --short --branch
git diff --staged --stat
git log -1 --oneline
git push
```

### 5.1) GitHub procedures (PR / CI)

- [ ] **Branch:** Prefer `curriculum/phase-<n>-<scope>` or `feature/<topic>` per `PHASED_ROLLOUT_PLAN.md` / team convention.
- [ ] **Pull request:** Open (or update) a PR with a **short description** in full sentences: what changed, why, how to verify.
- [ ] **CI:** Let GitHub Actions finish (e.g. `.github/workflows/ci-integration-tests.yml`, `pip-audit.yml` on dependency changes). Fix or document failures before merge.
- [ ] **Dependabot:** If this session bumped `requirements.txt` or lockfiles, note any Dependabot follow-up in the PR or a maintenance issue.
- [ ] **Pre-commit:** From repo root, `pre-commit run --all-files` before push when you changed many files (see `docs/CONTRIBUTING.md`).

---

## 6) Next-session trigger prompt

- [ ] Save a short trigger prompt in exact format:

```text
Start Phase <N>: execute docs/curriculum/PHASE_EXECUTION_TEMPLATE.md for <phase-scope>, run test gate #1, implement in-scope only, and report PASS/BLOCKED with evidence paths.
```

- [ ] Add optional first command for immediate resume:

```text
First command: <exact command>
```

- [ ] If refactor session is queued, use:

```text
Start Refactor Session: execute docs/refactor/GIT_DURING_REFACTORING.md workflow for <target-file-or-plan>, run plan test command before each extraction commit, and report PASS/BLOCKED with evidence paths.
```

---

## 7) Final handoff block (copy/paste)

```text
Result: PASS|BLOCKED
Summary: <one line>
Top evidence:
- <path>
- <path>
Deferred:
- <item>
Next trigger:
Start Phase <N>: execute docs/curriculum/PHASE_EXECUTION_TEMPLATE.md for <phase-scope>, run test gate #1, implement in-scope only, and report PASS/BLOCKED with evidence paths.
```

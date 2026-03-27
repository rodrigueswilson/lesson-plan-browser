# Curriculum Phased Rollout Plan (Unit-to-Grade-8)

**Purpose:** Define strict phase boundaries, completion criteria, and expansion strategy so implementation remains controlled and measurable.

## Program objective

Deliver a curriculum pipeline that is:
- extraction-faithful,
- provenance-complete,
- UI-clear for teachers,
- robust across unit templates and subjects,
- ready to scale through Grade 8.

## Mandatory phase git and quality workflow

Every phase must follow this sequence:

1. **Create phase branch**
   - naming: `curriculum/phase-<n>-<short-scope>`
2. **Implement only in-scope work**
   - no out-of-scope coding inside the phase branch
3. **Run phase test gate**
   - required tests defined in phase checklist
4. **Refactor pass (if tests pass)**
   - apply minimal refactors aligned to DRY/SOLID and current phase scope
5. **Run tests again**
   - same suite must pass after refactor
6. **Merge and push**
   - merge to integration branch/main process
   - push to GitHub only after both test passes are green

If step 3 fails, do not proceed to refactor or merge.

## Mandatory end-of-phase wrap-up

At the end of each phase, close the session with:

1. Phase result: `PASS` or `BLOCKED`.
2. One-line summary of what was completed.
3. List of blockers (if any), max 3 bullets.
4. Evidence paths (tests, reports, screenshots).
5. **Very short next-phase trigger prompt** saved in session notes.

### Next-phase trigger prompt format

Use this exact short format:

`Start Phase <N>: execute docs/curriculum/PHASE_EXECUTION_TEMPLATE.md for <phase-scope>, run test gate #1, implement in-scope only, and report PASS/BLOCKED with evidence paths.`

## End-of-phase refactor protocol (from docs/refactor)

At the end of each implementation phase, apply refactoring practices from:
- `docs/refactor/GIT_DURING_REFACTORING.md`
- `docs/refactor/REFACTORING_TOOLS_FOR_CURSOR.md`
- `docs/refactor/REFACTORING_PRIORITIES_AND_TOOLS.md`
- `docs/refactor/LOC_AND_METRICS.md`

Required end-of-phase sequence:

1. Identify touched files that are good refactor candidates.
2. If a touched file has a plan in `docs/refactor/plans/`, follow that plan strictly.
3. Keep refactor commits small and atomic (one extraction/purpose per commit).
4. Run focused tests before each refactor commit.
5. Run full phase test gate after refactor sequence.
6. Refresh LOC snapshot:
   - `python tools/refactor/count_loc.py --markdown`
7. Update refactor tracking docs if changed in this phase:
   - progress summary and done notes in `docs/refactor/REFACTORING_PRIORITIES_AND_TOOLS.md`
8. Merge and push only after all tests remain green.

## Program end state

This phase series ends when all of the following are true:
- quality gates pass on a representative cross-grade/cross-subject sample set (through Grade 8),
- parser variance is controlled with documented fallback behavior,
- provenance and run reports are always present,
- navigator UX supports lesson/unit progression and cross-grade semantic links,
- regression suite is stable enough for routine ingestion expansion.

After that, the project transitions from "hardening" to "production expansion" (bulk ingestion and continuous onboarding of units).

---

## Phase definitions

## Phase 0 - Program lock and baseline

**Goal:** Freeze target scope, baseline behavior, and acceptance artifacts before major changes.

**Sub-stage (Phase 0):** Prior-art and external landscape research — time-boxed review of GitHub/Stack Overflow and related material against our end-to-end extraction and ingestion pipeline. **Topic map, deliverables, and integration rules:** [`docs/curriculum/PRIOR_ART_RESEARCH_SUBSTAGE.md`](./PRIOR_ART_RESEARCH_SUBSTAGE.md). **Output home:** [`docs/curriculum/research-notes/`](./research-notes/).

**In scope**
- Confirm target acceptance unit and source IDs.
- Baseline ingest output, API payloads, and UI screenshots.
- Finalize quality gates and acceptance protocol.
- Complete the Phase 0 research sub-stage memo and source log (see sub-stage checklist exit criteria in `PRIOR_ART_RESEARCH_SUBSTAGE.md`).

**Out of scope**
- New parser features not tied to baseline correctness.
- Broad multi-unit ingestion.

**Exit criteria**
- Baseline evidence archived.
- No unresolved ambiguity in quality gates.
- Research sub-stage evidence archived under `docs/curriculum/research-notes/` (memo + sources + **reflexive review memo** per `PRIOR_ART_RESEARCH_SUBSTAGE.md`).
- Branch `curriculum/phase-0-baseline` merged and pushed after phase tests.

---

## Phase 1 - Provenance and fidelity foundation

**Goal:** Make one unit fully traceable and fidelity-verified end-to-end.

**In scope**
- Persist provenance metadata (unit + lesson).
- Expose provenance in API and UI source panel.
- Emit ingest run manifest in `ingest_reports/`.
- Pass all gates for one target unit.

**Out of scope**
- Full navigator search/index.
- Cross-grade linking automation.

**Exit criteria**
- `Unit-Complete` status for target unit with evidence.
- Branch `curriculum/phase-1-provenance-fidelity` merged and pushed only after:
  - phase tests pass,
  - refactor pass is complete,
  - tests pass again.

---

## Phase 2 - Unit intro parity and UX navigation hardening

**Goal:** Remove UX ambiguity and ensure unit intro quality equals lesson quality.

**In scope**
- Unit intro extraction parity and validation.
- Top navigation model (breadcrumb, previous/next lesson, previous/next unit).
- Ensure selected lesson context appears near top immediately.

**Out of scope**
- Full semantic search and recommendation ranking.

**Exit criteria**
- Teacher navigation acceptance passes for target unit.
- Branch `curriculum/phase-2-intro-ux` merged and pushed after double-pass tests (pre/post refactor).

---

## Phase 3 - Template resilience (same subject ladder)

**Goal:** Prove robustness within same subject before cross-subject expansion.

**In scope**
- Add at least 2 additional Grade 3 Math units (different structure patterns).
- Expand regression checks for heading variants and section drift.
- Tune parser heuristics only where evidence supports changes.

**Out of scope**
- Grade 3 ELA onboarding.

**Exit criteria**
- All sampled Grade 3 Math units pass gates with no critical parser regressions.
- Branch `curriculum/phase-3-template-resilience` merged and pushed after required phase test rerun.

---

## Phase 4 - Cross-subject hardening (Grade 3 ELA first)

**Goal:** Validate subject-config separation and parser generalization.

**In scope**
- Onboard one Grade 3 ELA unit sample set.
- Validate standards/procedure boundaries for ELA-specific patterns.
- Compare fidelity and section coverage against Math baseline.

**Out of scope**
- Broad multi-grade rollout.

**Exit criteria**
- Grade 3 ELA sample passes the same quality gates.
- Branch `curriculum/phase-4-cross-subject` merged and pushed after passing phase tests twice (before and after refactor).

---

## Phase 5 - Cross-grade representative sample (through Grade 8)

**Goal:** Build confidence that code is robust enough for broad ingestion.

**In scope**
- Curate representative sample matrix across Grades 2-8.
- Include high-variance templates and edge-case structures.
- Track pass/fail rates and parser exception classes.

**Out of scope**
- Bulk ingest all available units.

**Exit criteria**
- Sample matrix meets target pass threshold (see below).
- Branch `curriculum/phase-5-cross-grade-sample` merged and pushed only when all sampled rows meet gate policy.

---

## Phase 6 - Navigator and semantic progression features

**Goal:** Deliver pedagogical browsing improvements once core fidelity is stable.

**In scope**
- FTS5 (or approved search index) with highlighted results.
- Cross-grade semantic unit links (manual + assisted suggestions).
- Rationale display for related-unit links.

**Out of scope**
- Advanced autonomous agent planning features.

**Exit criteria**
- Teacher can navigate lesson progression and grade-to-grade progression clearly.
- Branch `curriculum/phase-6-navigator-semantic-links` merged and pushed after stable UX and regression tests.

---

## Phase 7 - Expansion readiness and controlled scale-up

**Goal:** Start broader ingestion with safety controls.

**In scope**
- Bulk onboarding in batches with run reports and rollback path.
- Continuous QA monitoring for newly ingested units.
- Maintenance cadence for parser and subject configs.

**Exit criteria**
- Transition to continuous ingestion mode approved.
- Branch `curriculum/phase-7-expansion-readiness` merged and pushed with operational signoff.

---

## Representative sampling strategy

## Stage A - Initial hardening sample
- Grade 3 Math Unit 2 (anchor unit)
- Grade 3 Math Unit X (different layout)
- Grade 3 Math Unit Y (different layout)

## Stage B - Subject contrast
- Grade 3 ELA Unit A
- Grade 3 ELA Unit B (if needed for variance)

## Stage C - Vertical sample to Grade 8
- At least one Math and one ELA unit per grade cluster:
  - Grades 2-3
  - Grades 4-5
  - Grades 6-8
- Prioritize units with known structural variety and standards complexity.

## Pass threshold recommendation
- 100% pass on critical gates (schema, provenance, boundary correctness).
- >=95% pass on fidelity spot checks across sample lines.
- 0 unresolved critical defects before next stage.

---

## Governance and change control

- Any parser behavior change requires:
  - reason tied to failing gate,
  - before/after evidence,
  - rerun of impacted sample units.
- Failure classification must use `docs/curriculum/FAILURE_TAXONOMY.md` as SSOT.
- Ingest reports must include and preserve:
  - `primary_failure_code`
  - `secondary_failure_codes`
  - `ingest_stats`
- For gate runs tied to a specific ingest, run `python tools/scraper/verify_curriculum_db.py --ingest-report ingest_reports/<run_id>.json` so verification outcomes are written back to the same run artifact.
- No phase advancement with open critical defects.
- Keep all phase decisions and acceptance evidence in `docs/curriculum/acceptance-evidence/`.

## Good-practice compliance checklist (.cursor/rules aligned)

Before merging each phase branch, verify:

- **SSOT:** no duplicated truth source for schema, parser behavior, or metadata definitions.
- **DRY:** duplicated logic extracted where repetition is proven.
- **KISS:** simplest implementation that meets current phase scope.
- **YAGNI:** no speculative features beyond the phase definition.
- **SOLID:** parser, API, and UI responsibilities remain separated and focused.
- **Project architecture:** changes remain consistent with `README.md` architecture.

For refactor tasks that have a plan under `docs/refactor/plans/`, follow `refactoring-workflow.mdc`:
- one extraction per commit,
- run the plan test command before each commit.

---

## Decision checkpoint: when to start broad ingestion

Start broad ingestion only after Phase 5 and Phase 6 exit criteria pass:
- representative sample validated through Grade 8,
- search/navigation UX stable,
- provenance and regression controls fully operational.

Until then, ingestion stays in curated batches only.

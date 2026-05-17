# LP2 Program Charter

Status: Proposed
Last updated: 2026-04-25

## Purpose
Define how `LP` (stable lane) and `LP2` (innovation lane) coexist during the transition period, while minimizing delivery risk for the current school year.

## Program Principles
- Keep `LP` stable and support-focused until school-year close.
- Use `LP2` for architectural experiments and next-generation capabilities.
- **If the summer deliverable (agentic line and/or chosen database) is not ready in time, `LP` remains the supported product** until the new stack meets promotion gates.
- Promote changes from `LP2` to `LP` only when they pass explicit gates.
- No direct destabilizing work lands in `LP` without rollback clarity.
- During the reflection period, no physical LP2 clone execution starts.

## Lane Definitions

### LP (Stable Lane)
- Scope: bug fixes, reliability patches, critical UX issues, low-risk quality improvements.
- Out of scope: major architecture changes, broad schema migrations, deep dependency shifts.
- Release policy: small, predictable, low-risk releases.

### LP2 (Innovation Lane)
- Scope: agent-centric architecture, container and portability improvements, retrieval/database decisions.
- Out of scope: production-cutover assumptions or LP2 clone execution before gate approval.
- Release policy: research-driven milestones with benchmark-backed decisions.
- Repository policy: LP2 runs in a dedicated repository (`LP2`) once clone execution is approved.

## Repository and Content Separation Policy
- LP2 must be created as a dedicated/cloned repository, not as a long-lived branch inside `LP`.
- Before clone creation, the team runs a repository audit of `LP` to classify content into:
  - required in LP2 baseline,
  - optional/migrate later,
  - excluded from LP2 (temporary artifacts, local logs, one-off dumps, stale generated files).
- LP remains the source for historical context and fallback references during transition.

## LP Audit Requirement Before LP2 Creation
- Produce an `LP` inventory report (code, docs, data, scripts, local artifacts) with owner and keep/drop rationale.
- Define copy rules for LP2 bootstrap (allowlist-first) to avoid carrying unnecessary files.
- Define ignore rules for LP2 from day one (`.gitignore`, data/log/cache exclusions) to prevent artifact drift.
- Capture migration notes for anything intentionally left in `LP`.

## Left-Behind File Access Policy
- LP2 may reference files left in `LP` only through explicit, documented paths/pointers.
- LP2 docs must include where these files live in `LP`, why they were not copied, and who owns migration timing.
- Any LP dependency discovered after clone kickoff must be triaged as:
  1. copy now into LP2,
  2. keep as temporary LP reference with deprecation date, or
  3. retire as no longer needed.

## Governance Model
- Weekly architecture checkpoint: status, risk, decisions pending.
- Biweekly stakeholder review: assess readiness for promotion candidates.
- Decision records required for:
  - containerization target,
  - portability baseline,
  - database direction.

## Promotion Rules (LP2 -> LP)
1. Functional readiness: feature behavior validated with acceptance criteria.
2. Operational readiness: backup/restore and rollback path documented and tested.
3. Performance readiness: meets agreed latency/quality thresholds.
4. Risk readiness: no unresolved high-impact risks.

If any criterion fails, promotion is deferred.

## Branching and Integration Guidance
- Keep `LP` and `LP2` separated logically (long-lived branches or separate root app path), with controlled cherry-picks/ports.
- Fix defects in active lane first, then port when needed.
- Avoid bidirectional drift by requiring migration notes for each promoted change.

## RACI (Lightweight)
- Product owner: priorities and gate approval.
- Architecture lead: technical recommendation and decision records.
- Engineering lead: execution plan and rollback readiness.
- QA owner: verification and release sign-off.

## Exit Criteria for Transition Phase
- LP2 container/portability baseline validated on target machines.
- Database architecture gate resolved with benchmark evidence.
- First promotion-ready LP2 capability accepted through all gates.

## Further reading (industry patterns)
For curated external articles and how they map to this charter (strangler-style evolution, branch by abstraction, parallel change, database expand/contract, and risks of long-lived divergence), see [LP2_EXTERNAL_REFERENCES_AND_PRACTICES.md](LP2_EXTERNAL_REFERENCES_AND_PRACTICES.md).

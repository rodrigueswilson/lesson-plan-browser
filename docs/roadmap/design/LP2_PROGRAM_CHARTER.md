# LP2 Program Charter

Status: Proposed
Last updated: 2026-04-23

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

# LP2 Execution Roadmap (8 Weeks)

Status: Planning
Last updated: 2026-04-25

## Intent
Use an 8-week transition window for research, documentation, and controlled LP2 execution under approved governance constraints.

Planning note: database transition work is preferred for summer execution (before next school year), subject to gate approval.

## Risk posture and fallback
- **Current `LP` remains the production fallback** if, by the end of summer, MariaDB (or the chosen store) and the agentic line are not yet ready. No forced cutover.
- Summer work can intentionally **optimize for the best agentic architecture** (retrieval, agents, skills, clear SSOT and contracts), even when that means more implementation effort and more careful database design.

## Sequencing: evidence before platform lock-in
1. **Use recent curriculum reality as input.** Ingestion of Math, ELA, and the more complex Science curriculum in SQLite is recent evidence of how grade/subject/course structure, units, and lesson artifacts need to be stored and queried. That workload should **inform** which database and schema patterns best support an agentic stack, not the other way around.
2. **Next design step: reference and assessment documents in the store.** Before committing to full container/MCP rollout, define how **WIDA framework** materials, **Newark Teacher Assessment** (and similar) documents are represented: metadata, chunks or segments, versioning, and retrieval keys. This is a prerequisite for realistic benchmarks and a sound `retrieve_context` contract.
3. **Then stack decisions.** With document storage and retrieval needs clearer, sequence **containers → MCP/tools surface → database decision (e.g. MariaDB vs alternatives) → agents and skills** in an order that avoids rework.

## Phase Plan

### Weeks 1-2: Research Consolidation
- Finalize LP2 governance and lane policy.
- Finalize containerization and portability recommendation.
- Validate database gate criteria and benchmark protocol.
- Publish architecture decision inputs in roadmap docs.
- Define LP2 dedicated-repo creation criteria and bootstrap strategy (allowlist-first copy).
- Start LP repository audit to identify what is unnecessary for LP2 baseline.

### Weeks 3-4: Documentation Hardening
- Convert strategy docs into implementation-ready checklists.
- Define acceptance tests for portability and backup/restore.
- Prepare decision review package for stakeholders.
- Finalize LP audit report: keep/migrate/exclude classification with owners.
- Draft LP2 migration manifest and explicit exclusions (`logs`, caches, one-off artifacts, large local dumps).

### Weeks 5-6: Readiness Validation (Conditional Go Active)
- Dry-run benchmark plan design (datasets, query suites, scoring templates).
- Dry-run migration and rollback playbook structure.
- Confirm team ownership and operating cadence for LP2.
- Dry-run LP2 bootstrap from manifest and verify excluded-content policy.
- Validate "left-behind in LP" lookup policy (documented references, temporary dependency tracking).

### Weeks 7-8: Closure Tracking and Controlled Start
- Stakeholder review of all LP2 strategy docs.
- Track D4/D5 conditional-waiver closure against dated requirements and owners.
- Proceed with LP2 clone kickoff and repository creation under Conditional Go controls.
- Approve LP-to-LP2 audit outputs and leftover dependency handling policy.

## Current Decision Boundary
Conditional Go is approved. During this roadmap window, the team executes LP2 clone stand-up while enforcing D4/D5 dated closure requirements and escalation on missed closure dates.

## Deliverables by End of Week 8
- Approved LP2 program charter.
- Approved containerization and portability strategy.
- Approved database decision gates.
- Approved execution checklist for LP2 clone kickoff.
- Approved LP audit dossier (keep/migrate/exclude inventory for LP2).
- Approved LP2 bootstrap manifest (what is copied, what is intentionally excluded).
- Approved LP left-behind reference protocol for temporary dependencies.

## Stop Conditions
Do not begin LP2 clone execution if any are true:
- unresolved high-impact risk in governance or operability,
- missing rollback plan,
- unapproved portability baseline,
- D4/D5 waiver closure date is missed or waiver ownership is missing.

## Go Conditions for Next Cycle
- Decision package accepted by stakeholders.
- Owners assigned for each LP2 workstream.
- Initial milestone plan reviewed and sequenced.
- Summer migration calendar approved (including rollback rehearsal dates before school-year start).

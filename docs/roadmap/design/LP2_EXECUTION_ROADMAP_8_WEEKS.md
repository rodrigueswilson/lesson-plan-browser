# LP2 Execution Roadmap (8 Weeks)

Status: Planning
Last updated: 2026-04-23

## Intent
Use an 8-week transition window for research, documentation, and decision readiness, without starting LP2 clone execution during the current reflection period.

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

### Weeks 3-4: Documentation Hardening
- Convert strategy docs into implementation-ready checklists.
- Define acceptance tests for portability and backup/restore.
- Prepare decision review package for stakeholders.

### Weeks 5-6: Readiness Validation (No Clone Yet)
- Dry-run benchmark plan design (datasets, query suites, scoring templates).
- Dry-run migration and rollback playbook structure.
- Confirm team ownership and operating cadence for LP2.

### Weeks 7-8: Reflection and Approval
- Stakeholder review of all LP2 strategy docs.
- Finalize go/no-go for initiating physical LP2 clone.
- If approved, schedule LP2 clone kickoff and database migration track in the summer execution window.

## Current Decision Boundary
During this roadmap window, the team prepares LP2 and defines gates, but does not start the physical LP2 clone until post-reflection approval.

## Deliverables by End of Week 8
- Approved LP2 program charter.
- Approved containerization and portability strategy.
- Approved database decision gates.
- Approved execution checklist for LP2 clone kickoff.

## Stop Conditions
Do not begin LP2 clone execution if any are true:
- unresolved high-impact risk in governance or operability,
- missing rollback plan,
- unapproved portability baseline.

## Go Conditions for Next Cycle
- Decision package accepted by stakeholders.
- Owners assigned for each LP2 workstream.
- Initial milestone plan reviewed and sequenced.
- Summer migration calendar approved (including rollback rehearsal dates before school-year start).

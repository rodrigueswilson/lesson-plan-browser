# Architecture Gate Decision Memo

Status: Draft recommendation for roadmap gate
Last updated: 2026-04-23
Owner: Architecture review

## Executive Recommendation
Proceed with a **phased decision path**:
1. Keep current operational data direction (`SQLite + Supabase/PostgreSQL`) for near-term roadmap execution.
2. Run a bounded retrieval pilot that compares:
   - PatternA (current + vector sidecar), and
   - PatternC (hybrid MariaDB retrieval pilot).
3. Defer PatternB (MariaDB-primary migration) unless benchmark thresholds and migration-readiness criteria are met.

This recommendation minimizes delivery risk while still validating MariaDB vector advantages against real workload evidence.

Planning update: because workload and data complexity are expected to increase, the preferred timing for any major DB migration is summer (pre-school-year), not in-term execution.

## Why This Is Recommended
- Current roadmap contracts and sync assumptions are already aligned with SQLite/Supabase.
- Retrieval architecture is already abstraction-friendly through `retrieve_context`.
- MariaDB vector capabilities are promising, but operational and migration impact must be proven locally, not assumed from vendor materials.

## Option Summary
- PatternA: fastest to execute, strongest roadmap alignment.
- PatternB: highest potential consolidation, highest migration/sync risk.
- PatternC: controlled exploration with limited blast radius.

See:
- `ARCHITECTURE_GATE_OPTION_MATRIX.md`
- `ARCHITECTURE_GATE_BENCHMARK_PROTOCOL.md`
- `ARCHITECTURE_GATE_RISK_REGISTER.md`
- `ARCHITECTURE_GATE_SOURCE_BRIEF.md`

## Go / No-Go Criteria

### Go for broader MariaDB adoption only if all are true
1. Benchmark total score >= 75/100 and hard constraints pass.
2. Retrieval quality is not worse than baseline and leakage remains under hard threshold.
3. Migration and rollback plans are validated in rehearsal.
4. Operational ownership and runbook are approved.

### No-Go conditions
- Hard benchmark constraints fail.
- Rollback path is unproven.
- Sync architecture impact remains unresolved.

## Fallback Strategy (if No-Go)
- Continue PatternA (current relational + vector sidecar).
- Keep provider abstraction so MariaDB can be revisited later without contract changes.
- Re-open gate after:
  - two roadmap increments,
  - refreshed benchmark corpus,
  - and updated vendor lifecycle/pricing review.

## Timeline Proposal
- Week 1: finalize benchmark corpus/query suite and infrastructure setup.
- Week 2: run PatternA baseline and PatternC pilot.
- Week 3: repeat runs, produce scorecards, execute rollback drill.
- Week 4: architecture review and final gate decision.
- Summer window (post-decision): if approved, execute staged migration/hardening before next school year.

## Required Outputs For Final Approval
- Completed scorecards for each pattern.
- Evidence log with source links + version/date.
- Migration/rollback rehearsal report.
- Signed architecture decision record with chosen path.

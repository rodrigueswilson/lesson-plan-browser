# LP2 Database Decision Gates

Status: Proposed
Last updated: 2026-04-23

## Goal
Select LP2 database direction for relational + vector retrieval with explicit evidence thresholds and fallback paths.

This document is decision support for the reflection period and does not authorize LP2 clone execution by itself.

## Planning Update (Summer Window Preference)
The current planning preference is to complete major database transition work during summer, before the next school year begins. This is driven by expected data growth and operational complexity:
- multi-curriculum storage by grade and subject,
- WIDA/pedagogical reference retrieval for high-frequency plan generation,
- expanded lesson-plan persistence and output pipeline support (DOCX/PDF generation flow).

This preference increases priority for PatternB/PatternC evaluation during the pre-school-year window, while keeping go/no-go gates mandatory.

## Candidate Patterns
- PatternA: current relational baseline (`SQLite + Supabase/PostgreSQL`) + vector sidecar.
- PatternB: MariaDB-centered relational + vector in one engine.
- PatternC: hybrid transition (current operational DB + MariaDB/vector pilot for retrieval).

## Non-Negotiable Constraints
- Must preserve local-first reliability for desktop workflows.
- Must preserve SSOT boundaries between operational lesson data and retrieval/index data.
- Must include validated rollback path before production promotion.

## Gate Metrics

### Quality
- Precision and relevance on representative retrieval tasks.
- Cross-grade leakage rate below threshold.

### Performance
- P50/P95 retrieval latency within agreed target.
- Acceptable index build and incremental update times.

### Operability
- Backup/restore runbook proven in rehearsal.
- Migration complexity and incident recovery burden acceptable for team capacity.

### Cost
- Embedding and storage cost within forecast budget bands.
- No unbounded operational cost growth from chosen pattern.

## Suggested Thresholds
- Total score >= 75/100 from benchmark rubric.
- Cross-grade leakage <= 2%.
- P95 retrieval latency at or better than baseline target.
- Two successful restore drills for chosen path.

## Gate Sequence
1. Baseline run (PatternA).
2. Pilot run (PatternC and/or PatternB).
3. Repeat run for consistency.
4. Migration/rollback rehearsal.
5. Architecture review decision.

## Decision Logic
- Choose the first pattern that passes all hard constraints and total threshold.
- If multiple pass, choose lower operational complexity.
- If none pass, continue PatternA and defer full migration, but keep summer hardening work that improves readiness (schema prep, backup drills, provider abstraction).

## Fallback Policy
- Keep retrieval provider abstraction to avoid lock-in.
- Re-run gate after:
  - benchmark corpus refresh,
  - model lifecycle review,
  - and one additional roadmap increment.

# Architecture Gate Benchmark Protocol

Status: Draft for gate evaluation
Last updated: 2026-04-23

## Objective
Run a repeatable, apples-to-apples benchmark across candidate architecture patterns for retrieval:
- PatternA: current relational stack + vector sidecar
- PatternB: MariaDB as relational+vector primary
- PatternC: hybrid transitional pilot

## Benchmark Principles
- Same corpus, same query set, same embedding model family, same dimensionality per run.
- Same query orchestration contract (`retrieve_context`) for all patterns.
- Separate indexing benchmarks from online query benchmarks.
- Record full run metadata (versions, hardware, model IDs, dimensions, timestamps).

## Dataset
- Source: representative curriculum JSON ETL output aligned to current lesson planning usage.
- Minimum size for benchmark:
  - 3 grades
  - 3 subjects
  - 2 school-year versions
  - at least 1,000 retrievable components (lesson segments/resources)
- Include update scenarios:
  - unit replacement
  - unit deletion
  - same lesson updated across versions

## Query Suites

### SuiteA_ExactMetadataQueries
Examples:
- grade=3, subject=Math, unit=5, lesson=2, component=exit_ticket
- grade=2, subject=ELA, proficiency=emerging, lesson_type=co_teaching

### SuiteB_HybridQueries
Examples:
- semantic intent plus strict metadata filter (grade/subject guardrails)
- vocabulary concept similarity within grade boundary

### SuiteC_OperationalQueries
Examples:
- concurrent retrieval while background indexing runs
- repeated queries for cache behavior

Target: at least 200 total queries per suite, with frozen test set definitions.

## Metrics

### Quality
- `TopKPrecision@k` (k=5,10)
- `NDCG@10`
- `GroundednessPassRate` (manual rubric, 2-reviewer adjudication)
- `CrossGradeLeakRate` (must be low; strict metadata relevance)

### Latency
- `P50/P95/P99` for online retrieval request
- Index build duration
- Incremental re-index duration for replaced unit

### Cost
- Embedding generation cost per 1k documents
- Storage growth per 1k documents
- Monthly run-rate estimate (expected query volume)

### Operability
- Backup/restore complexity score
- Migration effort estimate (engineering days)
- Mean time to recover (simulated rollback drill)

## Scoring Rubric (100 points)
- Quality: 40
- Latency: 25
- Cost: 20
- Operability: 15

### Hard Gate Constraints
Fail gate automatically if any are true:
- CrossGradeLeakRate > 2%
- P95 online retrieval latency > target SLO for two consecutive runs
- No validated rollback path

## Execution Steps
1. Freeze corpus snapshot and query set.
2. Run indexing benchmark for each pattern.
3. Run query suites with warm/cold cache passes.
4. Execute update scenarios (replace/delete/version-conflict).
5. Collect costs and ops observations.
6. Repeat full run twice to confirm consistency.

## Evidence Schema (Per Run)
- Date/time
- Pattern ID
- DB/vector engine versions
- Embedding model ID and dimensionality
- Hardware profile
- Query suite versions
- Full metric outputs
- Known anomalies

## Reporting Format
- One scorecard per pattern.
- One comparative table with normalized scores.
- One recommendation section with threshold rationale.

## Suggested Initial Thresholds (can be tuned)
- Quality score >= 32/40
- Latency score >= 18/25
- Cost score >= 12/20
- Operability score >= 10/15
- Total score >= 75/100

Pattern must pass hard constraints and total threshold to be considered Go.

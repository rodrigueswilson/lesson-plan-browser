# Phase 3 checkpoint report

**Date:** 2026-03-27  
**Phase:** Phase 3 - Template resilience (same subject ladder)

## Phase result

**PASS** (with non-critical follow-up)

## One-line completion summary

Wave 1 same-subject resilience runs (Grade 3 Math Units 2, 1, and 3) completed with gates passing, and math-equation fidelity issue mitigated via OMML recovery.

## Key evidence paths

- Wave profile:
  - `docs/curriculum/research-notes/empirical-profile/2026-03-27-wave1-profile.json`
- Outliers memo:
  - `docs/curriculum/research-notes/2026-03-27-wave1-top-outliers-memo.md`
- Export-vs-parser + classification:
  - `docs/curriculum/research-notes/2026-03-27-export-vs-parser-classification-memo.md`
  - `docs/curriculum/research-notes/export-vs-parser/math-artifacts-1W1IBU71bwuGpP3M3NTdQXQSH8Jx8fRKF-l9I4Rdo2B4.json`
- Unit 3 post-fix run report:
  - `ingest_reports/2026-03-27T01-37-45Z_fa7edaef.json`

## Test and gate outcomes

- `python tools/scraper/verify_curriculum_db.py --ingest-report ingest_reports/2026-03-27T01-37-45Z_fa7edaef.json` -> pass
- `python -m pytest tests/test_math_fidelity_helpers.py tests/test_ingest_report_failure_codes.py tests/test_curriculum_gaps.py -q` -> pass

## What was fixed in this phase checkpoint

- Fraction/equation token loss in standards text (example: `NJSLS-MATH.CONTENT.4.NF.B.4`) is recovered during ingest from DOCX OMML.
- Readability polish added to avoid run-join glue (for example `a/bas` -> `a/b as`).
- Ingest reports now include warning signals for:
  - high `lessons_started/lessons_ingested` ratio (`ANCHOR_MISS` family),
  - suspected equation-token loss (`EXPORT_LOSS` family).

## Non-critical follow-up (carry to next cycle)

- Investigate and reduce high `lessons_started_to_ingested_ratio` in outlier units (currently warning-only).
- Continue Step W1.5 worksheet artifact fidelity study (planned/deferred module research), without changing curriculum DB ingestion scope.

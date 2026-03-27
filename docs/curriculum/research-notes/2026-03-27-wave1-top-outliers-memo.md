# Wave 1 top outliers memo (first three runs)

**Date:** 2026-03-27  
**Inputs:**  
- `ingest_reports/2026-03-27T00-36-54Z_593534ca.json` (Math_3_U2_1hBoK4uk)  
- `ingest_reports/2026-03-27T00-42-36Z_1f8e40bf.json` (Math_3_U1_13jAzcMR)  
- `ingest_reports/2026-03-27T00-55-49Z_b37e785b.json` (Math_3_U3_1W1IBU71)  
- `docs/curriculum/research-notes/empirical-profile/2026-03-27-wave1-profile.json`

## Quick outcome

- All three runs passed:
  - `python tools/scraper/verify_curriculum_db.py --ingest-report ...` => pass
  - `python -m pytest tests/test_curriculum_gaps.py -q` => pass
- No run produced taxonomy codes (`primary_failure_code` remained `null` for all three).

## Outliers by run-level metrics

1. **Highest stream complexity:** `Math_3_U1_13jAzcMR`
   - `lessons_started`: **71** (highest)
   - `paragraphs_appended`: **1558** (highest)
   - `instructional_resources` section hits: **44** (highest)
   - Interpretation: this is the strongest same-subject stress case so far.

2. **Highest procedure routing volume:** `Math_3_U3_1W1IBU71`
   - `procedure_html` section hits: **109** (highest)
   - `paragraphs_appended`: **1530** (near highest)
   - Interpretation: heavy procedure flow with fractions variance remained stable.

3. **Baseline anchor comparison:** `Math_3_U2_1hBoK4uk`
   - Lowest complexity among the three:
     - `lessons_started`: 37
     - `paragraphs_appended`: 1264
   - Interpretation: useful baseline, but no longer representative of upper variance.

## Gaps observed (non-gate in current protocol)

- `daily_instructional_task`, `success_criteria`, and `essential_questions` are empty across currently ingested lessons in `audit_curriculum.py`.
- This is currently a **profile signal** only (not failing the active gate set). Keep watch for future gate expansion.

## Immediate recommendation

- Proceed to export-vs-parser classification pass (research plan Part D) on at least one high-variance sample from:
  - Unit 1 (`Math_3_U1_13jAzcMR`), and
  - Unit 3 (`Math_3_U3_1W1IBU71`).
- Keep taxonomy unchanged for now; no evidence yet that new failure classes are needed.

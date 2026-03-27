# Export-vs-parser classification memo (Wave 1 outliers)

**Date:** 2026-03-27  
**Scope:** Wave 1 high-variance units
- `Math_3_U1_13jAzcMR` (`13jAzcMR9KqRj3P9rvgySxPWysPAGBh9GsftzT3sw8fg`)
- `Math_3_U3_1W1IBU71` (`1W1IBU71bwuGpP3M3NTdQXQSH8Jx8fRKF-l9I4Rdo2B4`)

**Inputs**
- `docs/curriculum/research-notes/export-vs-parser/wave1-u1-13jAzcMR9KqRj3P9rvgySxPWysPAGBh9GsftzT3sw8fg-metrics.json`
- `docs/curriculum/research-notes/export-vs-parser/wave1-u3-1W1IBU71bwuGpP3M3NTdQXQSH8Jx8fRKF-l9I4Rdo2B4-metrics.json`
- `ingest_reports/2026-03-27T00-42-36Z_1f8e40bf.json`
- `ingest_reports/2026-03-27T00-55-49Z_b37e785b.json`
- `docs/curriculum/research-notes/empirical-profile/2026-03-27-wave1-profile.json`

## Classified cases

1. **Case A - Table structure density differs strongly (both units)**  
   - Evidence: JSON table count = 8 for both units; DOCX nested table count = 27 (U1) and 31 (U3).  
   - Classification: **Export issue** (`EXPORT_LOSS`)  
   - Rationale: structural table representation differs substantially between Docs JSON and DOCX export shape.

2. **Case B - Hyperlink density differs strongly (both units)**  
   - Evidence: JSON hyperlink count = 240 (U1) / 225 (U3); DOCX hyperlink count = 512 (U1) / 502 (U3).  
   - Classification: **Export issue** (`EXPORT_LOSS`)  
   - Rationale: link encoding/duplication behavior differs by format; parser-only changes should not be the first response.

3. **Case C - Text volume inflation in DOCX path (both units)**  
   - Evidence: text length JSON = 157,868 (U1) / 163,035 (U3); DOCX = 875,199 (U1) / 1,090,274 (U3).  
   - Classification: **Export issue** (`EXPORT_LOSS`)  
   - Rationale: cross-format text payload inflation is too large to treat as simple parser routing drift.

4. **Case D - `daily_instructional_task` and `success_criteria` absent in both formats**  
   - Evidence: anchor hits are zero for both phrases in JSON and DOCX for U1 and U3; DB audit shows fields empty.  
   - Classification: **Template/data shape issue** (track as `EMPTY_FIELD`, not export-loss).  
   - Rationale: these labels are not present in the source representations for these units, so export mismatch is not the root cause.

5. **Case E - `lessons_started` >> `lessons_ingested` in outlier units**  
   - Evidence: U1 report shows 71 started vs 21 ingested; U3 report shows 60 started vs 20 ingested.  
   - Classification: **Parser/template interaction** (`ANCHOR_MISS` family signal).  
   - Rationale: lesson-title detection across mixed/linked content starts many candidates; filtering then drops many. This is parser behavior under variance, not export distortion.

6. **Case F - Fraction/equation tokens missing in Unit 3 Lesson 1 standards (UI-observed)**  
   - Evidence:
     - user-observed source screenshot shows fraction/equation notation (for example `a/b`, `1/b`, `5/4 = 5 x 1/4`),
     - DB stored value for `Math_3_U3_1W1IBU71_L1` + `NJSLS-MATH.CONTENT.4.NF.B.4` already contains blanks (`... fraction as a multiple of . ... equation .`),
     - Docs JSON context for `1W1IBU71bwuGpP3M3NTdQXQSH8Jx8fRKF-l9I4Rdo2B4` contains `equation: {}` placeholders in those positions,
     - DOCX `word/document.xml` around the same code contains OMML math nodes (`<m:oMath><m:f>...`) with numerator/denominator tokens.
   - Classification: **Export/Docs-API representation issue** (`EXPORT_LOSS`) with parser mitigation applied.
   - Rationale: loss occurs before UI rendering and before DB persistence; targeted OMML extraction was added to recover equation tokens during ingest.

## Decision summary

- Export-related classes are now evidenced (`EXPORT_LOSS`) and should stay in taxonomy.
- No new taxonomy codes are required yet.
- Highest-priority follow-up is parser-side instrumentation for the started-vs-ingested drop pattern (Case E), while treating Cases A-C as cross-format variance constraints.
- Case F is now classified as `EXPORT_LOSS` (confirmed in Docs JSON and DB).

## Next implementation action

1. Add a small ingest warning rule when `lessons_started / max(lessons_ingested, 1)` exceeds a threshold (for example `> 2.0`) and map to `ANCHOR_MISS` secondary code.
2. Keep export-vs-parser artifacts for Unit 1 and Unit 3 as baseline references for future waves.
3. For Case F mitigation, treat equation/fraction spans as fidelity-risk and avoid parser-side normalization in the LLM feed path.
4. Continue broad math-symbol research and detector coverage using `2026-03-27-math-symbols-and-formula-fidelity-research-plan.md`.

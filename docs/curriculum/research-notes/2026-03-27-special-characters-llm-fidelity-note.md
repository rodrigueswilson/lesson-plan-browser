# Special characters and LLM fidelity note

**Date:** 2026-03-27

## Why this matters

Math/fraction/equation symbols are semantic content, not formatting.  
If these tokens are missing before prompt construction, generated lesson plans can be materially wrong.

## Confirmed finding (Unit 3, Lesson 1)

- Target: `Math_3_U3_1W1IBU71_L1`, standard `NJSLS-MATH.CONTENT.4.NF.B.4`.
- Observation: fraction/equation tokens visible in source screenshot are missing in app text.
- Verification:
  - DB value already has blanks in those slots.
  - Docs JSON uses `equation: {}` placeholder elements at those locations (no equation payload text).
  - DOCX export contains OMML math nodes (`<m:oMath>`, `<m:f>`, numerator/denominator tokens such as `a` and `b`).
- Classification: `EXPORT_LOSS` (upstream of UI rendering).

## LLM feed implications

1. `flatten_for_llm()` must preserve whatever Unicode/math tokens are present (no normalization/stripping there).
2. Missing equation tokens should be treated as source-fidelity risk, not silently ignored.
3. Prompt builders should receive a warning marker when standards text appears to have equation placeholders (for example repeated `... of . ... equation .` patterns).

## Recommended engineering follow-ups

- Add a lightweight detector in ingest/reporting for likely equation-token loss and map to `EXPORT_LOSS` secondary code.
- Keep an artifact snapshot proving the representation split:
  - `docs/curriculum/research-notes/export-vs-parser/math-artifacts-1W1IBU71bwuGpP3M3NTdQXQSH8Jx8fRKF-l9I4Rdo2B4.json`
- Prefer source variants that preserve equation semantics when available (if Docs API/Drive export alternatives expose richer math payloads).
- Keep this case in acceptance evidence so future regressions are caught early.

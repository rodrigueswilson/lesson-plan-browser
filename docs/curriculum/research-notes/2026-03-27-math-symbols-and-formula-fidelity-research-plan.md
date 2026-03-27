# Math symbols and formula fidelity research plan

**Date:** 2026-03-27  
**Phase context:** Phase 3 (template resilience), after Wave 1 rows for Grade 3 Math.

## Why this research is now mandatory

We confirmed a high-impact fidelity risk: equation/fraction tokens can disappear in one representation path and degrade downstream LLM prompts and lesson-plan generation quality.

## Continuity with prior execution path

Before this issue surfaced, the execution path was:
1. Complete Wave 1 row #3.
2. Produce top-outliers memo.
3. Run export-vs-parser classification.
4. Add minimal instrumentation for started-vs-ingested ratio.

This issue is now integrated into that path as the next fidelity-hardening track (not a detour).

## Inserted step (before resuming prior next action)

Add a worksheet-PDF fidelity investigation step for bilingual companion files (EN + ES) used in Unit 3 lesson materials. This step is inserted now, then execution returns to the previously queued engineering sequence.

### Step W1.5 - Worksheet artifact fidelity study

1. Capture paired worksheet artifacts for the same lesson:
   - English worksheet PDF
   - Spanish worksheet PDF
2. Inspect whether math symbols/formulas are represented as:
   - selectable text,
   - embedded equation objects,
   - raster images.
3. Record layout invariants required for future localization:
   - page size, margins, image positions, line breaks around formulas, table widths.
4. Add findings to roadmap docs as prerequisites for a future EN->PT worksheet localization module.

## Confirmed technical finding

For `NJSLS-MATH.CONTENT.4.NF.B.4` (Unit 3, Lesson 1):
- Docs JSON represents equations as `equation: {}` placeholders (no textual payload).
- DOCX export contains OMML math (`<m:oMath>`, `<m:f>`, numerator/denominator tokens).
- Prior parser behavior used paragraph text that omitted OMML equation text.
- After targeted OMML recovery, DB now stores reconstructed math text (for example `a/b`, `1/b`, `5/4=5×1/4`).

## Research goals (beyond fractions)

1. Build a practical inventory of math/special token types in curriculum docs:
   - fractions, superscripts/subscripts, radicals, mixed numbers, inequalities, Greek letters, operators, set notation, geometry symbols.
2. Determine representation differences across sources:
   - Docs JSON (`equation`, `inlineObjectElement`),
   - DOCX OMML (`m:oMath` family),
   - UI-safe render path,
   - LLM feed text path.
3. Define prevention controls so similar losses are detected early.

## Source channels to research deeply

- **Internal repo artifacts**
  - `reference_docs/scraped/*/originals/*.json` (Docs API snapshots)
  - DOCX exports and `word/document.xml` OMML inspection
  - ingest reports + empirical profile artifacts
- **Prior-art repos reviewed in this project**
  - equation/OMML extraction handling patterns and limitations
  - export-vs-parser variance handling practices
- **Stack Overflow / public docs**
  - Docs API equation placeholder behavior
  - python-docx OMML limitations and workarounds
  - practical OMML-to-text conversion edge cases

## Minimum deliverables

1. **Representation matrix** (`docs/curriculum/research-notes/math-symbol-representation-matrix.md`)
   - one row per symbol type, one column per source format/path.
2. **Detection spec** (`docs/curriculum/research-notes/math-fidelity-detectors.md`)
   - rules that emit `EXPORT_LOSS`/`UNKNOWN` when tokens likely dropped.
3. **Recovery policy** (`docs/curriculum/MATH_FIDELITY_POLICY.md`)
   - what gets reconstructed, what stays raw, and fallback rules.
4. **Fixture set** (`tests/fixtures/math_fidelity/`)
   - curated snippets covering each symbol class.

## Implementation guardrails (YAGNI)

- Target only math token recovery in standards/procedure text paths first.
- Avoid full symbolic algebra rendering or complex equation engines for now.
- Prefer deterministic textual reconstructions for LLM feed (clear and inspectable).

## Proposed next engineering steps

1. Extend OMML text recovery coverage:
   - handle more OMML nodes (`nary`, delimiters, matrices, accents) incrementally.
2. Add detector metrics to ingest reports:
   - count recovered math tokens and unresolved equation placeholders.
3. Add acceptance checks:
   - selected standards must preserve expected formula tokens in DB/API/UI.
4. Add LLM feed audit:
   - sample prompts and verify formula-bearing standards remain intact.

## Success criteria

- No known formula-bearing standards show blank placeholders in DB/API/UI for sampled Wave units.
- Ingest reports include math-fidelity signals.
- At least one regression test fails when OMML extraction is intentionally disabled.

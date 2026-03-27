# PDF Worksheet Localization Module (EN -> PT, template-preserving)

## Purpose

Define a future module that localizes worksheet PDFs from English to Portuguese while preserving source layout and visual assets.

## Priority and sequencing

- **Status:** Planned (roadmap feature).
- **Priority right now:** Deferred while curriculum ingestion hardening is in progress.
- **Execution order:** Resume implementation only after current curriculum phases reach stable ingestion/fidelity gates for Board of Education lesson plans and curriculum.

## Why this exists

- Curriculum worksheets include math symbols/formulas where fidelity affects learning outcomes.
- Translation-only pipelines are insufficient if they break layout, equations, or image alignment.

## Initial scope

- Source: English worksheet PDFs used by lesson materials.
- Optional reference: existing Spanish worksheet PDFs for cross-checking structure and translation segmentation.
- Target: Portuguese worksheet PDFs with template fidelity.

## Non-goals (first iteration)

- No general-purpose desktop publishing editor.
- No arbitrary redesign of worksheet style.
- No OCR-heavy pipeline unless source pages require it.

## Pipeline concept (planned)

1. **Analyze source PDF structure**
   - classify text blocks, vector graphics, images, tables, equation-like regions.
2. **Extract translation units**
   - preserve positional metadata and reading order.
3. **Translate content**
   - EN -> PT with curriculum-aware glossary and math-token preservation rules.
4. **Recompose PDF**
   - inject translated text into original template geometry.
5. **Validate**
   - layout delta checks + symbol/formula integrity checks.

## Fidelity constraints

- Preserve:
  - page size, margins, and coordinates,
  - image sizes/positions,
  - equation semantics,
  - table and callout boundaries.
- Allow:
  - controlled line wrapping adjustments,
  - font fallback only if required for glyph coverage.

## Research checklist

- Determine how often worksheet math appears as:
  - selectable text,
  - equation objects,
  - embedded images.
- Measure expansion pressure EN->PT by block type.
- Define fallback strategy for image-embedded text segments.

## Planned evidence artifacts

- `docs/curriculum/research-notes/worksheet-localization/`
  - source structure reports,
  - EN/PT/ES block alignment samples,
  - fidelity diff outputs,
  - risk log and mitigation decisions.

## Integration notes

- Align with `design/WORKSHEET_MODULE.md`.
- Keep this module under roadmap/planned state until Phase priorities authorize implementation.

# Curriculum Quality Gates

**Purpose:** Pass or fail rubric for declaring a unit fully extracted and production-usable.

**Execution order:** Use the operator command order in `docs/curriculum/TEST_PROTOCOL_UNIT_ACCEPTANCE.md` (Step 2) so verifier outcomes are written back to `ingest_reports/<run_id>.json` via `--ingest-report`.

## Gate A - Schema and structural integrity

- Required tables and columns are present (`verify_curriculum_db.py` + validator).
- `standards_structured` exists and parses as a JSON array.
- Every structured standard item includes `panel`, `section`, `code`, and `description_lines`.

**Fail examples**
- `standards_structured` is empty for lessons expected to include standards.
- malformed JSON or mixed shapes in a single unit.

## Gate B - Content fidelity and character retention

- Character-level spot checks against source for representative sections.
- No suspicious punctuation stripping or unicode normalization regressions.
- Soft-break merge preserves meaning and sentence boundaries.

**Minimum required checks**
- 10 sampled lines across lesson sections.
- 2 standards blocks.
- 2 procedure blocks.

## Gate C - Standards/procedure boundary correctness

- No `Activity n`, `Warm-up`, resource headers, or workshop labels leaking into standards descriptions.
- Procedure subheaders are visible in rendered procedure content.

## Gate D - Provenance completeness

Each lesson and unit must expose:
- `source_doc_id`
- `source_url`
- `ingested_at`
- `ingest_run_id`
- parser/version marker

## Gate E - API contract stability

- OpenAPI documents lesson payload shape for generated clients.
- Backward compatibility is preserved or versioned changes are documented.

## Gate F - UI clarity and navigation

- Selected lesson appears near top immediately after click.
- Previous/next lesson controls are always visible in lesson view.
- Unit overview is clearly accessible.
- Source metadata panel is visible.

## Gate G - Regression safety

- Automated tests pass for parser and data quality checks.
- Ingest run report is generated and archived.
- Second-template smoke check passes (or is marked pending with owner and date).

## Exit criteria

A unit is marked **Unit-Complete** only if all gates pass, with evidence links captured in an acceptance report.

## Evidence bundle checklist

- test command output
- ingest report artifact
- API sample payloads
- screenshots/video of navigation and source panel
- reviewer signoff (data + UX)

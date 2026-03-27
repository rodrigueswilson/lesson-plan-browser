# Curriculum Implementation Playbook (Unit-Complete)

**Status:** Active execution playbook  
**Scope:** Make one target unit fully extracted, validated, traceable, and usable in UI end-to-end.  
**Primary target unit:** Grade 3 Math Unit 2 (Area and Multiplication), unless replaced by product decision.

## Purpose

This playbook prevents ad-hoc coding by defining strict execution gates. A task is done only when it satisfies the quality gates in `docs/curriculum/QUALITY_GATES.md`.

## Non-negotiable principles

- SSOT first: schema and docs before feature expansion.
- Provenance required: no lesson or unit content without source metadata.
- Fidelity visible: ingestion must report what was preserved, transformed, or skipped.
- UX clarity over density: users must instantly see where they are and what changed.

## Workstreams and sequence

### 1) Baseline and freeze (Day 0)

- Confirm target unit source IDs and URLs.
- Export current DB, API, and UI snapshots for baseline comparison.
- Freeze parser behavior for this acceptance cycle except documented fixes.

### 2) Provenance and lineage (Day 1)

- Implement and document metadata fields (unit and lesson level):
  - `source_doc_id`
  - `source_url`
  - `ingested_at`
  - `ingest_run_id`
  - `ingest_parser_version`
  - optional `content_hash`
- Expose fields in API and show them in a UI source panel.

### 3) Fidelity and quality gates (Day 1-2)

- Automate checks for:
  - standards leakage (activity headings inside standards descriptions)
  - structured standards shape integrity
  - soft-break merge sanity
  - non-empty required lesson sections
- Generate ingest run report artifact (`ingest_reports/<run_id>.json`).
- Ensure ingest report captures:
  - `primary_failure_code`
  - `secondary_failure_codes`
  - `ingest_stats`
- Use `docs/curriculum/FAILURE_TAXONOMY.md` as the only allowed source for failure code values.
- For verification tied to a specific run, execute:
  - `python tools/scraper/verify_curriculum_db.py --ingest-report ingest_reports/<run_id>.json`
  so failed checks are mapped into that run report's failure codes and warnings.

### 4) Unit intro extraction parity (Day 2)

- Extract and persist unit introduction with the same rigor as lessons.
- Keep both render-friendly and future-structured forms.
- Validate intro appears as first-class content in UI.

### 5) UX hardening for navigation (Day 2-3)

- Implement top navigation model in `docs/curriculum/UI_NAVIGATION_SPEC.md`.
- Ensure lesson selection scroll/focus behavior is immediate and obvious.
- Add previous/next lesson and previous/next unit controls.

### 6) Acceptance run and signoff (Day 3)

- Run full protocol in `docs/curriculum/TEST_PROTOCOL_UNIT_ACCEPTANCE.md`.
- Archive evidence in `ingest_reports/` and `docs/curriculum/acceptance-evidence/`.
- Mark unit as Unit-Complete only if all gates pass.

## What finished means for this cycle

A unit is complete when:

- data fidelity is validated,
- provenance is queryable and visible,
- UI navigation is clear and top-driven,
- intro plus lessons are consistently represented,
- all acceptance checks pass without manual exceptions.

## Immediate future tracks (after unit-complete)

- Navigator FTS5 index and highlighted search matches.
- Procedure structured JSON (`procedure_structured`) rollout.
- Gap Manager UI plus one-click ingest.

## New teacher-priority track: cross-grade semantic unit links

Teachers need fast vertical alignment context (previous and next grade equivalent units) while planning.

### Objective

For each unit, show:
- related unit(s) in previous grade,
- related unit(s) in next grade,
- relation reason (semantic topic match, not only unit number).

### Initial implementation approach

- Add a curated mapping table (`curriculum_unit_links`) with confidence and rationale.
- Seed with manual mappings for core topics (geometry, fractions, area, measurement).
- Add optional semantic suggestion pipeline (FTS plus embedding or rule assist), but keep human approval as SSOT.

### Acceptance criteria

- A teacher can open a unit and click one previous-grade and one next-grade related unit in two clicks or less.
- Each link shows reason text and relation source (`manual` or `assisted`).
- No implicit hard dependency on matching unit numbers.

## Related docs

- `docs/curriculum/PHASED_ROLLOUT_PLAN.md`
- `docs/curriculum/QUALITY_GATES.md`
- `docs/curriculum/FAILURE_TAXONOMY.md`
- `docs/curriculum/PROVENANCE_AND_LINEAGE.md`
- `docs/curriculum/UI_NAVIGATION_SPEC.md`
- `docs/curriculum/TEST_PROTOCOL_UNIT_ACCEPTANCE.md`
- `docs/scrapers/CURRICULUM_EXTRACTION_ARCHITECTURE.md`
- `docs/roadmap/design/CURRICULUM_NAVIGATOR_MODULE.md`

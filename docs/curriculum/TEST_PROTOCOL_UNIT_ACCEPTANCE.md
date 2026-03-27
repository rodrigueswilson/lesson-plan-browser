# Unit Acceptance Test Protocol

**Purpose:** Verify one curriculum unit end-to-end before expanding scope.

## Preconditions

- Target unit source document and ID are confirmed.
- DB path and environment are explicit.
- Parser version is recorded.

## Step 1 - Fresh ingestion run

- Recreate target curriculum DB (or clean migration path).
- Seed required unit row if needed.
- Ingest target unit source.
- Save run manifest in `ingest_reports/`.

## Step 2 - Schema and integrity checks

Run:
- `python tools/scraper/verify_curriculum_db.py`
- targeted test suite for curriculum helpers/parsers.

### Operator command order (run-linked classification)

Use this exact order when you want verify outcomes written back to the same ingest report:

1. Run ingestion and note `<run_id>` from `ingest_reports/<run_id>.json`.
2. Run verifier with report write-back:
   - `python tools/scraper/verify_curriculum_db.py --ingest-report ingest_reports/<run_id>.json`
3. Run targeted tests:
   - `python -m pytest tests/test_curriculum_gaps.py -q`
   - add phase-specific parser tests as needed.
4. Archive evidence:
   - verifier output,
   - test output,
   - final `ingest_reports/<run_id>.json` containing `primary_failure_code`, `secondary_failure_codes`, and `ingest_stats`.

Failure-code values must follow `docs/curriculum/FAILURE_TAXONOMY.md` (SSOT).

Assert:
- required columns exist,
- standards leakage checks pass,
- structured standards are present where expected.

## Step 3 - Fidelity checks

- Compare sampled lines from source against rendered/API content.
- Validate punctuation and special character retention.
- Validate section routing correctness (procedure vs standards).

## Step 4 - API checks

- Confirm unit and lesson endpoints return expected fields.
- Confirm provenance metadata is present in payload.
- Confirm OpenAPI exposes stable schema.

## Step 5 - UI checks

- Unit Overview visible and readable.
- Lesson appears near top immediately after selection.
- previous/next lesson controls work.
- source panel shows doc link and ingest metadata.
- related previous/next grade units (if mapped) are reachable.

## Step 6 - Evidence package

Collect:
- command outputs,
- API payload snapshots,
- UI screenshots or short video,
- signed gate checklist from `docs/curriculum/QUALITY_GATES.md`.

## Decision

- **Pass:** mark unit as `Unit-Complete`.
- **Fail:** open remediation issues grouped by gate (`A`..`G`) and rerun full protocol after fixes.

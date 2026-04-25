# Curriculum Provenance and Lineage

## Why this matters

Curriculum data must be auditable. Teachers and developers need to know where each lesson came from, when it was ingested, and which parser logic produced it.

## Required metadata model

### Unit-level

- `unit_id`
- `source_doc_id`
- `source_url`
- `source_title`
- `ingested_at`
- `ingest_run_id`
- `ingest_parser_version`
- optional `source_revision_hash`

### Lesson-level

- `lesson_id`
- `unit_id`
- `source_doc_id`
- `source_url`
- `source_anchor` (optional location hint)
- `ingested_at`
- `ingest_run_id`
- `ingest_parser_version`
- optional `content_hash`

## Storage strategy

- Persist canonical provenance with curriculum rows (or dedicated side tables if preferred).
- Keep one run manifest per ingestion in `ingest_reports/`.
- Never rely on logs alone as SSOT.

## API exposure

Add provenance fields to lesson and unit detail endpoints.

Minimum UI support:
- source panel with clickable URL,
- ingest timestamp,
- run ID,
- parser version.

## Run manifest format (example)

```json
{
  "run_id": "2026-03-26T19-30-00Z_g3u2",
  "target_unit": "Math_3_U2_1hBoK4uk",
  "source_doc_id": "1hBoK4uk0Z_GBEixY4wFHXtFi1gLOXarytFhKamftSOE",
  "started_at": "2026-03-26T19:30:00Z",
  "ended_at": "2026-03-26T19:33:41Z",
  "parser_version": "table_extractor@vX.Y.Z",
  "lessons_ingested": 18,
  "warnings": [],
  "fidelity_checks": {
    "sample_lines_checked": 10,
    "mismatches": 0
  }
}
```

## Governance

- Any row without provenance is invalid for production use.
- Any parser change affecting extraction requires parser version bump and new acceptance run.

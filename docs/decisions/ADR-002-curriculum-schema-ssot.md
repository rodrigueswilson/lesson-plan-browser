# ADR-002: Curriculum SQLite schema single source of truth

## Status

Accepted

## Context

Curriculum data is stored in SQLite (`curriculum.db`) and accessed via `backend/database/curriculum.py`. Multiple schema definitions existed (`tools/db/initialize_db.py`, `tools/db/init_curriculum_db.sql`, ad-hoc migrations), causing confusion and mismatches (e.g. vocabulary junction columns, `resources` table shape).

## Decision

1. **Canonical schema** for a new curriculum database is defined in **`tools/db/initialize_db.py`**, including `resources` and `lesson_resources` required by `CurriculumDatabase.upsert_lesson_resource`.

2. **`tools/db/init_curriculum_db.sql`** is **legacy reference only** and must not be treated as authoritative for new environments.

3. **Documentation** lives in **`tools/db/CURRICULUM_SCHEMA_SSOT.md`** and **`docs/scrapers/CURRICULUM_EXTRACTION_ARCHITECTURE.md`**.

4. **Validation**: `backend/database/curriculum_validation.py` verifies required tables/columns before curriculum API routes serve traffic.

## Consequences

- New environments should be initialized with `initialize_db.py` (or a future migration tool that tracks the same shape).
- Existing databases continue to work via `PRAGMA`-filtered upserts; missing tables surface as validation errors with actionable messages.

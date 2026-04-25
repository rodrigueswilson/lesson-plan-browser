# Database tooling (`tools/db`)

| File | Purpose |
|------|---------|
| [initialize_db.py](initialize_db.py) | **SSOT** for a fresh `curriculum.db` layout aligned with `backend/database/curriculum.py`. |
| [CURRICULUM_SCHEMA_SSOT.md](CURRICULUM_SCHEMA_SSOT.md) | Documents canonical curriculum schema and legacy files. |
| [init_curriculum_db.sql](init_curriculum_db.sql) | Legacy reference; superseded by `initialize_db.py` for new databases. |
| [extract_curriculum.py](extract_curriculum.py) | Bulk extract/insert pipeline; may assume wide `lessons` columns. |
| [g2_math_corpus.py](g2_math_corpus.py) | Grade 2 Math unit specs (registry SSOT: `reference_docs/scraped_registry.json` → Grade 2 → Math). |
| [ingest_g2_math_corpus.py](ingest_g2_math_corpus.py) | Batch Drive export + `ingest_wave_unit` for all `G2_MATH_UNITS`. |
| [g3_math_phase3_corpus.py](g3_math_phase3_corpus.py) | Grade 3 Math Phase 3 corpus (`G3_MATH_PHASE3_UNITS`). |
| [ingest_g3_math_phase3_corpus.py](ingest_g3_math_phase3_corpus.py) | Batch ingest for Grade 3 Math Phase 3. |

See also: [docs/scrapers/CURRICULUM_EXTRACTION_ARCHITECTURE.md](../../docs/scrapers/CURRICULUM_EXTRACTION_ARCHITECTURE.md).

# Empirical profile artifacts

Store Wave profiling outputs here as described in [2026-03-27-blind-spots-and-empirical-research-plan.md](../2026-03-27-blind-spots-and-empirical-research-plan.md) (Part C).

**Suggested filenames:** `YYYY-MM-DD-waveN-profile.json` (small aggregates; avoid full copyrighted body text in-repo).

**Inputs you already have:** ingest report JSON includes `ingest_stats`, `primary_failure_code`, `lessons_ingested`, and `warnings`; pair with gate outputs and `verify_curriculum_db.py` when building a profile row.

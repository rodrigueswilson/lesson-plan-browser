# Architecture Gate Source Brief

Status: Research draft for roadmap gate (MariaDB + embeddings exploration)
Last updated: 2026-04-23

## Purpose
Collect official, versioned evidence for the architecture gate that evaluates:
- Keep current direction (`SQLite + Supabase/PostgreSQL`) with a separate vector retrieval store.
- Move to MariaDB as primary relational+vector database.

## Internal Baseline (Current Roadmap)
- Current stack states `SQLite / Supabase PostgreSQL` for persistence and sync in `README.md`.
- `REFERENCE_DOCS_AND_LESSON_PLAN_ACCESS.md` defines `CurriculumContextService` and a DB-agnostic `retrieve_context` contract.
- `CURRICULUM_JSON_DATABASE_ETL.md` targets hybrid retrieval and explicitly discusses vector stores.
- `DATABASE_ARCHITECTURE_AND_SYNC.md` centers local-first sync around SQLite + Supabase.

These internal docs are the comparison baseline for all external claims below.

## External Official Sources

### MariaDB Vector (official)
1. MariaDB vector functions and vector type docs:
   - https://mariadb.com/docs/server/reference/sql-structure/vectors/vector-functions
   - https://mariadb.com/kb/en/vector-functions/
2. MariaDB vector table/index creation:
   - https://mariadb.com/docs/server/reference/sql-structure/vectors/create-table-with-vectors.md
3. MariaDB 11.8 release notes / changes:
   - https://mariadb.com/docs/release-notes/community-server/11.8/what-is-mariadb-118
   - https://mariadb.com/docs/release-notes/enterprise-server/11.8/whats-new-in-mariadb-enterprise-server-11.8
4. MariaDB Foundation vector project:
   - https://mariadb.org/projects/mariadb-vector/

### Google Embeddings (official)
1. Gemini embeddings docs:
   - https://ai.google.dev/gemini-api/docs/embeddings
2. Gemini API pricing:
   - https://ai.google.dev/gemini-api/docs/pricing
3. Gemini billing:
   - https://ai.google.dev/gemini-api/docs/billing
4. Vertex AI model page for Gemini Embedding 2:
   - https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/embedding-2
5. Google announcement for Gemini Embedding 2:
   - https://blog.google/innovation-and-ai/technology/developers-tools/gemini-embedding-2

## Extracted Evidence (to validate in local spike)

### MariaDB
- MariaDB documents native vector support including `VECTOR(N)`.
- Documented vector functions include:
  - `VEC_DISTANCE`, `VEC_DISTANCE_EUCLIDEAN`, `VEC_DISTANCE_COSINE`
  - `VEC_FromText`, `VEC_ToText`
- MariaDB documents vector indexing with an HNSW-style implementation and tunable parameters (`M`, distance metric).
- Release documentation indicates vector features are part of MariaDB 11.8 line.

### Google embeddings
- `gemini-embedding-2` is documented as the latest embedding model family entry for multimodal embeddings.
- Docs describe configurable output dimensionality (for storage/latency tradeoffs).
- Pricing and billing pages provide token-based cost model for embedding generation.

## Notes on Confidence and Caveats
- High confidence: API and SQL capabilities explicitly documented by official vendor docs.
- Medium confidence: performance comparisons vs other engines from vendor materials; must be validated locally.
- Medium confidence: lifecycle/GA/preview details can change; re-check model/status immediately before final gate decision.
- Non-official benchmark sources were intentionally excluded from gate-critical claims.

## Mandatory Re-validation Before Decision
1. Re-open all official pages and confirm current model/version status.
2. Re-confirm pricing at decision date (costs can change).
3. Validate MariaDB vector behavior with local representative queries.
4. Validate embedding dimensionality/cost-quality tradeoff on your real curriculum dataset.

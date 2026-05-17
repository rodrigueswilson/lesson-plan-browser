# Wave 1 — Pass 1 notes (pinned SHAs local to clone date)

Consolidated answers to [agentic_doc_extraction_index.md](../agentic_doc_extraction_index.md) research questions. Clones live under `research/agentic_doc_extraction/clones/` (gitignored).

## langextract

- **Grounding:** README states extractions map to exact source location; supports interactive HTML visualization for traceability.
- **Long inputs:** Chunking, parallel processing, multiple passes per README (“optimized for long documents”).
- **Constrained output:** Few-shot + schema; controlled generation on supported models (e.g. Gemini).
- **Evaluation / visualization reuse:** HTML viz can be pattern-only without full dependency.
- **LP:** Strong fit for A1/A3/A4 if second-pass LLM must cite spans; cross-check against cell JSON / `json_to_html` SSOT before replacing pipeline.

## docling

- **Document model:** `DoclingDocument` IR; exports Markdown, HTML, JSON, DocTags (per README).
- **Placement:** Candidate **beside** `RecursiveTableParser`—normalize exported DOCX for difficult layout; keep structured cell walk for hyperlinks/OMML until ADR.
- **Tables / reading order:** Explicit feature list includes table structure, reading order, formulas; compare to our OMML path in `table_extractor.py` via spike.
- **Offline / ops:** Local execution advertised; PyPI package—expect heavy optional deps; verify A5 in spike.

## unstructured

- **DOCX:** `partition_*` produces elements with metadata (see upstream docs in clone); may augment but not replace anchor routing without design.
- **Chunking:** Standard “chunk for RAG” patterns—useful reference for LLM excerpt sizing (A1/A5).
- **Redundancy:** Overlaps with Google JSON → markdown (`docs_processor`) + DOCX path—**Pattern-only** unless chunk metadata solves a measurable gap.

## marker

- **LLM mode:** Optional higher-accuracy path; trade latency/cost vs layout-only—confirm flags in upstream CLI/docs.
- **Tables / equations:** Competitor reference vs our OMML; not a drop-in for hyperlink SSOT.
- **License:** GPL-3.0 in `LICENSE`; model weights terms separate—**no vendoring**; sidecar/spike only with review.

## markitdown

- **DOCX → Markdown:** Worth side-by-side on one unit DOCX (future spike); nested tables vary by converter.
- **MCP:** Useful for agent tooling around ingest; optional for production.
- **LLM image description:** Likely noise for core lesson text; optional for resource-heavy docs.

## instructor

- **Validation / retry:** README positions as schema-first with validation; supports multiple providers via `from_provider`.
- **Overlap with backend/llm:** Evaluate whether to wrap existing client or add thin adapter—**Dependency-candidate** for repair loops (A1/A3).
- **Partial extraction:** Use optional fields / nested models to fill only missing lesson fields.

## firecrawl

- **Fetch vs extract:** Architecture reference for “normalize then schema extract”; core curriculum DOCX path **Out-of-scope**.
- **AGPL-3.0:** Confirmed in `LICENSE`—**Pattern-only** or **separate service**; no substantial paste into `tools/scraper` without review.

## crawl4ai

- **fit_markdown / filtering:** Reference for future HTML portals (A5).
- **Async browser:** Relevant if sources expand beyond Google Docs API—**Out-of-scope** for current `main.py` doc crawl.

## scrapegraph-ai

- **Graph steps:** Metaphor for unit → lesson → schema pipeline; curriculum likely needs explicit schema over NL-only goals.
- **LP:** **Pattern-only** for orchestration sketches.

## llama_index

- **Ingestion / agents:** Maps loosely to `ingest_to_curriculum` + workflow ideas; **deterministic DB ingest** remains SSOT—avoid full RAG stack unless ADR (YAGNI).
- **LP:** **Pattern-only** for Step 3–5 unless A3 explicitly needs retrieval-first architecture.

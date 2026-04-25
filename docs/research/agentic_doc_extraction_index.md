# Agentic document extraction — research index

Reference clones and spikes stay under [research/agentic_doc_extraction/README.md](../../research/agentic_doc_extraction/README.md) (ignored subdirs: `clones/`, `spikes/`). Update this file with **verdicts**, **pinned SHAs**, and **LP tags** as you complete Pass 1–2.

**Wave 1 (automated setup 2026-03-29):** Shallow clones and SHAs captured on that date; Pass 1/2 notes in [repos/wave_1_pass1_notes.md](repos/wave_1_pass1_notes.md), [repos/wave_1_pass2_traces.md](repos/wave_1_pass2_traces.md), [repos/wave_1_spike_summary.md](repos/wave_1_spike_summary.md).

**Wave 2 (deep study):** Follow [repos/wave_2_deep_study.md](repos/wave_2_deep_study.md) — evidence-backed Pass 1/2 on Instructor, Docling, and LangExtract first. **Consolidated notes:** [repos/wave_2_pass1_notes.md](repos/wave_2_pass1_notes.md). **Evidence log:** [repos/wave_2_evidence.md](repos/wave_2_evidence.md). **Plain-language summary for newcomers:** [wave_2_learnings_for_newcomers.md](wave_2_learnings_for_newcomers.md). **Docling vs LP hyperlink fixture (three artifacts):** [repos/DOCX_HYPERLINK_ARTIFACTS_COMPARE.md](repos/DOCX_HYPERLINK_ARTIFACTS_COMPARE.md). **All smokes + venv recipe:** [spikes/README.md](spikes/README.md).

## Extraction contract (research stance)

- **Deterministic-first SSOT:** `tools/scraper` deterministic parsing remains the authoritative source for curriculum structure and DB writes.
- **AI is optional second pass:** Agentic extraction is an assist path for ambiguous or missing sections; it is not a replacement parser.
- **No silent overwrites:** AI-assisted writes must be explicitly scoped per field in issue/ADR acceptance criteria before implementation.
- **Fail safe:** Missing key, timeout, or invalid AI output must preserve deterministic ingest output and emit run evidence (warning/failure code).
- **Traceability required:** Any AI-assisted result must preserve source provenance expectations (A4) and be auditable in wave evidence.

## Runbooks (execution order)

Step-by-step procedures for the research workflow:

1. [01 — Workspace and shallow clones](runbooks/01_workspace_and_clones.md)  
2. [02 — Pass 1 for all repositories](runbooks/02_pass1_all_repositories.md)  
3. [03 — Pass 2: top three deep dives](runbooks/03_pass2_top_three.md)  
4. [04 — Bounded spike (2–4 hours)](runbooks/04_bounded_spike.md)  
5. [05 — Research to product backlog](runbooks/05_research_to_product_backlog.md)  
6. [06 — License hygiene and regression](runbooks/06_license_hygiene_and_regression.md)  

## LP symptom tags

| Tag | Meaning |
|-----|---------|
| **A1** | Anchor drift — `SubjectConfig` / `_resolve_field_from_anchors` in [tools/scraper/table_extractor.py](../../tools/scraper/table_extractor.py) miss headings. |
| **A2** | ELA layout variance — [ela_lesson_plan_table.py](../../tools/scraper/ela_lesson_plan_table.py) / [ela_summary_table.py](../../tools/scraper/ela_summary_table.py) heuristics break. |
| **A3** | Validation / gaps — e.g. [verify_curriculum_db.py](../../tools/scraper/verify_curriculum_db.py); when to run an LLM second pass. |
| **A4** | Provenance / SSOT — hyperlinks, `data-resource-id`, cell JSON vs HTML-only ([CURRICULUM_EXTRACTION_ARCHITECTURE.md](../scrapers/CURRICULUM_EXTRACTION_ARCHITECTURE.md)). |
| **A5** | Cost / ops — API keys, offline requirement, batch ingest. |

**Verdict values:** `Adopt` | `Pattern-only` | `Dependency-candidate` | `Out-of-scope` | `TBD` (until Pass 1 done).

**Study order:** Docling, Unstructured, Marker, MarkItDown, LangExtract, Instructor, Firecrawl, Crawl4AI, ScrapeGraphAI, LlamaIndex (see README for clone URLs).

---

## Master table

| Repo | Purpose (one line) | LP tags | Verdict | SPIKE / PR | Deep notes | License (quick) | Pinned SHA | Pass |
|------|-------------------|---------|---------|------------|------------|-----------------|------------|------|
| [langextract](https://github.com/google/langextract) | LLM structured extract + source grounding | A1, A3, A4 | Dependency-candidate | — | [Pass 1](repos/wave_1_pass1_notes.md), [Wave 2](repos/wave_2_pass1_notes.md#langextract) | Apache-2.0 | fb874f5611a3b8eed1975b304a9537bcaa7d3034 | 2 |
| [docling](https://github.com/docling-project/docling) | Layout-aware doc → gen-AI formats (PDF/DOCX/…) | A2, A4, A5 | Dependency-candidate | — | [Pass 1](repos/wave_1_pass1_notes.md), [Wave 2](repos/wave_2_pass1_notes.md#docling) | MIT | f2834848aeaa63ac51f4968e1665b6b8e77b90e4 | 2 |
| [unstructured](https://github.com/Unstructured-IO/unstructured) | Partition many formats → elements for LLM/RAG | A1, A5 | Pattern-only | — | [Pass 1](repos/wave_1_pass1_notes.md) | Apache-2.0 | 47f4728e01b1b285affff7225b478bba087395f0 | 1 |
| [marker](https://github.com/datalab-to/marker) | PDF/DOCX → MD/JSON; optional LLM | A2, A4, A5 | Pattern-only | — | [Pass 1](repos/wave_1_pass1_notes.md) | GPL-3.0 | d63e3d943b2cbcfd9c809f141f9cdb21294001d5 | 1 |
| [markitdown](https://github.com/microsoft/markitdown) | Files / Office → Markdown for LLM pipelines | A4, A5 | Pattern-only | — | [Pass 1](repos/wave_1_pass1_notes.md) | MIT | a6c8ac46a684bac4b4a2377d67ff615264eb8f27 | 1 |
| [instructor](https://github.com/567-labs/instructor) | Pydantic structured outputs + providers | A1, A3 | Dependency-candidate | [spike summary](repos/wave_1_spike_summary.md) | [Pass 1](repos/wave_1_pass1_notes.md), [vs transform_runner](repos/instructor_vs_transform_runner.md) | MIT | 7cf80156d51b415f080b524c75ad320f3f093fa4 | 2 |
| [firecrawl](https://github.com/firecrawl/firecrawl) | Crawl/fetch → MD / schema extract | A5 | Out-of-scope | — | [Pass 1](repos/wave_1_pass1_notes.md) | AGPL-3.0 | 8935b753c5732f19740d7c34f080fe22890079fe | 1 |
| [crawl4ai](https://github.com/unclecode/crawl4ai) | Async crawl → LLM-friendly markdown | A5 | Out-of-scope | — | [Pass 1](repos/wave_1_pass1_notes.md) | Apache-2.0 | af648e104fd9b26788a7c9a717bcc518a9b83559 | 1 |
| [scrapegraph-ai](https://github.com/ScrapeGraphAI/Scrapegraph-ai) | LLM + graph pipelines for structured scrape | A1, A3 | Pattern-only | — | [Pass 1](repos/wave_1_pass1_notes.md) | MIT | 7b5733daec918c8087b09b6282a52bb41e138956 | 1 |
| [llama_index](https://github.com/run-llama/llama_index) | Ingestion, agents, workflows over documents | A3 | Pattern-only | — | [Pass 1](repos/wave_1_pass1_notes.md) | MIT | d3be017add958ea30686ddd9fa3bcbb06c917e1a | 1 |

Pass 2 traces: [repos/wave_1_pass2_traces.md](repos/wave_1_pass2_traces.md).

## Wave 1 backlog (product handoff)

1. **Instructor smoke:** Done (Wave 2 Run F — [repos/wave_2_evidence.md](repos/wave_2_evidence.md)). **Next product step (only if prioritized):** optional second pass in [tools/scraper](../../tools/scraper) behind a flag, A4 SSOT preserved, reuse [backend/llm](../../backend/llm); see [CURRICULUM_EXTRACTION_ARCHITECTURE.md](../scrapers/CURRICULUM_EXTRACTION_ARCHITECTURE.md) and [repos/instructor_vs_transform_runner.md](repos/instructor_vs_transform_runner.md).
2. **Docling evaluation:** Done for **real unit-export DOCX** (Wave 2 Runs D–E; compare [repos/DOCX_REAL_UNIT_DOCLING_VS_LP_COMPARE.md](repos/DOCX_REAL_UNIT_DOCLING_VS_LP_COMPARE.md)). Prior PDF + hyperlink fixture work remains in [repos/wave_2_evidence.md](repos/wave_2_evidence.md) and [repos/DOCX_HYPERLINK_ARTIFACTS_COMPARE.md](repos/DOCX_HYPERLINK_ARTIFACTS_COMPARE.md).
3. **LangExtract:** Short fixture (Run H), synthetic lesson-scale (Run I), and **real DB lesson** Grade 2 Unit 1 lesson 1 (Run J) in [repos/wave_2_evidence.md](repos/wave_2_evidence.md). Post-extract checks in `char_interval_verify.py` follow **LangExtract `alignment_status`** (`match_exact` → strict slice equality; `match_lesser` / `match_fuzzy` → in-range non-empty span). Optional **`LANGEXTRACT_SMOKE_REQUIRE_EXACT_ALIGNMENT=1`** requires all grounded rows to be `match_exact`. CI: `pytest tests/test_langextract_char_interval_verify.py` (no `langextract` install required).

## Wave 2 handoff — Runbook 05 ([05 — Research to product backlog](runbooks/05_research_to_product_backlog.md))

- **No `tools/scraper` change until:** a **named ingest gap** (A1–A5) is ticketed **and** the issue/ADR includes field ownership, invocation triggers, failure policy, and a verification gate per the runbook. Until then, deterministic ingest remains SSOT.
- **No new ADR in this wave:** integration proposals are deferred to sprint planning when a gap is chosen.

## Runbook 06 — license hygiene (2026-04-06)

- **AGPL (firecrawl) / GPL (marker):** Policy unchanged; see table below and [runbooks/06_license_hygiene_and_regression.md](runbooks/06_license_hygiene_and_regression.md).
- **Pinned SHA refresh:** `git fetch` run for **instructor**, **docling**, and **langextract** clones; **HEAD matches index** (no drift on this date). **Revisit cadence:** quarterly or before a major ingest redesign (runbook 06).

## License hygiene and revisit (wave 1)

| Repo | Policy |
|------|--------|
| **firecrawl** | AGPL-3.0 — **Pattern-only** or separate service; no substantial code paste into app repo without review. |
| **marker** | GPL-3.0 + upstream model terms — **sidecar/spike only** with compliance review before any dependence in LP packaging. |
| Permissive rows | Prefer PyPI dependency over vendoring; refresh **Pinned SHA** quarterly or before major ingest redesign; append dated line to [repos/wave_1_pass1_notes.md](repos/wave_1_pass1_notes.md) if **Verdict** changes. |

Full procedure: [runbooks/06_license_hygiene_and_regression.md](runbooks/06_license_hygiene_and_regression.md).

---

## Definition of done (each research wave)

- Every row above has **Verdict** not `TBD`, **LP tags** confirmed, and **Pinned SHA** after Pass 1.
- At least **three** repos have Pass 2 notes or a completed spike with a one-sentence outcome.
- At least **one** concrete next step for [tools/scraper](../../tools/scraper) (spike or doc) or an explicit “no code change until …”.

---

## Per-repository research questions

Use as a checklist; answers belong in the master table row (bullets) or in [repos/](repos/) if long.

### google/langextract

- How is **source grounding** represented (spans, offsets) for auditing against teacher-guide text?
- How are **long inputs** handled (chunking, windows, limits) for one lesson or one tab?
- What **constrained output** patterns are used (JSON mode, tools, validation)?
- Can we reuse **evaluation / visualization** ideas without the full stack?

### docling-project/docling

- What is the **canonical document model** and exports (Markdown, JSON)—placement **before** or **beside** `RecursiveTableParser` on exported DOCX?
- **Table structure** and **reading order** vs cell-walking + OMML in `table_extractor.py`?
- **PyPI** weight, runtime, **offline** fit (A5)?

### Unstructured-IO/unstructured

- How does **DOCX** partitioning expose elements and metadata—can metadata replace or augment **anchor** routing?
- Recommended **chunking** before LLM extraction?
- **Redundancy** vs [docs_processor.py](../../tools/scraper/docs_processor.py) + current DOCX path?

### datalab-to/marker

- When does **LLM-assisted** mode run; **accuracy vs latency** vs layout-only?
- **Tables and equations** vs our **OMML** handling?
- **License / commercial** constraints on models—acceptable for us?

### microsoft/markitdown

- **DOCX → Markdown** quality for **nested tables** vs a real unit export—worth a side-by-side?
- **MCP** pattern applicable to agent tooling without production dependency?
- **LLM image description**—useful for resources or noise?

### 567-labs/instructor

- **`response_model` + Pydantic** and **retry** on validation failure?
- Overlap vs [backend/llm](../../backend/llm) — one abstraction or redundant?
- **Partial extraction** (fill nulls only) patterns?

### firecrawl/firecrawl

- Separation of **schema extract** vs **crawl/fetch**—mirror in our normalize → extract design?
- **AGPL-3.0** implications for service / embed / copy-paste—record conclusion.
- **Out of scope** for non-web curriculum core ingest? State explicitly.

### unclecode/crawl4ai

- **Markdown / fit_markdown** ideas for future **HTML** curriculum portals?
- Async browser patterns if we leave Google Docs–only fetch?

### ScrapeGraphAI/Scrapegraph-ai

- **Graph** decomposition (fetch → parse → extract)—map to unit index → lesson tables → schema?
- NL goal vs **explicit schema**—which fits curriculum precision?

### run-llama/llama_index

- **Ingestion / document agents** vs `ingest_to_curriculum` and [main.py](../../tools/scraper/main.py) crawl—what maps?
- Avoid **RAG** overbuild if the goal remains **deterministic DB ingest** (YAGNI)?

---

## Optional deep-dive notes

Add a file under [repos/](repos/) only when the master row is insufficient. Link the filename in the **Deep notes** column.

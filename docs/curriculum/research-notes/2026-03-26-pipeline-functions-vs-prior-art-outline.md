# Pipeline functions ↔ prior-art equivalents (outline)

**Purpose:** Structure **our** processes and named responsibilities, then map each to **transferable** primitives—libraries, algorithms, or patterns—in ten public codebases. None of those repos implement *curriculum lesson extraction*; the mapping is about **how** they solve the same *mechanical* problems (API I/O, traversal, normalization, element streams, tables, etc.).

**Architecture SSOT:** [`docs/scrapers/CURRICULUM_EXTRACTION_ARCHITECTURE.md`](../../scrapers/CURRICULUM_EXTRACTION_ARCHITECTURE.md)  
**Repo survey:** [2026-03-26-github-repos-extraction-complexity-survey.md](./2026-03-26-github-repos-extraction-complexity-survey.md)  
**Source-level evidence (files read, § by §):** [2026-03-26-pipeline-outline-repo-evidence.md](./2026-03-26-pipeline-outline-repo-evidence.md)

---

## Reference: ten repositories (abbreviations)


| Abbr      | Repository                                                                                    | Role                             |
| --------- | --------------------------------------------------------------------------------------------- | -------------------------------- |
| **OOSDK** | [dotnet/Open-XML-SDK](https://github.com/dotnet/Open-XML-SDK)                                 | Typed OOXML / OPC (.NET)         |
| **OXDOC** | [OfficeDev/open-xml-docs](https://github.com/OfficeDev/open-xml-docs)                         | Open XML documentation           |
| **GWS**   | [googleworkspace/python-samples](https://github.com/googleworkspace/python-samples)           | Docs API usage samples           |
| **GAPC**  | [googleapis/google-api-python-client](https://github.com/googleapis/google-api-python-client) | Discovery HTTP client            |
| **PD**    | [python-openxml/python-docx](https://github.com/python-openxml/python-docx)                   | Python DOCX API                  |
| **UNS**   | [Unstructured-IO/unstructured](https://github.com/Unstructured-IO/unstructured)               | `partition()` → elements         |
| **DCL**   | [docling-project/docling](https://github.com/docling-project/docling)                         | Multi-format → `DoclingDocument` |
| **MM**    | [mwilliamson/python-mammoth](https://github.com/mwilliamson/python-mammoth)                   | Semantic DOCX → HTML             |
| **TIKA**  | [apache/tika](https://github.com/apache/tika)                                                 | Java parse façade / POI stack    |
| **PAN**   | [jgm/pandoc](https://github.com/jgm/pandoc)                                                   | Reader → AST → writer            |


---

## 1. Acquisition and credentials

### What we do


| Concern                                            | Our code (indicative)                                                                                            |
| -------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| OAuth2 desktop flow, token refresh, service builds | `[tools/scraper/docs_client.py](../../tools/scraper/docs_client.py)` — `DocsClient._authenticate`, `build('docs' |
| Fetch Docs JSON (tabs, body)                       | `get_document`                                                                                                   |
| Binary export (HTML, DOCX, …)                      | `export_document` → `drive_service.files().export_media`                                                         |
| Persist raw JSON snapshot                          | `get_document_json`                                                                                              |
| Binary download (non-Docs files)                   | `download_drive_file`                                                                                            |


### Problem shape

Reliable, authenticated **HTTP** to Google; **large responses**; **export limits** and transient failures.

### Equivalents (not drop-in; same problem class)


| Abbr     | What to study                                                                                 |
| -------- | --------------------------------------------------------------------------------------------- |
| **GWS**  | Minimal `InstalledAppFlow` + `documents().get` / export patterns                              |
| **GAPC** | `discovery.build`, default **retry/backoff** on 429/5xx; discovery-doc caching (v2)           |
| —        | `**google.api_core.retry`** (outside the ten repos but pairs with GAPC) for custom call sites |


**Algorithms / policies:** exponential backoff + jitter; idempotent “same `documentId` → same path” writes; **10 MB** `files.export` ceiling (official API constraint)—compare with your batch design, not a library function.

---

## 2. Document graph and link discipline

### What we do


| Concern                                        | Our code (indicative)                                                                                                             |
| ---------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| Recursive crawl, depth cap, visit dedup        | `[tools/scraper/crawler.py](../../tools/scraper/crawler.py)` — `CurriculumCrawler.crawl_root`, `_crawl_recursive`, `visited_docs` |
| Link typing (Doc / PDF / Slides / PPTX / HTML) | regex extractors + `doc_resource_map`                                                                                             |
| Link discovery from API JSON                   | `_extract_links_from_doc`, tab recursion                                                                                          |


### Problem shape

**Graph traversal** with **cycles**, **depth limits**, **typed edges**, **skip non-ingestible** targets.

### Equivalents


| Abbr     | What to study                                                                                                                              |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| **UNS**  | Ingest **connectors** concept: bounded fetch, same pattern family as ETL breadth limits (docs site + `unstructured-ingest` repo if needed) |
| **TIKA** | “One file in → routed parser” **facade** (different domain, same *orchestration* idea)                                                     |
| —        | Crawler docs (e.g. max depth, dedup)—**algorithm**, not lesson logic                                                                       |


No repo gives “curriculum-safe” crawl rules; equivalence is **control flow**, not content.

---

## 3. Google Docs JSON → linear / tabbed text

### What we do


| Concern                                    | Our code (indicative)                                                                                                                                            |
| ------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Structural walk of `tabs` / `body.content` | `[tools/scraper/docs_processor.py](../../tools/scraper/docs_processor.py)` — `GoogleDocsProcessor.process`, `_process_tab_to_dict_recursive`, `_process_element` |
| Markdown emission, inline objects / images | per-tab `markdown` + `images` dict                                                                                                                               |


### Problem shape

**Tree walk** of a **vendor JSON AST** → **lossy linearization** (Markdown) for human or secondary use.

### Equivalents


| Abbr    | What to study                                                                              |
| ------- | ------------------------------------------------------------------------------------------ |
| **GWS** | `docs/output-json` / quickstart: **ground truth JSON shape** for tables, paragraphs, links |
| **PAN** | **Reader** modules: AST as intermediate representation; explicit **lossiness** in README   |
| **MM**  | **Style → tag** mapping philosophy (semantic output, not pixel fidelity)                   |
| **UNS** | `partition` routing: “detect type → delegate”                                              |


Our JSON→MD is **domain-specific**; Pandoc/Mammoth are **different inputs** (DOCX/HTML) but the *pattern*—**recursive descent + emit**—matches.

---

## 4. DOCX ingest: structure extraction

### What we do


| Concern                                 | Our code (indicative)                                                                                                                                   |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Walk document tree (paragraph vs table) | `[tools/scraper/table_extractor.py](../../tools/scraper/table_extractor.py)` — `RecursiveTableParser.parse_element`, `_parse_paragraph`, `_parse_table` |
| Nested tables                           | `parse_element(..., depth=...)`                                                                                                                         |
| Paragraph JSON (runs, hyperlinks)       | `_parse_paragraph`                                                                                                                                      |
| Table → nested JSON / flatten           | `_parse_table`, `_table_to_text`, `flatten_elements`                                                                                                    |
| Optional LLM-oriented flatten           | `flatten_for_llm`                                                                                                                                       |


### Problem shape

**OOXML traversal**, **nested block** model, **run-level** fidelity, **table grid** extraction.

### Equivalents


| Abbr                  | What to study                                                                                           |
| --------------------- | ------------------------------------------------------------------------------------------------------- |
| **PD**                | Object model you already depend on: `Document`, `Paragraph`, `Table`, `Run`, underlying `lxml` elements |
| **OOSDK** + **OXDOC** | **Spec-level** behavior for `w:tbl`, merge, grid—when PD issues or heuristics need ground truth         |
| **UNS**               | `unstructured/partition/docx.py`: same `**import docx`** traversal + **table→HTML matrix** helpers      |
| **MM**                | ZIP/XML read path + **style-based** semantics (contrast with our anchor-based routing)                  |
| **PAN**               | DOCX **reader** implementation: mapping Word features into a **smaller** AST                            |
| **TIKA**              | Office parsing via stack (POI): “**many weird files → text/table-ish output**”                          |


---

## 5. DOCX ingest: stream, merge, and HTML assembly

### What we do


| Concern                                 | Our code (indicative)                                                                             |
| --------------------------------------- | ------------------------------------------------------------------------------------------------- |
| Ordered **semantic stream** from tables | `parse_to_stream`, `_table_to_semantic_items`                                                     |
| Word **soft-break** paragraph merge     | `merge_docx_soft_break_paragraphs`, `_should_merge_docx_soft_break`, `_merge_two_paragraph_items` |
| JSON-ish elements → HTML                | `json_to_html`, `_get_paragraph_inner_html`                                                       |


### Problem shape

**Buffering** and **reducing** noisy tokenization (split paragraphs); **HTML** emission with rules.

### Equivalents


| Abbr    | What to study                                                               |
| ------- | --------------------------------------------------------------------------- |
| **MM**  | Deliberate **normalization** (ignore visual noise; care about structure)    |
| **UNS** | **Element** types + **metadata** attachment; cleaners e.g. `clean_bullets`  |
| **PAN** | Filters / Lua transforms on **AST**—same *phase* as “merge then serialize”  |
| —       | **Hypothesis** / property tests (not in the ten repos)—for merge predicates |


---

## 6. Curriculum semantics (lesson routing)

### What we do


| Concern                                             | Our code (indicative)                                                                                     |
| --------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Subject-specific **anchors** and regexes            | `[tools/scraper/subject_config.py](../../tools/scraper/subject_config.py)` — `SubjectConfig.MATH` / `ELA` |
| Section guards (procedure vs standards, subheaders) | `_is_procedure_subheader`, `_is_non_standard_heading` in `table_extractor.py`                             |
| Flush buffered text into **lesson fields**          | `flush_buffer` → `lesson_data` keys, `standards_structured`, etc.                                         |
| Linked doc enrichment                               | `process_recursive_links`, DOCX export for linked procedures                                              |


### Problem shape

**Finite-state / rule-based sectioning** over a token stream; **template variance** across units.

### Equivalents


| Abbr    | What to study                                                                             |
| ------- | ----------------------------------------------------------------------------------------- |
| **MM**  | **Configurable style map** (declarative routing table vs our `SubjectConfig` dict)        |
| **UNS** | **Classifier** hooks / element categories—conceptual parallel to “Title vs NarrativeText” |
| **PAN** | Div/section mapping in readers—**pattern**, not NJ curriculum                             |
| **DCL** | **Reading order** and layout graph—relevant if you ever add layout-aware PDFs             |


**No equivalent “lesson plan compiler”** in those repos; the transferable part is **configuration-driven routing**, not standards codes.

---

## 7. Persistence, provenance, reports

### What we do


| Concern                      | Our code (indicative)                                                                                                                                                                  |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Normalized curriculum upsert | `ingest_to_curriculum` → `[backend/database/curriculum.py](../../backend/database/curriculum.py)`                                                                                      |
| Legacy / cache ingest        | `ingest_to_db`                                                                                                                                                                         |
| Run reports                  | `_build_ingest_report`, `_write_ingest_report` in `table_extractor.py`                                                                                                                 |
| Post-ingest checks           | `[tools/scraper/verify_curriculum_db.py](../../tools/scraper/verify_curriculum_db.py)`, `[backend/database/curriculum_validation.py](../../backend/database/curriculum_validation.py)` |


### Problem shape

**Transactional** DB writes, **schema-aware** upsert, **audit** artifacts.

### Equivalents


| Abbr                         | What to study                                                                                |
| ---------------------------- | -------------------------------------------------------------------------------------------- |
| **UNS** / **DCL** / **TIKA** | **Metadata** attachment on elements; batch **ingest** pipelines—**observability** ideas only |
| —                            | **SQLite migration** discipline (not specific to those ten repos)                            |


---

## 8. API surface

### What we do

FastAPI routers + Pydantic for curriculum read models (`[backend/routers/curriculum.py](../../backend/routers/curriculum.py)`).

### Equivalents in the ten repos

**None directly.** Versioning/OpenAPI patterns are a different literature (see prior-art memo Topic 7). Listed repos focus on **parsing**, not HTTP contracts.

---

## Compact matrix (function family × strongest prior-art anchor)

Rows are **our** function families; cells name where to look first for **mechanical** parallels.


| Our function family           | PD  | OOSDK/OXDOC | GWS/GAPC | UNS | MM  | PAN | DCL | TIKA |
| ----------------------------- | --- | ----------- | -------- | --- | --- | --- | --- | ---- |
| OAuth + API I/O               |     |             | ●        |     |     |     |     |      |
| Export / download             |     |             | ●        |     |     |     |     |      |
| Crawl / dedup / depth         |     |             |          | ○   |     |     | ○   |      |
| JSON tree → text              |     |             | ●        | ○   |     | ●   |     |      |
| DOCX tree walk                | ●   | ●           |          | ●   | ●   | ●   | ○   | ●    |
| Table grid / merge truth      | ○   | ●           |          | ○   | ○   | ○   | ○   | ○    |
| Run / hyperlink fidelity      | ●   | ●           |          | ●   | ●   |     |     |      |
| Soft-merge / normalize buffer |     |             |          | ●   | ●   | ●   |     |      |
| Style/anchor routing          |     |             |          | ○   | ●   | ○   |     |      |
| Intermediate document model   |     |             |          | ●   |     | ●   | ●   | ●    |
| Element stream → downstream   |     |             |          | ●   |     | ●   | ●   | ●    |


**Legend:** ● = strong mechanical overlap; ○ = partial / architectural analogy.

---

## How to use this outline

1. When debugging a **class of failure**, locate the **row** (e.g. table merges → §4 + matrix column PD/OOSDK).
2. Read the **external** code for **data structures and control flow**, not for lesson fields.
3. Prefer **one borrowed technique** (e.g. a normalization predicate, a retry wrapper) over **importing a whole second parser stack** unless an ADR changes SSOT.


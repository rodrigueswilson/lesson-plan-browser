# WIDA Framework as Operating System: Ingestion and Use Plan

**Status:** Planning  
**Goal:** Plan how to use the WIDA ELD framework as the "operating system" for creating lesson plans, including whether and how to build software that extracts or scrapes information from WIDA documents and converts it into databases, Markdown, and (optionally later) an embeddings/vector database.

**Related:** [REFERENCE_DOCS_AND_LESSON_PLAN_ACCESS.md](./REFERENCE_DOCS_AND_LESSON_PLAN_ACCESS.md), [reference_docs/WIDA_ELD/README.md](../../reference_docs/WIDA_ELD/README.md), [PHASE1_CURRICULUM_DOCUMENT_INVENTORY.md](./PHASE1_CURRICULUM_DOCUMENT_INVENTORY.md), [ASSESSMENT_MODULE.md](./ASSESSMENT_MODULE.md), [NOTEBOOKLM_WIDA_QUESTIONS_AND_BRIEF.md](./NOTEBOOKLM_WIDA_QUESTIONS_AND_BRIEF.md) (NotebookLM synthesis).

---

## 1. Two WIDA document types and how they differ

We ingest two distinct families; their structure differs and retrieval must respect that.

| Source | Key Uses | Domains / Modes | Slice dimensions |
|--------|----------|------------------|------------------|
| **Can Do Descriptors (Key Uses Edition)** | Recount, Explain, Argue, **Discuss** (Discuss = Listening + Speaking only) | Four domains: Listening, Reading, Speaking, Writing (all four for Recount/Explain/Argue; L+S only for Discuss) | grade_cluster, key_use, domain, proficiency_level |
| **ELD Standards Framework 2020** | Narrate, Inform, Explain, Argue | Two modes: **Interpretive** (listening, reading, viewing), **Expressive** (speaking, writing, representing) | grade_cluster, standard, key_language_use, communication_mode |

**Domain-to-mode mapping for 2020:** The app can keep "domains" (L/R/S/W) in the UI. When querying the 2020 Standards or PLDs, the backend must map **Listening and Reading → Interpretive**, **Speaking and Writing → Expressive**.

---

## 2. WIDA as "operating system" for lesson plans

The WIDA ELD framework (five standards, four Key Language Uses, grade clusters, Language Expectations, Language Functions and Features, plus Can Do Descriptors and related documents) provides the **shared structure and vocabulary** that lesson plans are built on. In that sense it acts like an **operating system**: a stable layer that defines how "programs" (lesson plans) are composed and what primitives they use (expectations, functions, features, Can Do descriptors).

To use this operating system in software we need:

- **Structured access:** The framework content must be queryable by (grade cluster, standard, key use, domain) so that when planning one slot we load only the relevant slice.
- **Stable representation:** PDFs are the authoritative source but are not directly queryable; we need derived representations (database, Markdown, or both) that preserve the known structure (see [WIDA_ELD/README.md](../../reference_docs/WIDA_ELD/README.md) – common structure of ELD materials).
- **Optional later:** If we later adopt semantic search, an embeddings/vector database could sit alongside or replace part of the metadata-based lookup for certain queries.

This document plans the **ingestion pipeline** (extract from source documents → convert to database and/or Markdown, and optionally to embeddings) and how it fits with the rest of the system.

---

## 3. Do we need a software module to extract or scrape?

**Yes, we should plan for one.** The WIDA PDFs (Can Do, ELD Standards 2020 per grade cluster, Language Charts, Standards FAQ) are not natively queryable by (grade cluster, standard, key use). To support:

- **Retrieval by slice** (e.g. "Grades 2-3, Standard 2, Inform" only),
- **Consistent structure** for the LLM (expectations + functions + features),
- **Registry and context service** that resolve a query profile to concrete content,

we need a **repeatable way** to get from PDF (and any future source) to structured content. That implies a **dedicated software module** (or tooling) for extraction and conversion, even if the first pass is semi-manual (e.g. script-assisted export plus hand-edited Markdown).

**Scope of the module:**

- **Inputs:** WIDA PDFs (and optionally other formats) under `reference_docs/` and `reference_docs/WIDA_ELD/`.
- **Process:** Extract or scrape text and structure (tables, headings, bullets) and map them to the known schema (grade cluster, standard, key use, expectations, functions, features). Parsing can use PDF libraries (e.g. PyMuPDF, pdfplumber) or OCR if needed; for complex layouts, a mix of automated extraction and manual review may be needed initially.
- **Outputs:** Database records and/or Markdown files (and optionally chunks + embeddings for a vector DB later). Output format is decided per document type (see below).

The module does **not** replace the document context service; it **feeds** it by producing the structured content (DB or files) that the CurriculumContextService reads.

**Extraction cues (for PDF parsing):** See [NOTEBOOKLM_WIDA_QUESTIONS_AND_BRIEF.md](./NOTEBOOKLM_WIDA_QUESTIONS_AND_BRIEF.md) synthesis (c) and (f). **Can Do Original Edition:** Grade cluster first, then domain. Heading `Can Do Descriptors: Grade Level Cluster [Band]`; domain = vertical all-caps (LISTENING, SPEAKING, READING, WRITING); slice end = next domain or cluster. Strip: introductory sentence, WIDA framework text, "Write in grade-level [Domain] expectations below:", NAMES column. **Can Do Key Uses Edition:** Hierarchy Key Use → domain. Grade cluster in top corner; Key Use = large vertical all-caps on far left (can span two pages); domain = second vertical block (marks row start). **Table:** domain = row, six ELP levels = columns (ELP Level 1 Entering … 6 Reaching). One slice = one row = six cells. Discuss may be labeled "ORAL LANGUAGE". Slice end = next domain label or table/page bottom. **2020 Framework:** Section 3 = grade-level materials. Key Use = primary organizer (prominent headings); under each = Language Expectations then Functions/Features. Split by mode (Interpretive/Expressive), marked by Reference Code suffix (`.Interpretive`/`.Expressive`) and action labels ("Interpret… by" / "Construct… that"). Reference Code pattern `Standard.GradeCluster.KeyUse.Mode` (e.g. `ELD-LA.2-3.Narrate.Expressive`): use as primary key or filename (e.g. `ELD-LA_2-3_Narrate_Expressive.md`); split on periods to populate columns. Backend: map domain (e.g. Writing) → Expressive, build code, fetch that chunk. Language Functions = bullet (●); Language Features = square (■), **Expressive only**; Standard 1 has no Language Features.

---

## 4. Output formats: database, Markdown, and (later) embeddings

### 4.1 Database (concrete schema from NotebookLM synthesis)

Separate tables for Can Do vs. 2020 content. Query by (grade_cluster, subject, key_use, and mode derived from domain) so the LLM receives only matching rows.

**Table `wida_2020_expectations`**

| Column | Example |
|--------|---------|
| reference_code (PK) | "ELD-LA.2-3.Inform.Expressive" |
| grade_cluster | K, 1, 2-3, 4-5, 6-8, 9-12 |
| standard | ELD-SI, ELD-LA, ELD-MA, ELD-SC, ELD-SS |
| key_language_use | Narrate, Inform, Explain, Argue |
| mode | Interpretive, Expressive |
| expectation_text | The high-level goal |
| language_functions | JSON array or related table |
| language_features | JSON array or related table (null for Interpretive and Standard 1) |

**Table `wida_can_do_descriptors`**

| Column | Example |
|--------|---------|
| grade_cluster | K, 1, 2-3, 4-5, 6-8, 9-12 |
| key_use | Recount, Explain, Argue, Discuss |
| domain | Listening, Speaking, Reading, Writing, or Oral Language |
| level_1_entering | Text |
| level_2_emerging | Text |
| level_3_developing | Text |
| level_4_expanding | Text |
| level_5_bridging | Text |
| level_6_reaching | Text |

**Table `wida_2020_plds`** (optional, for assessment/goals): one set per grade cluster; columns e.g. grade_cluster, communication_mode, language_dimension, proficiency_level, descriptor_text.

**Use case:** For a Grade 3 Science lesson focused on Explaining (Speaking), query wida_2020_expectations with grade_cluster="2-3", standard=ELD-SC, key_language_use="Explain", mode="Expressive"; return only those rows to the LLM. **Pros:** Precise retrieval; easy to extend; drives APIs and context service. **Cons:** ETL and PDF-to-schema mapping effort.

### 4.2 Markdown (naming and content per framework)

**2020 ELD:** One file per (standard, grade cluster, key use, mode). **Naming:** `[Standard]_[GradeCluster]_[KeyUse]_[Mode].md` (e.g. `ELD-LA_2-3_Narrate_Expressive.md`). **Frontmatter:** standard, grade_cluster, key_use, mode. **Body:** Overarching Language Expectation statement; list of Language Functions; under each Function, associated Language Features (if applicable).

**Can Do Key Uses Edition:** One file per (grade cluster, key use, domain). **Naming:** `CanDo_[GradeCluster]_[KeyUse]_[Domain].md` (e.g. `CanDo_2-3_Explain_Speaking.md`). **Frontmatter:** grade_cluster, key_use, domain. **Body:** Six ELP level descriptors (Level 1 Entering … Level 6 Reaching; Level 2 = "Emerging") for that slice.

**Can Do Original Edition:** One file per (grade cluster, domain). **Naming:** `CanDo-Original_[GradeCluster]_[Domain].md` (e.g. `CanDo-Original_1-2_Writing.md`). **Frontmatter:** framework "Can Do Descriptors Original", grade_cluster, domain. **Body:** Bulleted descriptors for Levels 1–6 only (Level 2 = "Beginning"; strip all boilerplate—intro sentence, framework explanation, teacher prompts, NAMES column).

**Performance Definitions (Receptive):** One page; slice **by proficiency level** (six records). **DB schema:** `level` (int 1–6), `discourse_dimension`, `sentence_dimension`, `word_phrase_dimension` (text or array). **Markdown (optional):** one file per level, e.g. `Performance-Definitions-Receptive_Level2.md`. Strip: "Within sociocultural contexts for processing language…"; "At each grade, toward the end of a given level…"; footer "WIDA Performance Definitions - Listening and Reading Grades K–12". **Retrieval:** Use in addition to Can Do for Listening/Reading; do not use when planning with 2020 ELD (use 2020 PLDs instead). See [WIDA_ELD/README.md](../../reference_docs/WIDA_ELD/README.md) "Performance Definitions (Receptive) – ingestion and retrieval".

**WIDA Language Charts (2025):** 38 pages: Introduction/Tips; Charts by (grade cluster, mode); Definitions and Examples glossary. **One file per (grade_cluster, mode),** e.g. `LanguageChart_Grades2-3_Expressive.md`. **YAML:** framework "WIDA Language Charts 2025", grade_cluster, mode. **Body:** rows by proficiency_level (6…1), fields discourse, sentence, word_phrase. **End of Level 1:** section at end inverts layout (rows = grade clusters); parse separately, add Level 1 to each (grade_cluster, mode) file. **One global file** for Glossary. **Strip:** WIDA footer; repeating "As multilingual learners work toward…"; four "Planning Questions" at bottom of each chart. **Retrieval:** Use instead of older Performance Definitions when using 2020 ELD; in addition to 2020 Expectations and PLDs. For KLU-specific Discourse, use glossary "Discourse Dimension Definitions." See [WIDA_ELD/README.md](../../reference_docs/WIDA_ELD/README.md) "Language Charts (2025) – ingestion and retrieval".

**Use case:** Context service resolves the slot to the correct file path and injects the file into the prompt. Versionable in git. **Pros:** No DB dependency; agents resolve path from metadata. **Cons:** Many files; updates require re-running extraction.

### 4.3 Boilerplate (store once, reference by ID)

- **Standard 1:** Language Expectations are identical for K–3 and for 4–12; no Language Features. Store once, link by ID.
- **PLDs (2020):** One set per grade cluster (not per standard or Key Use). Store per grade cluster.
- **Key Language Use definitions:** Narrate, Inform, Explain, Argue definitions are consistent across grades and disciplines; store once.

### 4.4 Extraction pitfalls

- **2020 two-column layout:** Interpretive and Expressive are often side-by-side; extract by mode (Reference Code) so columns are not merged.
- **Null language_features:** Expressive-only; Standard 1 has none. Parser must accept null/empty without breaking.
- **Symbols (2020):** Functions = bullet (●), Features = square (■) nested under Functions; distinguish for correct parent-child.
- **Discuss (Can Do):** Single row "Oral Language", not four domain rows; table layout differs.
- **Page-spanning tables (Can Do):** Key Use label repeats on next page; merge rows, do not treat as new Key Use.
- **Annotated Language Samples:** Do not scrape as raw text; they rely on visual cues (color, underlines, arrows); text-only extraction is meaningless.
- **Footnotes (Can Do Key Uses):** Repeating footnote (e.g. "*Except for Level 6...") must not be appended to descriptor text.
- **Can Do Original boilerplate:** Strip introductory sentence, WIDA framework explanation, "Write in grade-level [Domain] expectations below:" prompts, and NAMES column; keep only the six level descriptor bullets.
- **Performance Definitions (Receptive) boilerplate:** Strip intro "Within sociocultural contexts for processing language…", repeating "At each grade, toward the end of a given level…", and footer "WIDA Performance Definitions - Listening and Reading Grades K–12".
- **Language Charts (2025):** Strip footer "WIDA is housed within the Wisconsin Center for Education Research…"; repeating header "As multilingual learners work toward the end of a proficiency level…"; four "Planning Questions for Instruction and Classroom Assessment" at bottom of every chart. **End of Level 1 section:** rows = grade clusters (not proficiency levels); parse separately and distribute Level 1 into each (grade_cluster, mode) file.

### 4.5 Embeddings / vector database (later, optional)

- **Use case:** If we later need semantic search (e.g. "find expectations about comparing and contrasting" without knowing the exact key use), we would chunk the extracted content, embed chunks, and store in a vector DB. Retrieval would be by similarity (and optionally filtered by metadata: grade cluster, standard).
- **Status:** Deferred per [REFERENCE_DOCS_AND_LESSON_PLAN_ACCESS.md](./REFERENCE_DOCS_AND_LESSON_PLAN_ACCESS.md). Plan the ingestion pipeline so that **if** we add embeddings later, the **source of truth for chunking** is the same structured content (database or Markdown) produced by this module. No duplicate extraction logic.

---

## 5. Recommended phasing

| Phase | What | Output |
|-------|------|--------|
| **1. Schema and manual/semi-automated content** | Define the canonical schema for ELD slices (grade_cluster, standard, key_use, expectations, functions, features) and for Can Do (cluster, domain, level, descriptor). Populate a first version by manual extraction or script-assisted export into Markdown or a seed database. | Markdown files per slice and/or seed DB. Document the schema in this repo. |
| **2. Extraction module (MVP)** | Implement a small software module (e.g. under `tools/` or `backend/`) that reads WIDA PDFs from `reference_docs/`, extracts text and structure using a PDF library, and maps to the schema. Output: Markdown and/or SQL/JSON for database load. Run on a schedule or on-demand when PDFs are updated. | Repeatable pipeline: PDF → structured content (MD and/or DB). |
| **3. Registry and context service integration** | CurriculumContextService (and document registry) consume the structured content: for a query profile (grade, subject, key use), resolve to the correct slice(s) and return only that content to the LLM. | Lesson plan generation uses WIDA as the "OS" via the context service. |
| **4. (Optional) Embeddings and vector DB** | If we decide to add semantic search, add a step that chunks the structured content (from DB or Markdown), generates embeddings, and loads a vector DB. Retrieval can then combine metadata filter (cluster, standard) with similarity search. | Same ingestion pipeline; additional output path to vector DB. |

---

## 6. Where the module lives and how it fits

- **Placement:** A dedicated **WIDA ingestion** (or "reference doc extraction") module is appropriate. It could live under `tools/wida_ingestion/` (scripts and extractors) and/or as a service under `backend/` if we want an API to trigger re-ingestion. For now, planning for **scripts under `tools/`** is enough; they can be run locally or in CI when reference docs change.
- **Single source of truth:** The **PDFs (and any official WIDA files)** in `reference_docs/` remain the authoritative source. The module produces **derived** content (DB, Markdown). If we later add embeddings, they are derived from the same structured content, not from a second extraction pass.
- **Document registry:** The registry (e.g. `curriculum_documents` or a WIDA-specific index) should point to either (a) the generated Markdown paths or (b) the database table/view that holds the slices. The context service queries the registry and then reads from files or DB accordingly.

---

## 7. Combining WIDA with curriculum documents (per subject and level)

Lesson plan generation for a given **slot** (grade, subject, level) should use **combined context** from two families:

| Source | Content | Keyed by |
|--------|---------|----------|
| **WIDA** | ELD standards slices (expectations, functions, features), Can Do descriptors, Key Language Uses | Grade cluster, standard (1–5), key use (Narrate, Argue, Inform, Explain), domain |
| **Curriculum documents** | Subject- and level-specific standards, scope, unit goals, or other district/school curriculum | Subject, grade/level, optional unit or topic |

For each lesson plan slot, the system assembles:

1. **WIDA content** for that slot’s grade cluster, subject-mapped standard (e.g. Math → Standard 3), and relevant key use(s) (and for assessment, Can Do by cluster and domain).
2. **Curriculum content** for that subject and level (e.g. “Grade 3 Math scope,” “ELA Unit 2 objectives”) when such documents are registered in the document registry.

The **query profile** for the slot (grade, subject, proficiency, lesson type, key use, etc.) drives both lookups. Combined, WIDA + curriculum give the LLM the “operating system” (WIDA) plus the subject/level-specific goals (curriculum) so the lesson plan aligns to both.

Curriculum documents may be stored in the same ways we use for WIDA: ingested into a **database** (with subject, grade_range, optional unit) or as **Markdown** in a structured path (e.g. `reference_docs/curriculum/math/grade_3.md`). The same retrieval contract—query profile in, document content out—applies; the context service (or an agent using skills/tools) fetches from both WIDA and curriculum stores and merges the result for the slot.

---

## 8. Prompts, agents, skills, and tools for slot-level access

To orient the LLM toward creating the **specific** lesson plan for a slot, we use:

- **Prompts (or prompt templates)** that frame the task: e.g. “You are generating a lesson plan for [grade], [subject], aligned to WIDA ELD Standard [N] and Key Language Use [X]. Use the following WIDA and curriculum context for this slot only.”
- **Agents** that orchestrate the flow: e.g. an agent responsible for “lesson plan generation” that (1) builds the query profile for the slot, (2) requests the combined context (WIDA + curriculum) for that slot, (3) invokes the LLM with the prompt and context, (4) post-processes or validates the output.

Those agents are accompanied by **skills and tools** that actually access the data:

- **Skills** (e.g. “lesson-plan-generation,” “retrieve-context”) encapsulate the logic and call the right tools. See [AGENT_SKILLS_AND_CODE_EXECUTION.md](./AGENT_SKILLS_AND_CODE_EXECUTION.md).
- **Tools** provide slot-level access to the databases or Markdown documents:
  - **Database:** A tool (e.g. “get_wida_slice” or “get_curriculum_for_slot”) that takes (grade_cluster, standard, key_use) or (subject, grade) and returns the corresponding rows or JSON from the ingested WIDA/curriculum tables.
  - **Markdown:** A tool (e.g. “read_reference_doc”) that takes a resolved path (e.g. from a registry or from a path convention like `reference_docs/WIDA_ELD/eld/2-3_LA_Inform.md`) and returns the file contents for that slot.

So for **each lesson plan slot**, the agent uses skills that call tools to:

1. **Resolve** the slot’s query profile to the right slice identifiers (grade cluster, standard, key use; subject; level).
2. **Fetch** WIDA content (from DB or Markdown) for that slice.
3. **Fetch** curriculum content (from DB or Markdown) for that subject and level, when available.
4. **Combine** both into a single context payload and pass it (with the orienting prompt) to the LLM.

The LLM then creates the lesson plan with a clear, slot-specific orientation and without loading unrelated grades, subjects, or key uses. Prompts and agents ensure the model knows it is producing one slot’s plan; skills and tools ensure the model only receives the WIDA and curriculum content that applies to that slot.

---

## 9. Checklist (planning)

- [ ] Define canonical schema: `wida_2020_expectations` (reference_code PK, grade_cluster, standard, key_language_use, mode, expectation_text, language_functions, language_features), `wida_can_do_descriptors` (grade_cluster, key_use, domain, level_1_entering … level_6_reaching), `wida_2020_plds` (per grade cluster). Map UI domains to Interpretive/Expressive when querying 2020. See 4.4 for extraction pitfalls.
- [ ] Decide first output format: Markdown only, database only, or both (Markdown for git and agents, DB for context service).
- [ ] Create initial structured content (manual or script-assisted) for at least one grade cluster and one standard/key use to validate the schema and retrieval flow.
- [ ] Design and implement the extraction module (PDF → structure → Markdown and/or DB); document how to run it and how often (e.g. when WIDA docs are updated).
- [ ] Wire CurriculumContextService to use the structured WIDA content (by slice) when building context for lesson plan generation.
- [ ] (Later) If embeddings/vector DB are adopted, add a pipeline step from structured content to chunks and vector DB without re-extracting from PDF.

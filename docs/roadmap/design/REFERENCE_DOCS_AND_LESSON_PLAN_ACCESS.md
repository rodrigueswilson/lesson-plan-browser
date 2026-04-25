# Reference Documentation and Lesson Plan Access Plan

**Status:** Planning (Phase 1 Document Context)  
**Goal:** Define how reference documentation is scoped, made accessible, kept intelligible to humans and to LLMs/agents/skills, and how it is used when creating new lesson plans. This doc also records the decision on embeddings and vector databases.

**Related:** [PHASE1_CURRICULUM_DOCUMENT_INVENTORY.md](./PHASE1_CURRICULUM_DOCUMENT_INVENTORY.md), [ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md](./ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md), [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md), [WIDA_FRAMEWORK_INGESTION_AND_USE.md](./WIDA_FRAMEWORK_INGESTION_AND_USE.md) (extraction pipeline and use of WIDA as "operating system"), [LESSON_PLANNING_BALANCE.md](./LESSON_PLANNING_BALANCE.md) (balance of domains and Key Language Uses across weekly, unit, period, year).

---

## 1. Scope: What Counts as Reference Documentation

Reference docs are the **curriculum context** used when generating or refining lesson plans:

| Category | Location | Content | Used for |
|----------|----------|---------|----------|
| **Strategies** | `strategies_pack_v2/` | 33 bilingual strategies (6 categories), indexed by grade cluster, lesson type, proficiency | Strategy selection per slot |
| **WIDA** | `wida/` | Framework reference, strategy enhancements by grade/proficiency | WIDA-aligned scaffolding |
| **Co-teaching** | `co_teaching/` | 6 Friend & Cook models, phase patterns, Portuguese misconceptions, selection rules | Delivery mode and linguistic support |
| **Curriculum (future)** | User-registered | Standards, scope, unit docs per grade/subject | Optional enrichment when registered in document registry |
| **WIDA (one important source)** | In repo | Multiple documents under [reference_docs/](../../reference_docs/) and [reference_docs/WIDA_ELD/](../../reference_docs/WIDA_ELD/). Full catalog: [WIDA_ELD/README.md](../../reference_docs/WIDA_ELD/README.md). | Can Do (goals, objectives, assessment); ELD Standards 2020 (one PDF per grade cluster); Language Charts (modes/dimensions); Standards FAQ (conceptual). For one slot, retrieve only the matching grade cluster and domain(s). |

Pedagogical support (strategies, WIDA, co-teaching) is already in-repo and structured. The WIDA Can Do Descriptors PDF is a key reference for the planned Assessment module and should be registered once the document system supports PDF or an extracted/structured version. Content curriculum (e.g. "Grade 3 Math standards") is optional and would be registered in the `curriculum_documents` registry with `subject` + `grade_range` when added.

### 1.1 Primary source: the teacher's lesson plans

**One main source of information will always be the primary teacher's lesson plans.** They are always important because they **decide what will be taught on each day of the week and on each lesson.** The teacher's plan determines the **lesson number according to the curriculum** (i.e. where this lesson sits in the unit or course sequence) and thus drives scope and sequence at the day/slot level. That plan is then **enriched by the curriculum** (and by WIDA, strategies, co-teaching): reference documentation adds standards, language expectations, and scaffolding but does not override what the teacher has chosen to teach or when. When we generate or enhance a lesson plan, the teacher's input (e.g. uploaded DOCX, slot metadata, objectives, lesson number) is the authority for *what* is taught and *when*; reference docs supply the *how* (alignment, expectations, strategies). The document inventory and retrieval design should keep this hierarchy explicit: teacher plan first (what/when), reference context second (enrichment).

### 1.2 Ongoing document insertion and analysis

We will **keep inserting and analyzing new documents** over time. As new items are added (e.g. additional WIDA materials, curriculum by subject/level, assessment guides), we will:

- **Analyze how they relate to each other** (e.g. which docs apply to the same grade cluster or subject; how Can Do maps to ELD Standards; how curriculum docs map to WIDA standards).
- **Document how they are structured** (grade clusters, domains, key uses, sections) so that retrieval and ingestion stay consistent.
- **Update the document inventory and catalogs** (e.g. [PHASE1_CURRICULUM_DOCUMENT_INVENTORY.md](./PHASE1_CURRICULUM_DOCUMENT_INVENTORY.md), [reference_docs/WIDA_ELD/README.md](../../reference_docs/WIDA_ELD/README.md)) so that relationships and structure remain visible and the context service (or agents/tools) can resolve the right slice for each lesson plan slot.

The reference-doc set is therefore **living**: new documents are added, analyzed for structure and relationships, and then integrated into the retrieval path. The primary teacher's lesson plans remain the constant main source that these documents support.

---

## 2. How Documentation Will Be Accessible

### 2.1 Human access

- **Existing:** Markdown and JSON in repo; README and [Documentation Policy](../DOCUMENTATION_POLICY.md) point to [Reference](https://github.com/README#reference) (Strategy Dictionary, Co-Teaching, WIDA, Examples).
- **Planned:** Keep reference docs as the single source of truth in `strategies_pack_v2/`, `wida/`, `co_teaching/`. No separate “human-only” copy. Humans read the same files (and any generated indexes) via repo browse, local editors, or a future lightweight index page if needed.

### 2.2 Programmatic access (during lesson plan creation)

- **Mechanism:** Metadata-driven lookup, not semantic search. A **CurriculumContextService** (Phase 2) selects documents by (grade, subject, proficiency, lesson type, delivery mode), reads the matching local files, and returns their content.
- **API surface:** Exposed to the generation flow (and later to Agent Skills / MCP) as a single operation: **retrieve context** given a **query profile**. No direct file paths in prompts; the service is the single entry point.
- **Storage:** A **document registry** (e.g. `curriculum_documents` table or equivalent index) stores metadata (document_type, grade_range, subject, category, etc.) and file paths. It is populated from the existing directories by an indexing script (Phase 2). The registry is the authority for “what exists” and “how to find it.”

---

## 3. Intelligibility to Humans and to LLMs/Agents/Skills

### 3.1 Humans

- **Format:** Existing JSON is structured (strategies, WIDA, co-teaching). Keys and values use clear, consistent names (e.g. `grade_cluster`, `lesson_type`, `core_principle`). Optional: one-page “reference index” (markdown or generated) that lists documents and their dimensions.
- **Discoverability:** Document inventory (Phase 1) and registry metadata make it clear which docs apply to which grade/subject/use case.

### 3.2 LLMs, agents, and skills

- **Contract:** The system does not send raw “search the repo” instructions. It sends **already-selected document content** (full or filtered) in the prompt. Selection is done by CurriculumContextService using the query profile.
- **Structure:** JSON is passed as-is (or as a stable, versioned subset) so that models see consistent fields (e.g. `strategy_name`, `core_principle`, `wida_band`, `misconception_pattern`). No ad-hoc formats.
- **Agent/Skill contract:** Skills (e.g. lesson-plan-generation, weekly-architect) call one well-defined operation: “retrieve curriculum context for this query profile.” Input: query profile. Output: document list + content + selection reasoning. This keeps agents/skills independent of file layout and indexing details.
- **Documentation for agents:** A short, machine-readable spec (e.g. in `docs/roadmap/design/` or openapi fragment) should describe: (1) query profile schema, (2) response shape (documents, token estimate, selection_reasoning), (3) which document types exist and what dimensions they use. This makes it easy for future MCP tools or skills to consume the same contract.

---

## 4. How This Information Is Accessed While Creating New Lesson Plans

1. **Input:** User uploads a lesson plan (e.g. DOCX) or triggers generation for a slot/week. The system has or infers: grade, subject, proficiency levels, lesson type, delivery mode, optional unit topic.
2. **Query profile:** The pipeline builds a **query profile** (see ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md) from that metadata.
3. **Retrieval:** CurriculumContextService.**retrieve_context**(query_profile) runs:
   - Query the document registry (and strategy index) by grade cluster, subject, lesson type, proficiency, delivery mode.
   - Resolve to a list of files (and, for strategies, in-file filters).
   - Read those files and optionally filter (e.g. strategies by grade_cluster and proficiency).
   - Return a single response: list of document contents, token estimate, selection reasoning.
4. **Generation:** The LLM (Claude) receives the primary plan content **plus** the retrieved document content in its context. No chunking or embedding lookup at request time; selection is deterministic from metadata.
5. **Logging (planned):** Log which documents were selected and why (e.g. in a `context_retrievals` or equivalent table) for auditing and debugging.

So “how it’s accessed” is: **only through the context service**, using a **query profile**, returning **full document content** (or filtered slices) for the current lesson context.

---

## 5. Embeddings and Vector Databases: Decision Accepted via JSON ETL

**Decision: We will implement a structured RAG approach utilizing an ETL pipeline to convert curriculum documents to JSON, stored in a local JSON cache or Vector Database (like Qdrant) depending on scale.**

- **Rationale:** The raw Markdown documents lack the token efficiency and component-level detail required for advanced Agent Skills and MCP tool integration. Feeding entire unit outlines wastes context and degrades result accuracy.
- **Future approach:** An ETL pipeline will parse the downloaded curriculum documentation into strict JSON schemas (e.g., separating "Do Now", "Guided Practice", "Exit Ticket" logically). 
- **Structure over Semantic RAG:** Instead of standard "fuzzy" embeddings, the Vector DB (or indexed JSON document store) will utilize heavy metadata pre-filtering (e.g. `filter: grade=3, unit=5, lesson=2`). This eliminates cross-grade hallucinations while allowing specific retrieval for tools like `get_lesson_component()`.
- **Reference:** For details on this architectural shift, see: [CURRICULUM_JSON_DATABASE_ETL.md](./CURRICULUM_JSON_DATABASE_ETL.md).

---

## 6. Summary Table

| Question | Answer for Phase 1–2 |
|----------|----------------------|
| **What documentation?** | Strategies, WIDA, co-teaching (in-repo); optional user curriculum/assessment docs in registry. |
| **How accessible to humans?** | Same files in repo; optional index page; doc inventory and registry metadata. |
| **How accessible to LLMs/agents/skills?** | Only via CurriculumContextService: query profile in → document content + reasoning out. |
| **Intelligible how?** | Stable JSON structure; single “retrieve context” contract; optional machine-readable spec for agents. |
| **Accessed when creating lesson plans?** | Pipeline builds query profile → service retrieves context → content injected into LLM context. |
| **Embeddings / vector DB?** | **Accepted.** We will use an ETL process to convert scrape Markdown into strict JSON schemas, allowing Vector Databases like Qdrant to power structured RAG with strict metadata filtering. |
| **How “queried”?** | Today: by (grade, subject, proficiency, lesson type, delivery mode) against registry and strategy index; then file read. Future: to be revisited if we add embeddings/vector DB. |

---

## 7. Checklist for Implementation

- [ ] **Phase 1:** Complete document inventory and grade/subject mapping (PHASE1_CURRICULUM_DOCUMENT_INVENTORY.md); fix grade cluster convention; document subject → lesson_type mapping; design retrieval logging.
- [ ] **Phase 2:** Implement CurriculumContextService and document registry/indexing; wire retrieve_context into batch processor; (optional) add a one-page human-facing index and a short agent-facing spec for the retrieve-context contract.
- [ ] **Later:** Once we have a clearer picture of what information is consulted during lesson plan creation, decide whether embeddings/vector DB or managed RAG is needed; if so, design and document without breaking the existing “retrieve context” contract for consumers.

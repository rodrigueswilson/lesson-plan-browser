# Curriculum JSON Database & ETL Strategy

**Status:** Planned
**Goal:** Convert raw, scraped curriculum Markdown files into a highly structured JSON database. This document serves as the architectural strategy for how to structure the data, why it benefits AI agents, and how it integrates with vector databases (like Qdrant) and the local MCP server.

**Related:** [REFERENCE_DOCS_AND_LESSON_PLAN_ACCESS.md](./REFERENCE_DOCS_AND_LESSON_PLAN_ACCESS.md), [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md)

---

## 1. The Core Problem
The curriculum scraper successfully downloads Google Docs, PDFs, and slide decks, converting them into hierarchical Markdown `(Unit -> Lesson -> Resources)`. While this is excellent for human readability and base-level context, raw Markdown presents challenges for AI Agents:
- **Token Inefficiency:** Feeding a 4-page Markdown document to an LLM just to find the "Exit Ticket" wastes context window space and costs.
- **Retrieval Inaccuracy:** Semantic search over raw narrative text can sometimes return overlapping or subtly incorrect lessons (e.g., retrieving Grade 2 Unit 3 instead of Grade 3 Unit 3).
- **Component Modification:** Agents struggle to confidently rewrite *just* the "Guided Practice" section of a flat text file without inadvertently altering surrounding formatting.

## 2. The Solution: Incremental & Heterogeneous JSON Database
We will implement an **Incremental ETL (Extract, Transform, Load)** pipeline. Unlike a rigid SQL database, this system will use a **Schema-Flexible JSON collection** that can adapt as we discover new patterns in different grades and subjects.

### Key Data Principles
- **Incremental Growth**: New documents can be scraped and converted to JSON independently. The database grows as new "Unit folders" are processed, without requiring a full system re-index.
- **Heterogeneous Schemas**: We recognize that Grade 1 Math and Grade 3 ELA have different instructional needs. The JSON structure is allowed to vary:
    - *ELA* might include: `text_dependent_questions`, `vocabulary_focus`, `reading_log`.
    - *Math* might include: `manipulatives_needed`, `practice_problems`, `conceptual_understanding_checks`.
- **Adaptability**: If a new curriculum version introduces a unique field (e.g., "Social-Emotional Learning Integration"), the JSON can accommodate it immediately without a schema migration.
- **Curriculum Lifecycle & Versioning**: The database must support school-year transitions:
    - **Versioning**: Tagging units with a `school_year` (e.g., "2024-2025").
    - **Replacement**: Ability to "Archive" or "Delete" an old unit and replace it with a newly scraped version if the Board of Education updates the curriculum.
    - **Conflict Resolution**: Logic to handle cases where a teacher's old lesson plan points to a deleted curriculum unit (e.g., "This reference is deprecated, view the 2025 version instead").

### Example Flexible Schema (Lesson Plan)
```json
{
  "grade_level": 3,
  "unit": 5,
  "lesson_number": 2,
  "lesson_title": "Poetry Analysis",
  "standards": ["RL.3.1", "RL.3.4"],
  "objective": "Students will determine the meaning of words and phrases as they are used in a text.",
  "components": {
    "do_now": "Read the short poem on the board and circle rhyming words.",
    "direct_instruction": "Teacher models identifying stanzas...",
    "guided_practice": "Students work in pairs to annotate...",
    "independent_practice": "Students choose a poem and answer text-dependent questions.",
    "exit_ticket": "Write two lines of poetry that rhyme and follow the pattern."
  }
}
```

---

## 3. Advantages Acquired via JSON Structure

### A. AI Agents & Skills
- **Pinpoint Accuracy:** Agents can query exactly what they need. A skill can request `get_lesson_component(grade=3, unit=5, lesson=2, component="exit_ticket")` rather than reading the whole file.
- **Dynamic Swapping:** If a teacher requests to "make the independent practice more interactive," an agent only needs to rewrite the `components.independent_practice` JSON node, ensuring the rest of the lesson structure is flawlessly preserved.
- **Predictable Formatting:** Strict JSON output guarantees that UI components and generators never break due to stray markdown characters.

### B. Physical Technology Stack

To ensure **Local-First / Private** operation on a teacher's workstation, we will use a **Unified Local Hybrid Store**:

- **Primary Engine**: **LanceDB** (Embedded Vector & Metadata Store).
    - *Why*: It is serverless, runs locally on Windows, handles millions of vectors with sub-millisecond latency, and allows us to store **full JSON metadata** alongside embeddings in a single table.
- **Relational Backup**: **libSQL / SQLite**.
    - *Why*: For strict relational lookups and session state that doesn't require semantic search.
- **Data Format**: **Apache Arrow**.
    - *Why*: LanceDB uses Arrow for ultra-efficient on-disk storage, perfect for "Lesson Packages" that include media and text.

### C. Hybrid Retrieval System (JSON + Vector DB)
We will implement a **Hybrid Retrieval Architecture** to provide agents with both precision and semantic depth:
- **Structured JSON Queries**: Used for exact matches (e.g., "Find Lesson 3 in Unit 5"). This is perfect for identifying specific standards and required materials.
- **Vector Search (Embeddings)**: Used for semantic discovery (e.g., "Find all lessons across the building that introduce the concept of 'Regrouping' or 'Borrowing'").
- **Categorized Organization (Metadata Payload)**: Each vector stored in the database is tagged with a **Metadata Payload** mirroring the JSON structure:
    - `{ "grade": "3", "subject": "Math", "unit": "4", "lesson": "2", "school_year": "2024-2025" }`
    - This allows for **Strict Filtering**: An agent can semantic-search for "multiplication games" while pre-filtering specifically for `grade == 3`.
- **Vocabulary Reasoning**: This hybrid approach is critical for solving vocabulary-related challenges. Agents can:
    - Search the Vector DB for "synonyms or related concepts" in the curriculum.
    - Query the JSON DB for the *exact definition* or *sentence frame* used in a specific grade's glossary.
    - Cross-reference across subjects (e.g., "How is the term 'Mass' defined in 6th grade Science vs. Math?").

### C. Automated Index Mirroring & Consistency
To prevent the AI from retrieving stale or deleted information, we will implement an **Automated Mirroring Service**:
- **JSON as SSOT**: The JSON database (and the local file system) is the Single Source of Truth.
- **Synchronized Lifecycle**: Whenever a Unit is replaced, updated, or deleted in the JSON database:
    - The mirroring service identifies the affected `unit_id`.
    - It performs an **Atomic Invalidation** in the Vector DB (deleting all vectors associated with that specific unit).
    - It re-embends the updated JSON content and populates the Vector DB with fresh data.
- **Transactional Integrity**: The "Replace" operation is transactional—if the re-indexing fails, the old vectors are retained (or the system marks the unit as "Indexing Pending") to maintain a reliable search state.

### D. The MCP (Model Context Protocol) Server
The MCP server thrives on structured data. Exposing the curriculum as JSON means:
- We can define precise MCP tools like `query_curriculum_database` (JSON) and `search_curriculum_semantics` (Vector).
- Claude Desktop or other MCP-compatible clients can traverse the curriculum programmatically.
- External agents can instantly map our JSON structure to their internal logic to design multi-week schedules autonomously.

---

## 4. Implementation Phasing
1. **Define the Pydantic/JSON Schemas:** Establish the strict schema for Lesson Plans, Rubrics, and Slide Decks based on the newly downloaded Grade 2 and Grade 3 materials.
2. **Build the Extraction Tool:** Create a Python script that reads `reference_docs/scraped/`, chunks the markdown by headers, and populates the schema.
3. **Database Initialization:** Spin up a local document store (like TinyDB) or a Vector Database (like Qdrant) to hold the extracted JSON objects.
4. **Agent Integration:** Update the `CurriculumContextService` to query this JSON database directly instead of (or in addition to) reading flat Markdown files.

---

## Procedure segments (SQL + JSON)

HTML in `lessons.procedure_html` remains the render cache. The next structured field for agents is **`procedure_structured`** (or equivalent), derived from the same subheader anchors as the explorer UI splitter—see [LESSON_PROCEDURE_SEGMENTS_SCHEMA.md](./LESSON_PROCEDURE_SEGMENTS_SCHEMA.md).

---

## Downstream dependency order (long horizon)

Work that assumes **trustworthy structured curriculum** (not re-parsed HTML) should land **after**:

1. Stable **`standards_structured`** ingestion and validation (see [CURRICULUM_EXTRACTION_ARCHITECTURE.md](../../scrapers/CURRICULUM_EXTRACTION_ARCHITECTURE.md)).
2. Optional **`procedure_structured`** (or segment table) populated from the same parser signals.

Then sequence: **document context + vocabulary module** ([ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md](./ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md)), **WIDA ingestion** ([WIDA_FRAMEWORK_INGESTION_AND_USE.md](./WIDA_FRAMEWORK_INGESTION_AND_USE.md)), **lesson plan editor**, **cmi5 / worksheet** packages—so downstream modules consume JSON SSOT instead of scraping HTML.

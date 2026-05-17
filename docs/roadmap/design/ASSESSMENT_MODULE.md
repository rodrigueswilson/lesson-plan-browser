# Assessment Module (Planned)

**Status:** Planning  
**Goal:** Define a module that ties lesson plan generation to assessment design and in-class data collection, aligned with WIDA Can Do Descriptors and the ODPAR cycle (Observe, Document, Plan, Act, Reflect).

**Related:** [REFERENCE_DOCS_AND_LESSON_PLAN_ACCESS.md](./REFERENCE_DOCS_AND_LESSON_PLAN_ACCESS.md), [PHASE1_CURRICULUM_DOCUMENT_INVENTORY.md](./PHASE1_CURRICULUM_DOCUMENT_INVENTORY.md), [ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md](./ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md).

---

## 1. Purpose

The Assessment module ensures that when the LLM creates a lesson plan, it also decides:

- **How that lesson plan will be assessed** (what evidence of learning we look for).
- **How the student will be assessed during delivery** (what the teacher observes and records in the classroom).

The module provides a **set of assessment tools** (e.g. checklist, tally record, others to be added). For each lesson, the LLM selects **one, two, or three** tools that are specifically used for that lesson. Tools are aligned with lesson objectives (e.g. if the objective is about Writing, the assessment is about Writing, and the chosen tool is appropriate and available).

Assessment data is collected by the teacher **during the lesson**, using tools available on the **tablet** in the classroom. The module supports the ODPAR cycle by linking **assessment** (Observe, Document) to **planning** (Plan, Act, Reflect) so that what is assessed informs the next planning steps.

---

## 2. Reference Document: WIDA Can Do Descriptors

A key reference for this module is the **WIDA Can Do Descriptors (Original, Student Name Charts)**. This document:

- Informs **student goals** and **ELD (English Language Development) objectives** in the lesson plan.
- Informs the **assessment section** of the lesson plan (what we expect students to “can do” and how we measure it).
- Provides **Can Do descriptors** that guide the ODPAR cycle: assessment and planning are driven by what we observe and document, so that the next plan and act phases are informed by that information.

### 2.1 Structure of the Original Edition (verified from WIDA)

The **Original Edition** is organized by:

- **Grade level clusters:** PreK-K, **1-2**, **3-5**, 6-8, 9-12. (So grades 1 and 2 are together; grades 3, 4, and 5 are together; etc.)
- **Four language domains:** **Listening**, **Reading**, **Speaking**, **Writing.** Each cluster has descriptors for all four domains.

So the document is effectively structured in **parts** by (grade_cluster, domain). Within each part, descriptors are typically organized by proficiency level (e.g. WIDA levels 1-6).

### 2.2 Document in parts: retrieve only what the slot needs

When the app is **planning or assessing one slot**, it should **retrieve only the relevant part(s)** of the Can Do Descriptors:

- **By grade:** Map the slot's grade to the correct cluster (e.g. grade 3 to cluster **3-5**; grade 1 to cluster **1-2**).
- **By domain:** If the slot (or the chosen assessment) targets a specific language domain (e.g. Writing), retrieve only the **Writing** descriptors for that grade cluster. If the slot spans more than one domain, retrieve the parts for each domain involved (e.g. Reading + Writing).

This keeps context small and precise: the LLM receives only the Can Do content for the grade cluster and domain(s) of the lesson being planned or assessed, not the entire PreK-12 document.

### 2.3 Registration and implementation

**Document (to be registered in the document system):**

| Field | Value |
|-------|--------|
| **Name** | WIDA Can Do Descriptors – Original, Student Name Charts |
| **Format** | PDF |
| **Source / location** | To be placed in the project’s reference doc store or registered path (e.g. under a `reference_docs/WIDA_ELD/` or equivalent). Current source example: `reference_docs/WIDA_ELD/CanDo-Descriptors-Original-Student-Name-Charts (1).pdf`. |
| **document_type** | `assessment` (or `wida_assessment`) |
| **Use in generation** | Student goals, ELD objectives, assessment section; Can Do–aligned descriptors for ODPAR. |
| **Grade dimension** | PreK-K, 1-2, 3-5, 6-8, 9-12 |
| **Domain dimension** | Listening, Reading, Speaking, Writing |

Implementation options: (1) Pre-extract one file/section per (grade_cluster, domain) and register as retrievable parts; or (2) Store the PDF and at retrieval time return only the section(s) matching the slot's grade cluster and domain(s). Registry or index must support lookup by `grade_cluster` and `domain`.

Once the document context service and registry support PDF (or an extracted/structured version), this document should be registered and included in the context retrieved when generating lesson plans so the LLM can use Can Do descriptors for goals, objectives, and assessment design.

### 2.4 Grade clusters (confirmed)

The Can Do Descriptors are organized in exactly five grade level clusters:

| Cluster label | Covers |
|---------------|--------|
| Can Do Descriptors: Grade Level Cluster PreK-K | PreK, K |
| Can Do Descriptors: Grade Level Cluster 1-2 | Grade 1, Grade 2 |
| Can Do Descriptors: Grade Level Cluster 3-5 | Grades 3, 4, 5 |
| Can Do Descriptors: Grade Level Cluster 6-8 | Grades 6, 7, 8 |
| Can Do Descriptors: Grade Level Cluster 9-12 | Grades 9-12 |

When the LLM is planning a class for a given grade (e.g. second grade), **only the cluster for that grade is needed** (e.g. 1-2). All other clusters are unnecessary and should not be loaded into the LLM context.

### 2.5 Storage and retrieval format: PDF vs database vs Markdown

We need to decide in which format to keep Can Do content so that (1) only the relevant cluster (and domain) is retrieved for the grade being planned, (2) agents and skills can query it efficiently, and (3) the LLM context window is used well (minimal, relevant content only).

| Option | Pros | Cons | Context efficiency |
|--------|------|------|--------------------|
| **PDF** (one file or one per cluster) | Matches original WIDA source; easy to archive. | Hard to query by (cluster, domain) without prior extraction; sending full PDF or large chunks wastes context. | Poor unless we add a separate extraction/index step and only send extracted text. |
| **Database** | Query by `grade_cluster`, `domain`, and optionally proficiency level; return only the exact rows needed; small, precise payload to LLM; agents/skills call an API (e.g. "cluster=1-2, domain=Writing") and get JSON or text. | Requires ETL from PDF to populate; DB to maintain when WIDA updates. | Best: only the requested descriptors are returned. |
| **Markdown** | Human-readable; versionable in git; no DB. One file per (cluster, domain), e.g. `can_do_1-2_writing.md`, so the context service reads that file and returns it. Agents/skills resolve path from (cluster, domain) and read the file. | One-time work to convert PDF into structured .md files (e.g. 5 clusters x 4 domains = 20 files); files to maintain on WIDA updates. | Best: only the requested file(s) are loaded and sent to the LLM. |

**Recommendation (to be confirmed):**

- **Do not** send the full PDF (or full PreK-12 content) to the LLM. Always retrieve **only** the content for the slot's grade cluster and domain(s).
- **Preferred retrieval format for the LLM:** Plain text or structured text (e.g. JSON or Markdown) containing only the descriptors for the requested (grade_cluster, domain). So the **storage** format should support precise retrieval; the **delivery** to the LLM is always minimal.
- **Storage format choice:**
  - **Markdown** is a good fit if we want simplicity, no database, and git-trackable content. One file per (cluster, domain), e.g. under `reference_docs/WIDA_ELD/can_do/` with names like `PreK-K_listening.md`, `1-2_writing.md`, etc. The context service (or an MCP tool) then maps (grade_cluster, domain) to file path and returns the file contents. Agents and skills can use the same path convention.
  - **Database** is a good fit if we need structured fields (e.g. proficiency level, descriptor text) and richer queries (e.g. "all Level 3 descriptors for 1-2 Writing"). Same retrieval contract: API returns only the requested slice.
- **Keep the authoritative PDF** in the repo (or doc store) for reference and for re-extraction if we change the structured format later.

**Decision:** To be made: adopt **Markdown** (one file per cluster+domain) for simplicity and agent-friendly paths, or **database** for structured querying. Both satisfy "only the relevant cluster (and domain) for this grade" and efficient use of the LLM context window.

---

## 3. ODPAR Cycle and the Assessment Module

ODPAR frames how assessment and planning work together:

| Phase | Role in assessment module |
|-------|---------------------------|
| **1. Observe** | Teacher observes students during the lesson; assessment tools on the tablet support structured observation. |
| **2. Document** | Teacher records what was observed (e.g. checklist, tally); data is stored and linked to the lesson/slot. |
| **3. Plan** | Lesson plan generation (and future “next steps”) uses assessment context; LLM designs how the lesson will be assessed and which tools to use. |
| **4. Act** | Lesson is delivered; teacher uses the selected tools to collect assessment data. |
| **5. Reflect** | Assessed information feeds back into planning (e.g. next lesson, next cycle). |

The Assessment module connects **Plan** (LLM decides assessment approach and tools) with **Observe/Document** (teacher collects data on the tablet) and **Reflect** (data available for future planning). This document focuses on the **Plan** and **Act** sides (what the LLM generates and what tools the teacher has); data flow for Reflect will be refined as the module is detailed.

---

## 4. How the Assessment Module Works (High Level)

3. **Physical Assessment Loop (FastScan)**
    - Worksheets are printed with **Dual-Metadata QR Codes** (identifying the Student, Lesson, and Assessment item).
    - Teachers use a high-speed scanner (e.g., **Epson FastScan**) to batch-process completed worksheets.
    - An AI-powered "Extraction Agent" reads the QR codes and handles the digital archival of the work.

4. **Unified Learner Timeline (Analytics Sync)**
    - The module merges **Digital Evidence** (xAPI statements from cmi5 packages) and **Physical Evidence** (Scanned worksheet scores) into one view.
    - This allows the teacher to see a holistic picture of student mastery (e.g., "Student A showed mastery on the digital quiz but struggled with the paper-pencil writing task").

5. **Alignment**
   - Objectives and assessment are aligned (e.g. Writing objective → writing assessment).  
   - Tools are aligned with the lesson (e.g. no “writing” tool for a listening-only lesson unless intended).  
   - The LLM’s choices are constrained to the **registered** tool set so that whatever it selects is actually available in the UI.

---

## 5. Legal, Ethical, and Privacy Requirements

The Assessment module is the **first part of the app** that will use **grade**, **classroom**, and **student identity** (name, pseudonym, or an encrypted/opaque identifier). This creates legal and ethical obligations that must be designed in from the start.

### 5.1 Compliance

The module **must** comply with:

- **FERPA (Family Educational Rights and Privacy Act)** – US federal law governing access to and disclosure of student education records.
- **Federal student privacy laws** – Any other applicable US federal requirements for K–12 student data.
- **State student privacy laws** – Applicable state laws in the jurisdictions where the app is used (e.g. state-specific student data privacy acts).

Design and implementation must be reviewed against these (and any district policies) before handling real student data. Legal review is recommended when the data model and data flows are finalized.

### 5.2 Anonymization and Encryption

- **Anonymize as much as possible:** Prefer pseudonyms or stable opaque codes (e.g. `student_id` as a UUID or locally generated code) instead of student names in storage and in any data exchange. Where the teacher needs to see a name on the tablet (e.g. to record who was observed), that information must be stored and transmitted under strict controls (see below).
- **Encrypt student-identifying data at rest:** Any field that can identify a student (name, or the mapping code → name) must be encrypted at rest. Keys must be controlled by the school/teacher, not sent to third parties.
- **Stable anonymized code:** Use a single, consistent anonymized identifier per student (e.g. per class roster) so that computation and analytics can track “student A” across lessons without ever using a real name in logs, exports, or APIs.

### 5.3 No Student Names on the Internet

- **No contact of student names with the internet:** Student names (and any data that directly identifies a student) must **never** be sent over the network to external services (e.g. cloud, LLM APIs, third-party analytics).
- **Preferred transfer path for assessment data:** Where assessment data is moved from the tablet (classroom) to the teacher’s computer (e.g. at home), prefer **local transfer only** – e.g. **USB cable** or local file copy – so that data does not traverse the internet. If any sync over the network is introduced later, it must transfer only **anonymized** assessment data (e.g. checklist results keyed by opaque `student_id`, no names), with name–code mapping remaining strictly on-device or on a single, controlled machine.

### 5.4 LLM and External Systems: No PII

- **The LLM must never receive student-identifying information.** Lesson plan generation, tool selection, and any future “Reflect” or planning features must not be given student names, real IDs, or any PII. If aggregated or exemplar data is ever sent to an LLM (e.g. “three students met the objective”), it must be in anonymized form only (e.g. “student A, B, C” or counts only).
- **All computation on assessment data** that could leave the device (e.g. reports, analytics, exports) must use **anonymized data and stable codes** only. No pipeline (LLM, cloud, or third party) may receive data that could identify a student.

### 5.5 Summary of Constraints

| Requirement | Implementation direction |
|-------------|--------------------------|
| FERPA / federal / state | Design and review for compliance; no PII to third parties; secure, minimal storage of identifiers. |
| Anonymize | Prefer pseudonym or opaque `student_id`; names only where strictly needed for teacher UI, encrypted at rest. |
| No names on internet | No student names (or name–code mapping) sent over the network; prefer USB/local transfer for assessment data tablet ↔ computer. |
| LLM never sees PII | Only anonymized aggregates or codes in any input to the LLM; no student names or identifying fields. |
| Computation always anonymized | Reports, analytics, exports use anonymized data and stable codes only. |

These requirements are part of the Assessment module plan and must be reflected in the data model, tablet ↔ computer transfer design, and any future sync or cloud options.

---

## 6. Scope of This Design (What We Plan Now)

- **Document the module** in the roadmap (this file) so the Assessment module is a recognized planned feature.
- **Register the WIDA Can Do Descriptors** in the document inventory and reference-doc plan as a key reference for goals, ELD objectives, and assessment; once the document system supports it, include it in context for lesson plan generation.
- **Plan gradually:** Since there is no existing “Assessment module” document in the documentation system, this design doc serves as the first place to plan it. As we implement:
  - Define the **tool set** (checklist, tally record, plus future tools) and their schema.
  - Define how the **LLM selects** 1–3 tools per lesson (prompt, schema, constraints).
  - Define **tablet UI** for each tool (data entry, storage, link to lesson/slot).
  - Define **data model** for assessment records (e.g. per lesson/slot/student or group) and how they feed into Reflect/planning.

No implementation is implied in this document; it establishes the concept, the link to the Can Do reference and ODPAR, the legal/ethical/privacy constraints above, and reserves the Assessment module on the roadmap.

---

## 7. Dependencies and Ordering

- **Document context (Phase 1–2):** So that the Can Do Descriptors (and other assessment-related docs) can be retrieved when generating lesson plans.
- **Lesson plan schema:** Assessment section and “selected assessment tools” (1–3) need a place in `lesson_json` or the plan structure; to be specified when we detail the schema.
- **Tablet / Lesson Plan Browser:** Assessment tools will be used from the same tablet flow where the teacher views the lesson; UI and data capture to be designed with that context in mind.

---

## 8. Checklist (Planning Only)

- [x] Add Assessment module to roadmap and create this design doc.
- [x] Add WIDA Can Do Descriptors to reference docs / document inventory as a document to be registered.
- [ ] Define the canonical list of assessment tools (checklist, tally, …) and their schemas.
- [ ] Define how the LLM selects tools (prompt, output schema, validation).
- [ ] Define storage and schema for assessment data (per lesson/slot, link to plan); ensure schema supports anonymized identifiers only for any synced or exported data.
- [ ] Design tablet UI for each tool and data flow (Observe/Document); define where and how names vs. codes are shown and stored; encryption at rest for name/code mapping.
- [ ] Design tablet ↔ computer transfer (prefer USB/local only for assessment data containing identifiers); document compliance with FERPA and state/federal student privacy.
- [ ] Integrate Can Do (or extracted content) into document registry when PDF/structured content is supported.
- [ ] Decide Can Do storage format (PDF-only with extraction vs database vs Markdown per cluster+domain) and implement retrieval so only the slot's grade cluster and domain(s) are sent to the LLM; see section 2.5.

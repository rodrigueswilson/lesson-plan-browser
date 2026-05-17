# Phase 1: Curriculum Document Inventory and Grade/Subject Mapping

**Status:** Draft for Phase 1 (Document Context Foundation)  
**Goal:** Clarify which documents supply curriculum context for lesson plan generation and how they map to each grade/subject combination.

**Living inventory:** We will keep inserting and analyzing new documents; this inventory and the catalogs (e.g. [reference_docs/WIDA_ELD/README.md](../../reference_docs/WIDA_ELD/README.md)) should be updated as we document how new docs relate to each other and how they are structured. The **primary source remains the primary teacher's lesson plans**: they determine the lesson number according to the curriculum and decide what is taught on each day and each lesson; reference docs (curriculum, WIDA, strategies) enrich that plan but do not override what or when to teach. See [REFERENCE_DOCS_AND_LESSON_PLAN_ACCESS.md](./REFERENCE_DOCS_AND_LESSON_PLAN_ACCESS.md) sections 1.1 and 1.2.

---

## 1. What counts as "curriculum" here?

In this app, **curriculum context** for generation means:

1. **Pedagogical support** (already in repo): strategies, WIDA framework, co-teaching models. These are **not** organized as one file per grade/subject; they are selected by **grade cluster**, **lesson type**, **proficiency**, and (for strategies) **category**.
2. **Content curriculum** (optional/future): standards, scope, or unit documents per grade and subject (e.g. "Grade 3 Math standards", "ELA Unit 2"). The design allows registering these in the document registry with `subject` + `grade_range`.

For Phase 1 we focus on **cataloging what exists** and defining how the system will **select documents for a given (grade, subject)** so that Phase 2 can implement the lookup service.

---

## 2. Existing document corpus

### 2.1 Strategies (`strategies_pack_v2/`)

| File | Organization | Grade dimension | Subject dimension | Notes |
|------|--------------|-----------------|-------------------|--------|
| `_index.json` | Master index | `grade_clusters`: K-2, 3-5, 6-8, 9-12 | Implicit via `lesson_type` (e.g. math_problem_solving, science_inquiry) | Selection rules: by_lesson_type, by_grade_cluster, by_proficiency_range, by_primary_skill |
| `core/language_skills.json` | Category | K-2, 3-5, 6-8, 9-12 | All (lesson_type drives use) | 9 strategies |
| `core/frameworks_models.json` | Category | 3-5, 6-8, 9-12 | All | 7 strategies |
| `core/cross_linguistic.json` | Category | 3-5, 6-8, 9-12 | All | 8 strategies |
| `core/assessment_scaffolding.json` | Category | K-2, 3-5, 6-8, 9-12 | All | 5 strategies |
| `specialized/social_interactive.json` | Category | K-2, 3-5, 6-8 | All | 2 strategies |
| `specialized/cultural_identity.json` | Category | 3-5, 6-8, 9-12 | All | 2 strategies |

**Grade cluster alignment:** The index uses **K-2, 3-5, 6-8, 9-12**. The ENHANCED design uses **K, 1, 2-3, 4-5, 6-8, 9-12**. We should pick one convention for the registry (e.g. map single grades to these clusters consistently).

**Subject:** Strategies are not stored per subject. Subject enters via **lesson type** (e.g. ELA → reading_comprehension, writing_workshop; Math → math_problem_solving). So "curriculum for grade 3 math" = strategies selected by grade_cluster 3-5 + lesson_type math_problem_solving (+ proficiency).

### 2.2 WIDA (`wida/`)

| File | Organization | Grade dimension | Subject dimension | Notes |
|------|--------------|-----------------|-------------------|--------|
| `wida_framework_reference.json` | Single framework | Grade clusters K, 1, 2-3, 4-5, 6-8, 9-12 | ELD by subject (LA, MA, SC, SS, SI) | Used for all WIDA-aligned generation |
| `wida_strategy_enhancements.json` | Single file | Grade clusters, proficiency bands | All | Proficiency adaptations for 33 strategies |

**Grade/subject:** One file per purpose; content is structured by grade cluster and (in framework) by ELD subject. Lookup is "load these two files when doing WIDA-aligned generation," then use grade/proficiency inside the content. No separate file per grade/subject.

### 2.3 Co-teaching (`co_teaching/`)

| File | Organization | Grade dimension | Subject dimension | Notes |
|------|--------------|-----------------|-------------------|--------|
| `co_teaching_models.json` | 6 models | General | General | Model definitions |
| `wida_model_rules.json` | Rules | WIDA band → model priority | General | Selection rules |
| `phase_patterns_45min.json` | Per model | General | General | Timing templates |
| `portuguese_misconceptions.json` | 6 patterns | General | General | Keyword-triggered |
| `co_teaching_selection_algorithm.json` | Algorithm | General | General | Selection logic |

**Grade/subject:** Co-teaching docs are **not** split by grade or subject. They apply to any lesson; selection is by delivery mode / WIDA band, not by (grade, subject).

### 2.4 WIDA Can Do Descriptors – Original Edition (to be registered)

**Structure (verified from WIDA Original Edition):**

- **Grade level clusters:** PreK–K, **1–2**, **3–5**, 6–8, 9–12. (Grades 1 and 2 are together; grades 3, 4, and 5 are together.)
- **Four language domains:** **Listening**, **Reading**, **Speaking**, **Writing.** Each cluster has content for all four domains.

The document is therefore structured in **parts** by (grade_cluster, domain). When the app plans or assesses **one slot**, it should retrieve only the part(s) for that slot’s **grade cluster** and the **domain(s)** being planned or assessed (e.g. for a grade 3 Writing objective, retrieve only the 3–5 + Writing section). See [ASSESSMENT_MODULE.md](./ASSESSMENT_MODULE.md) (section 2).

| Document | Organization | Grade dimension | Domain dimension | Notes |
|----------|---------------|-----------------|------------------|--------|
| Can Do Descriptors – Original, Student Name Charts (PDF) | By (grade_cluster, domain) | PreK–K, 1–2, 3–5, 6–8, 9–12 | Listening, Reading, Speaking, Writing | Student goals, ELD objectives, assessment section; ODPAR. **Retrieve by part:** only the (grade_cluster, domain) relevant to the slot. Source: `reference_docs/WIDA_ELD/CanDo-Descriptors-Original-Student-Name-Charts.pdf`. Register when document system supports PDF or extracted parts. |

**Use:** When generating lesson plans or assessment for a slot, the LLM receives only the Can Do content for the slot’s grade cluster and domain(s), not the full PreK–12 document. This document is a dependency for the planned Assessment module.

### 2.5 WIDA as one important source - full document set

WIDA is one important source of reference documents for lesson plan generation. The **five WIDA ELD Standards** are the main labels for organizing and retrieving WIDA content: **Standard 1** (Language for Social and Instructional Purposes, foundational), **Standard 2** (Language Arts), **Standard 3** (Mathematics), **Standard 4** (Science), **Standard 5** (Social Studies). Map the slot's subject to the corresponding standard when retrieving ELD Framework or related documents. See [reference_docs/WIDA_ELD/README.md](../../reference_docs/WIDA_ELD/README.md) for the full relationship and subject-to-standard mapping. The following are stored under `reference_docs/` and `reference_docs/WIDA_ELD/`. For the detailed catalog and retrieval strategy, see [reference_docs/WIDA_ELD/README.md](../../reference_docs/WIDA_ELD/README.md).

| Document | Location | Grade dimension | Retrieval | Use in generation |
|----------|----------|-----------------|-----------|-------------------|
| Can Do Descriptors (Original, Student Name Charts) | reference_docs root | PreK-K, 1-2, 3-5, 6-8, 9-12 | By (cluster, domain) | Goals, ELD objectives, assessment; ODPAR |
| ELD Standards Framework 2020 - Kindergarten | WIDA_ELD/ | K | By file | Language Expectations, standards alignment |
| ELD Standards Framework 2020 - Grade 1 | WIDA_ELD/ | 1 | By file | Same |
| ELD Standards Framework 2020 - Grades 2-3 | WIDA_ELD/ | 2-3 | By file | Same |
| ELD Standards Framework 2020 - Grades 4-5 | WIDA_ELD/ | 4-5 | By file | Same |
| ELD Standards Framework 2020 - Grades 6-8 | WIDA_ELD/ | 6-8 | By file | Same |
| ELD Standards Framework 2020 - Grades 9-12 | WIDA_ELD/ | 9-12 | By file | Same |
| ELD Standards Framework 2020 (full/overview) | WIDA_ELD/ | All | Whole; cross-cluster reference only | Overview; not slot-specific |
| WIDA Language Charts | reference_docs root | K-12 | Whole or by section | Discourse/sentence/word; assessment planning |
| WIDA Standards FAQ - Language Expectations | reference_docs root | General | Whole | How to use standards |

When planning one slot: load only the grade-cluster file(s) or parts that match the slot. Do not load all WIDA documents for a single slot.

---

## 3. How (grade, subject) maps to documents today

For a lesson with **grade = 3**, **subject = Math**:

1. **Strategies:** Map grade 3 → cluster **3-5**. Map subject Math → lesson_type **math_problem_solving**. Index says math_problem_solving → categories `["language_skills", "assessment_scaffolding"]`. Load `core/language_skills.json` + `core/assessment_scaffolding.json`; filter strategies by grade_cluster 3-5 and proficiency.
2. **WIDA:** Load both `wida_framework_reference.json` and `wida_strategy_enhancements.json`; use grade cluster and ELD-MA (math) inside.
3. **Co-teaching:** Load models + rules + phase_patterns + misconceptions as needed by delivery mode.

So **"documents for grade/subject"** is:

- **Strategies:** 2–4 category files, chosen by (grade_cluster, lesson_type, proficiency).
- **WIDA:** 2 fixed files; content used by (grade_cluster, subject/ELD, proficiency).
- **Co-teaching:** 4–5 files; not keyed by grade/subject.

There are **no** per-(grade, subject) content files (e.g. "Grade 3 Math standards") unless we add and register them later.

---

## 4. Proposed metadata dimensions for the registry

For Phase 1 inventory and Phase 2 lookup, use:

| Dimension | Values / notes |
|-----------|-----------------|
| **document_type** | `strategy` \| `wida` \| `co_teaching` \| `curriculum` \| `assessment` |
| **grade_range** | Single convention, e.g. `K`, `1`, `2-3`, `4-5`, `6-8`, `9-12` (NULL = all grades) |
| **subject** | `math`, `ela`, `science`, `social_studies`, etc. (NULL = all subjects) |
| **category** | For strategies: category name (e.g. `language_skills`). For others: optional grouping. |
| **lesson_type** | For strategy selection: e.g. `math_problem_solving`, `reading_comprehension`. Optional in registry; can stay in _index.json and be used by the service. |

Strategy files get `document_type=strategy`, `grade_range` from category’s grade_clusters (or NULL if used for all), `subject=NULL`, `category` from index. WIDA/co-teaching get their types and NULL grade_range/subject unless we add more granular metadata later.

---

## 5. Phase 1 checklist (aligned with IMPLEMENTATION_ROADMAP)

- [ ] **Document inventory**: Catalog each file in `strategies_pack_v2/`, `wida/`, `co_teaching/` with the dimensions above (document_type, grade_range, subject, category).
- [ ] **Grade cluster convention**: Decide and document one canonical set (e.g. K, 1, 2-3, 4-5, 6-8, 9-12) and map from single grade and from _index.json clusters consistently.
- [ ] **Subject ↔ lesson_type**: Document the mapping from app subject (math, ela, science, …) to strategy index `lesson_type` so the service can resolve (grade, subject) → strategy categories.
- [ ] **Schema stability**: Confirmed already for OriginalLessonPlan and lesson_json.
- [ ] **Retrieval logging design**: Define what to store when documents are used (which files, query profile, token estimate, timestamp) for auditing and debugging.

---

## 6. Next steps

1. **Confirm grade cluster convention** (e.g. K, 1, 2-3, 4-5, 6-8, 9-12) and add a small mapping table: single grade → cluster, and _index.json cluster name → registry cluster if different.
2. **Write the inventory** as a static table (or JSON) listing every file with its metadata dimensions, then use it to populate the `curriculum_documents` registry in Phase 2.
3. **Document subject → lesson_type** in one place (e.g. in this file or in the service spec) so "curriculum for grade 3 math" is unambiguous for the CurriculumContextService.

Once this is agreed, Phase 2 can implement `CurriculumContextService` with metadata-driven lookup and the indexing script that fills the registry from the existing directories.

**Related:** [REFERENCE_DOCS_AND_LESSON_PLAN_ACCESS.md](./REFERENCE_DOCS_AND_LESSON_PLAN_ACCESS.md) — plan for how reference docs are accessible, dual audience (humans + LLMs/agents/skills), and how they are queried during lesson plan creation; embeddings/vector DB decision deferred until we have a clearer picture of what information is consulted.

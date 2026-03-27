# Roadmap - Bilingual Weekly Plan Builder

This directory is the single entry point for **planned** (not-yet-implemented) modules and features. For what is already implemented, see [../IMPLEMENTATION_STATUS.md](../IMPLEMENTATION_STATUS.md).

---

## Project summary and current status

The Bilingual Weekly Plan Builder is production-ready for core lesson plan generation, multi-user processing, Lesson Plan Browser (week/day/lesson views, current lesson, Today), Tablet tab, Analytics dashboard, slot-level reprocessing, and document/output enhancements. The roadmap below lists only **planned** work.

**Curriculum Navigator vs what exists today:** An initial **DB-backed curriculum explorer** is implemented (`curriculum.db`, FastAPI `/api/curriculum/*`, lesson-plan-browser `CurriculumExplorer`) with structured standards and rich lesson HTML—see [IMPLEMENTATION_STATUS.md](../IMPLEMENTATION_STATUS.md) and [scrapers/CURRICULUM_EXTRACTION_ARCHITECTURE.md](../scrapers/CURRICULUM_EXTRACTION_ARCHITECTURE.md). The **Curriculum Navigator** designs below still cover **FTS/search**, **registry-aligned hierarchy**, and **planning integration** beyond that MVP.

---

## Short-term and long-term goals

- **Short-term:** Document context foundation (local metadata-driven lookup) and service layer; Browser filter UI; remaining enhancement-plan items (session history, folder picker, image/hyperlink preservation if not done).
- **Long-term:** Vocabulary module; Agent Skills / MCP; Games and SCORM; P2P sync; containerized workers; cross-platform (React Native) if needed.

---

## Planned modules (status and design docs)


| Module or feature                         | Status  | Design / detail                                                                                                                                                                                 |
| ----------------------------------------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Document Context (local MCP access)**   | Planned | [design/ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md](design/ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md), [design/IMPLEMENTATION_ROADMAP.md](design/IMPLEMENTATION_ROADMAP.md) (Phases 1–2). Google FileSearch retained as hypothesis. |
| **Progressive Ingestion (Gap Manager)** | Planned | [design/PROGRESSIVE_CURRICULUM_INGESTION.md](design/PROGRESSIVE_CURRICULUM_INGESTION.md) – Identify, track, and ingest missing curriculum links from teacher-uploaded lesson plans in real-time. |
| **Curriculum Navigator**                | Planned | [design/CURRICULUM_NAVIGATOR_MODULE.md](design/CURRICULUM_NAVIGATOR_MODULE.md) – Browse, search, and query the entire reference curriculum (Grade, Subject, Unit, Lesson) in a fast, web-based interface. |
| **Curriculum Expansion (Teacher Improvements)** | Planned | [design/CURRICULUM_EXPANSION_MODULE.md](design/CURRICULUM_EXPANSION_MODULE.md) – Allow teachers to enrich the official curriculum with supplementary videos, links, and detailed concepts while respecting standards. |
| **Curriculum JSON RAG / Vector DB (ETL)** | Planned | [design/CURRICULUM_JSON_DATABASE_ETL.md](design/CURRICULUM_JSON_DATABASE_ETL.md) – Extract scraped Markdown into highly structured JSON schemas for agents, MCP tools, and metadata-filtered Vector Databases (like Qdrant). |
| **WIDA framework ingestion**             | Planned | [design/WIDA_FRAMEWORK_INGESTION_AND_USE.md](design/WIDA_FRAMEWORK_INGESTION_AND_USE.md) – Extract/scrape WIDA PDFs; convert to database, Markdown; optionally later embeddings/vector DB. WIDA as "operating system" for lesson plans. |
| **Lesson planning balance (domains + key uses)** | Planned | [design/LESSON_PLANNING_BALANCE.md](design/LESSON_PLANNING_BALANCE.md) – Balance four domains and four Key Language Uses by subject across weekly, unit, period, school year; planner memory and prediction. |
| **Assessment module**                     | Planned | [design/ASSESSMENT_MODULE.md](design/ASSESSMENT_MODULE.md) – LLM-designed assessment per lesson, tool set (checklist, tally, etc.), tablet data collection; WIDA Can Do Descriptors; ODPAR cycle. Legal/privacy: FERPA and state/federal student privacy; anonymization; no student names on internet; USB/local transfer preferred; LLM never receives PII. |
| **Vocabulary module**                     | Planned | [design/ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md](design/ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md)                                                                                    |
| **Agent Skills / MCP**                    | Planned | [design/AGENT_SKILLS_AND_CODE_EXECUTION.md](design/AGENT_SKILLS_AND_CODE_EXECUTION.md), [design/IMPLEMENTATION_ROADMAP.md](design/IMPLEMENTATION_ROADMAP.md) (Phase 3)                          |
| **API client contract (OpenAPI codegen)** | Planning | [design/API_CLIENT_CONTRACT_TOOLING.md](design/API_CLIENT_CONTRACT_TOOLING.md) – Typed HTTP client from FastAPI OpenAPI; **Orval** + TanStack React Query recommended; incremental adoption vs [shared/lesson-api](../../shared/lesson-api/). |
| **Browser: Subject/Grade/Time filter UI** | Planned | [design/LESSON_PLAN_BROWSER_MODULE.md](design/LESSON_PLAN_BROWSER_MODULE.md)                                                                                                                    |
| **Browser: Schedule-order UI polish**     | Planned | [design/IMPLEMENTATION_ROADMAP.md](design/IMPLEMENTATION_ROADMAP.md) (Phase 4), [design/LESSON_PLAN_BROWSER_MODULE.md](design/LESSON_PLAN_BROWSER_MODULE.md)                                    |
| **Lesson Plan Editor**                    | Planning | [design/lesson_plan_editor/README.md](design/lesson_plan_editor/README.md) – Manual rich-text edit + LLM assistant; SSOT `lesson_json`; research memo and architecture bundle.                      |
| **Pedagogical tooltips / popovers**       | Research | [design/pedagogical_tooltips/README.md](design/pedagogical_tooltips/README.md) – Strategy and WIDA inline help in Browser/Lesson Mode; research bundle (data inventory, UX/a11y, spikes, decision log). |
| **Lesson Package (cmi5 + Worksheet)**     | Planned | [design/CMI5_PACKAGE_GENERATION.md](design/CMI5_PACKAGE_GENERATION.md), [design/WORKSHEET_MODULE.md](design/WORKSHEET_MODULE.md) – Unified per-lesson output: a digital cmi5 package and a printable worksheet, both ODPAR-aligned. |
| **Worksheet PDF Localization (EN -> PT)** | Planned (deferred) | [design/PDF_WORKSHEET_LOCALIZATION_MODULE.md](design/PDF_WORKSHEET_LOCALIZATION_MODULE.md) – Preserve source template (measures/images/layout) while replacing language layer with Portuguese text and retaining math/formula fidelity. Deferred until current curriculum ingestion/fidelity phases stabilize. |
| **Agentic cmi5 Design Rules**            | Research | [design/AGENTIC_CMI5_DESIGN_RULES.md](design/AGENTIC_CMI5_DESIGN_RULES.md) – Pedagogical "instruction manual" for agents, incorporating best practices for language and content development. |
| **Student Data Privacy (FERPA)**        | Planning | [design/STUDENT_DATA_PRIVACY_AND_FERPA.md](design/STUDENT_DATA_PRIVACY_AND_FERPA.md) – Mandatory security framework for protecting student PII and ensuring legal compliance. |
| **P2P sync**                              | Planned | [design/DATABASE_ARCHITECTURE_AND_SYNC.md](design/DATABASE_ARCHITECTURE_AND_SYNC.md)                                                                                                            |
| **Containerized workers**                 | Planned | [design/CONTAINERIZATION_STRATEGY.md](design/CONTAINERIZATION_STRATEGY.md), [design/IMPLEMENTATION_ROADMAP.md](design/IMPLEMENTATION_ROADMAP.md) (Phase 5)                                      |
| **Session-based history view**            | Planned | [../planning/FEATURE_ENHANCEMENT_PLAN.md](../planning/FEATURE_ENHANCEMENT_PLAN.md) (Feature 11)                                                                                                 |
| **Source folder path confirmation**       | Planned | [../planning/FEATURE_ENHANCEMENT_PLAN.md](../planning/FEATURE_ENHANCEMENT_PLAN.md) (Feature 8)                                                                                                  |
| **Image preservation (input to output)**  | Planned | [../planning/FEATURE_ENHANCEMENT_PLAN.md](../planning/FEATURE_ENHANCEMENT_PLAN.md) (Feature 2)                                                                                                  |
| **Hyperlink preservation**                | Planned | [../planning/FEATURE_ENHANCEMENT_PLAN.md](../planning/FEATURE_ENHANCEMENT_PLAN.md) (Feature 4)                                                                                                  |
| **Cross-platform (React Native, etc.)**   | Planned | [design/CROSS_PLATFORM_TECHNOLOGY_ANALYSIS.md](design/CROSS_PLATFORM_TECHNOLOGY_ANALYSIS.md)                                                                                                    |


---

## Design documents (detailed specs)

All detailed design and architecture docs for the above are under **[design/](design/)** (moved from `expansionNov/`). Start with [design/README.md](design/README.md) for the document index and relationships.

- **Curriculum JSON ETL Strategy (RAG & Vector DB):** [design/CURRICULUM_JSON_DATABASE_ETL.md](design/CURRICULUM_JSON_DATABASE_ETL.md) — Architectural strategy for loading scraped curriculum Markdown into structured JSON schemas to support exact agent queries, dynamic component swapping, and structured RAG via Vector Databases (like Qdrant).
- **Progressive Ingestion (Gap Manager):** [design/PROGRESSIVE_CURRICULUM_INGESTION.md](design/PROGRESSIVE_CURRICULUM_INGESTION.md) — Identify and ingest missing curriculum links from teacher lesson plans.
- **Curriculum Navigator:** [design/CURRICULUM_NAVIGATOR_MODULE.md](design/CURRICULUM_NAVIGATOR_MODULE.md) — Fast browsing and full-text search across the reference curriculum.
- **Curriculum Expansion:** [design/CURRICULUM_EXPANSION_MODULE.md](design/CURRICULUM_EXPANSION_MODULE.md) — Teacher-led enrichment of the official curriculum.
- **Phase 1 document inventory:** [design/PHASE1_CURRICULUM_DOCUMENT_INVENTORY.md](design/PHASE1_CURRICULUM_DOCUMENT_INVENTORY.md) — curriculum documents per grade/subject, existing corpus catalog, and metadata dimensions for the context service.
- **Reference docs and lesson plan access:** [design/REFERENCE_DOCS_AND_LESSON_PLAN_ACCESS.md](design/REFERENCE_DOCS_AND_LESSON_PLAN_ACCESS.md) — how reference documentation is accessible, intelligible to humans and LLMs/agents/skills, and used when creating lesson plans. (Note: Embedding/Vector DB decision updated to support the JSON ETL strategy).
- **WIDA framework ingestion and use:** [design/WIDA_FRAMEWORK_INGESTION_AND_USE.md](design/WIDA_FRAMEWORK_INGESTION_AND_USE.md) — WIDA as "operating system" for lesson plans; plan for a software module to extract/scrape WIDA PDFs and convert to database, Markdown, and (optionally later) embeddings/vector DB; phasing and integration with CurriculumContextService.
- **Lesson planning balance:** [design/LESSON_PLANNING_BALANCE.md](design/LESSON_PLANNING_BALANCE.md) — Balance of the four domains (Listening, Reading, Speaking, Writing) and four Key Language Uses (Narrate, Argue, Inform, Explain) by subject across four layers: weekly (5 days), by unit, by period, by school year; planner memory and prediction to maintain balance.
- **Pedagogical tooltips and popovers:** [design/pedagogical_tooltips/README.md](design/pedagogical_tooltips/README.md) — Research for in-app strategy and WIDA glosses from existing JSON SSOT; gate criteria before implementation.
- **API client contract (OpenAPI codegen):** [design/API_CLIENT_CONTRACT_TOOLING.md](design/API_CLIENT_CONTRACT_TOOLING.md) — Orval + TanStack React Query recommended; OpenAPI from FastAPI as SSOT.

---

## Related documentation

- **Implemented features:** [../IMPLEMENTATION_STATUS.md](../IMPLEMENTATION_STATUS.md)
- **Documentation policy:** [../DOCUMENTATION_POLICY.md](../DOCUMENTATION_POLICY.md)
- **Planning docs (mixed implemented/planned):** [../planning/](../planning/) – see status notes in each file (e.g. TABLET_TAB_PLAN is implemented; FEATURE_ENHANCEMENT_PLAN has a Status section).


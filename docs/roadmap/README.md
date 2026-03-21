# Roadmap - Bilingual Weekly Plan Builder

This directory is the single entry point for **planned** (not-yet-implemented) modules and features. For what is already implemented, see [../IMPLEMENTATION_STATUS.md](../IMPLEMENTATION_STATUS.md).

---

## Project summary and current status

The Bilingual Weekly Plan Builder is production-ready for core lesson plan generation, multi-user processing, Lesson Plan Browser (week/day/lesson views, current lesson, Today), Tablet tab, Analytics dashboard, slot-level reprocessing, and document/output enhancements. The roadmap below lists only **planned** work.

---

## Short-term and long-term goals

- **Short-term:** Document context foundation (local metadata-driven lookup) and service layer; Browser filter UI; remaining enhancement-plan items (session history, folder picker, image/hyperlink preservation if not done).
- **Long-term:** Vocabulary module; Agent Skills / MCP; Games and SCORM; P2P sync; containerized workers; cross-platform (React Native) if needed.

---

## Planned modules (status and design docs)


| Module or feature                         | Status  | Design / detail                                                                                                                                                                                 |
| ----------------------------------------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Document Context (local MCP access)**   | Planned | [design/ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md](design/ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md), [design/IMPLEMENTATION_ROADMAP.md](design/IMPLEMENTATION_ROADMAP.md) (Phases 1–2). Google FileSearch retained as hypothesis. |
| **WIDA framework ingestion**             | Planned | [design/WIDA_FRAMEWORK_INGESTION_AND_USE.md](design/WIDA_FRAMEWORK_INGESTION_AND_USE.md) – Extract/scrape WIDA PDFs; convert to database, Markdown; optionally later embeddings/vector DB. WIDA as "operating system" for lesson plans. |
| **Lesson planning balance (domains + key uses)** | Planned | [design/LESSON_PLANNING_BALANCE.md](design/LESSON_PLANNING_BALANCE.md) – Balance four domains and four Key Language Uses by subject across weekly, unit, period, school year; planner memory and prediction. |
| **Assessment module**                     | Planned | [design/ASSESSMENT_MODULE.md](design/ASSESSMENT_MODULE.md) – LLM-designed assessment per lesson, tool set (checklist, tally, etc.), tablet data collection; WIDA Can Do Descriptors; ODPAR cycle. Legal/privacy: FERPA and state/federal student privacy; anonymization; no student names on internet; USB/local transfer preferred; LLM never receives PII. |
| **Vocabulary module**                     | Planned | [design/ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md](design/ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md)                                                                                    |
| **Agent Skills / MCP**                    | Planned | [design/AGENT_SKILLS_AND_CODE_EXECUTION.md](design/AGENT_SKILLS_AND_CODE_EXECUTION.md), [design/IMPLEMENTATION_ROADMAP.md](design/IMPLEMENTATION_ROADMAP.md) (Phase 3)                          |
| **Browser: Subject/Grade/Time filter UI** | Planned | [design/LESSON_PLAN_BROWSER_MODULE.md](design/LESSON_PLAN_BROWSER_MODULE.md)                                                                                                                    |
| **Browser: Schedule-order UI polish**     | Planned | [design/IMPLEMENTATION_ROADMAP.md](design/IMPLEMENTATION_ROADMAP.md) (Phase 4), [design/LESSON_PLAN_BROWSER_MODULE.md](design/LESSON_PLAN_BROWSER_MODULE.md)                                    |
| **Lesson Plan Editor**                    | Planning | [design/lesson_plan_editor/README.md](design/lesson_plan_editor/README.md) – Manual rich-text edit + LLM assistant; SSOT `lesson_json`; research memo and architecture bundle.                      |
| **Pedagogical tooltips / popovers**       | Research | [design/pedagogical_tooltips/README.md](design/pedagogical_tooltips/README.md) – Strategy and WIDA inline help in Browser/Lesson Mode; research bundle (data inventory, UX/a11y, spikes, decision log). |
| **Games / SCORM**                         | Planned | [design/ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md](design/ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md)                                                                                    |
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

- **Phase 1 document inventory:** [design/PHASE1_CURRICULUM_DOCUMENT_INVENTORY.md](design/PHASE1_CURRICULUM_DOCUMENT_INVENTORY.md) — curriculum documents per grade/subject, existing corpus catalog, and metadata dimensions for the context service.
- **Reference docs and lesson plan access:** [design/REFERENCE_DOCS_AND_LESSON_PLAN_ACCESS.md](design/REFERENCE_DOCS_AND_LESSON_PLAN_ACCESS.md) — how reference documentation is accessible, intelligible to humans and LLMs/agents/skills, and used when creating lesson plans; embeddings/vector DB decision deferred until we know more about what information is consulted during lesson plan creation.
- **WIDA framework ingestion and use:** [design/WIDA_FRAMEWORK_INGESTION_AND_USE.md](design/WIDA_FRAMEWORK_INGESTION_AND_USE.md) — WIDA as "operating system" for lesson plans; plan for a software module to extract/scrape WIDA PDFs and convert to database, Markdown, and (optionally later) embeddings/vector DB; phasing and integration with CurriculumContextService.
- **Lesson planning balance:** [design/LESSON_PLANNING_BALANCE.md](design/LESSON_PLANNING_BALANCE.md) — Balance of the four domains (Listening, Reading, Speaking, Writing) and four Key Language Uses (Narrate, Argue, Inform, Explain) by subject across four layers: weekly (5 days), by unit, by period, by school year; planner memory and prediction to maintain balance.
- **Pedagogical tooltips and popovers:** [design/pedagogical_tooltips/README.md](design/pedagogical_tooltips/README.md) — Research for in-app strategy and WIDA glosses from existing JSON SSOT; gate criteria before implementation.

---

## Related documentation

- **Implemented features:** [../IMPLEMENTATION_STATUS.md](../IMPLEMENTATION_STATUS.md)
- **Documentation policy:** [../DOCUMENTATION_POLICY.md](../DOCUMENTATION_POLICY.md)
- **Planning docs (mixed implemented/planned):** [../planning/](../planning/) – see status notes in each file (e.g. TABLET_TAB_PLAN is implemented; FEATURE_ENHANCEMENT_PLAN has a Status section).


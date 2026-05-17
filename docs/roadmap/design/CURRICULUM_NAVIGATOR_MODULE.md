# Curriculum Navigator Module

## Current implementation (MVP)

The repo already ships a **database-backed reference explorer**: `curriculum.db` is populated via `ingest_to_curriculum`, exposed through FastAPI under `/api/curriculum/*`, and browsed in the lesson-plan-browser **CurriculumExplorer** (structured `standards_structured`, procedure HTML, resources). Pipeline behavior is documented in [CURRICULUM_EXTRACTION_ARCHITECTURE.md](../../scrapers/CURRICULUM_EXTRACTION_ARCHITECTURE.md). The phases below extend that MVP toward **full Navigator** capabilities (registry coverage, FTS, planning hooks)—they are not a greenfield assumption.

## 📋 Overview
The **Curriculum Navigator** is a dedicated research and planning tool that allows teachers to browse, search, and query the entire reference curriculum repository (Grades K-12, all Subjects) through a high-performance web interface. It eliminates the need to manually open and navigate Board of Education Word documents.

## 🎯 Key Objectives
1. **Hierarchical Browsing**: Seamlessly navigate from Grade → Subject → Unit → Lesson folder structures.
2. **Instant Search**: Full-text search across all curriculum content (Markdown/JSON) to find specific standards, keywords, or activities.
3. **Content Preview**: Detailed view of lesson objectives, materials, and procedures directly in the browser.
4. **Planning Support**: Allow teachers to "pin" or "reference" curriculum lessons while preparing their own weekly plans.

## 🛠️ Components

### A. Curriculum Discovery Service (Backend)
- Uses the `scraped_registry.json` and the `reference_docs/curriculum/` directory as its primary data source.
- Fast indexing (potentially using a lightweight search index like Lunr.js or a simple SQLite FTS5 table).
- Dynamic metadata extraction (detecting Objectives vs. Assessments in the Markdown).

### B. Navigator UI (Frontend)
- **Explorer Sidebar**: Tree-view of the curriculum hierarchy.
- **Search Bar**: Global search with filters for Grade and Subject.
- **Preview Pane**: Rich-text rendering of the selected curriculum unit or lesson.
- **Unit Overview**: High-level summary of unit goals and key learnings.

### C. Search & Filter Bar
- Filter by Grade (e.g., "Grade 2 only").
- Filter by Subject (e.g., "Math").
- Keyword search (e.g., "Number Line").

## 📅 Phases

### Phase 1: Static Hierarchy Browser
- Implement the "Explorer" view using existing `scraped_registry.json`.
- Enable markdown rendering for unit/lesson descriptions.
- Basic navigation (click a unit to see its lessons).

### Phase 2: Full-Text Search
- Implement a search index for all curriculum Markdown files.
- Add the global search bar with instant results.
- Highlight search terms in the preview pane.

### Phase 3: Advanced Queries & Planning Integration
- Enable "Complex Queries" (e.g., "Find all lessons in 3rd grade ELA that mention 'Main Idea'").
- Add "Copy to Plan" button to quickly pull curriculum objectives into the current lesson builder.

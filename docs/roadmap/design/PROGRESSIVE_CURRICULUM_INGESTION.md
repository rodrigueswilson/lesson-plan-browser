# Progressive Curriculum Ingestion (Gap Manager)

## 📋 Overview
The **Progressive Curriculum Ingestion** module is designed to bridge the gap between classroom reality (teacher-uploaded lesson plans) and the local curriculum repository. It identifies curriculum document links (Google Docs, PDFs, etc.) referenced in teacher plans that are not yet part of the local codebase.

## 🎯 Key Objectives
1. **Real-time Detection**: Automatically identify new document links in the `original_lesson_plans` table as they are uploaded.
2. **Gap Visualization**: Provide a UI dashboard (Gap Manager) where users can see a list of missing documents organized by Grade, Subject, Unit, and Lesson.
3. **Integrated Ingestion**: Allow users to trigger a "Scrape & Ingest" action directly from the UI for any detected gap.
4. **LLM Synergy**: Ensure the LLM uses these identified "required" documents to enrich its context before generating or refining lesson plans.

## 🛠️ Components

### A. Database Monitor (Backend)
- A trigger or periodic scan on the `original_lesson_plans` table.
- Use the logic from `tools/scraper/gap_detect_db.py` to extract links and associate them with existing metadata.
- Maintain a `curriculum_gap_registry` in the database to track the status of each gap (Detected, Pending, Scraped, Skipped).

### B. Ingestion UI (Frontend)
- **Gap List View**: A table/tree view showing missing documents.
- **Action Toolbar**: Buttons to "Download All for Unit", "Download Selection", or "Mark as Manually Added".
- **Progress Tracking**: Real-time progress bars for active scraping sessions.

### C. Agent Integration
- An "Ingestion Agent" that can proactively suggest downloading missing materials when a user starts planning a unit.
- "Permission-based" workflow: "I see you're planning Unit 4, but I'm missing the Number Line overview. Should I download it now?"

## 📅 Phases

### Phase 1: Interactive Gap Dashboard
- Migrate `gap_detect_db.py` logic into a backend service.
- Create the "Curriculum Gaps" tab in the UI.
- Display the prioritized list of missing documents.

**Implemented hook (partial):** Shared gap logic lives in `backend/services/curriculum_gaps.py` (also used by `tools/scraper/gap_detect_db.py`). The API exposes **`GET /api/curriculum/gaps`**, which compares Google Doc links in `original_lesson_plans` (lesson planner SQLite) to `reference_docs/scraped_registry.json`. A dedicated Gap Manager UI tab and one-click ingest are still **Phase 1–2** scope.

### Phase 2: One-Click Ingestion
- Integrate the `CurriculumCrawler` and `DocsClient` into the main application.
- Implement the "Scrape" button in the UI.
- Update `scraped_registry.json` automatically upon success.

### Phase 3: Automated Monitoring & Agent Proactivity
- Implement the background scanner for new uploads.
- Integrate gap detection into the LLM prompt preparation (checking context completeness before generation).

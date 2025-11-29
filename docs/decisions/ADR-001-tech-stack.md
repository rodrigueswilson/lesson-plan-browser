## ADR-001: Technology Stack Selection

### Status
Accepted (2025-09-20)  
Updated (2025-10-05) - Multi-slot rendering approach

### Context
- App processes weekly `.docx` lesson plans, transforms them using WIDA-aligned logic, and outputs a compiled `.docx` matching the district template `input/Lesson Plan Template SY'25-26.docx`.
- Offline-first, local filesystem workflows, zero IT constraints, DOCX-only in v1.
- Performance targets: p95 < 3s for core strategy/objective generation; total weekly run < 10 minutes including parsing/merge/render.

### Decision
- Desktop wrapper: Tauri (small bundle, native integration)
- Frontend: React + TypeScript (lean), i18next (EN/PT)
- Backend: Python FastAPI over 127.0.0.1 (HTTP + SSE) for document processing
- Packaging: PyInstaller one-file backend; Pydantic schemas (JSON Schema to client)
- Storage: SQLite (local-first); OS keychain for secrets (LLM keys, if used)
- Document processing: `python-docx` + `docxcompose` with district `.dotx` template
- Updates: In-app “update available” notice opening release page (no auto-update)
- CI/QA: GitHub Actions (lint, type-check, tests, SAST/secret scan); Pytest, Playwright, axe

### Rationale
- Python ecosystem is best-in-class for `.docx` parsing, table handling, and templated rendering.
- Tauri provides fast startup, small bundle, lower memory vs Electron; no IT constraints to bias toward Electron.
- Localhost HTTP + SSE is simple, testable, and adequate for progress streaming.
- SQLite meets profile/config needs; easy to back up and migrate if required.

### Scope & Constraints
- DOCX is the only output (and input) format in v1; no PDF or other formats.
- Header in the district template remains static; dynamic fields are populated only in body tables.

### Alternatives Considered
- Electron + React + FastAPI
  - Pros: mature ecosystem; familiar
  - Cons: larger bundle/runtime; higher memory
- PWA-only (no desktop wrapper)
  - Pros: simplest distribution
  - Cons: weaker filesystem integration; offline packaging complexity
- Streamlit/Gradio (full Python stack)
  - Pros: rapid prototyping
  - Cons: limited UX control; packaging overhead

### Consequences
- Pros: small installer; robust DOCX handling; clear separation of UI and processing; privacy-friendly local runtime.
- Cons: introduces Rust toolchain for Tauri builds; need PyInstaller configuration and resource path handling.

### Implementation Notes
- Bind backend to 127.0.0.1 with ephemeral port; expose SSE endpoint for compile progress.
- Cache WIDA JSON in-memory; parallelize `.docx` parsing; normalize to district `.dotx` with numbering copied wholesale from template.
- Apply calibrated capacity heuristics (~70% of raw) with sentence-boundary truncation and continuation references for overflow.

### Out of Scope (v1)
- PDF export and any non-DOCX outputs
- Auto-updaters and enterprise deployment features

---

## Update: Multi-Slot Rendering Approach (2025-10-05)

### Context
Initial design attempted to merge multiple class slots into a single DOCX with combined tables. Testing revealed:
- Complex table copying issues with `python-docx` (property setters not available)
- Data integrity issues (only Monday data rendering, other days empty)
- Template formatting not preserved correctly

### Revised Decision
**Generate separate DOCX files per slot** instead of merging into one document.

**Implementation:**
- Each slot gets its own complete DOCX file with full template formatting
- Filename pattern: `{UserName}_Slot{N}_{Subject}_W{WeekNum}_{DateRange}.docx`
- Last file includes signature box
- All files saved to week folder: `{BasePath}/{YY} W{WeekNum}/`

**Example Output:**
```
F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W41\
├── Wilson_Rodrigues_Slot1_ELA_W41_10-06-10-10.docx
├── Wilson_Rodrigues_Slot2_Science_W41_10-06-10-10.docx
├── Wilson_Rodrigues_Slot3_Math_W41_10-06-10-10.docx
├── Wilson_Rodrigues_Slot4_SocialStudies_W41_10-06-10-10.docx
└── Wilson_Rodrigues_Slot5_Reading_W41_10-06-10-10.docx (with signature)
```

### Rationale
- **Reliability**: Uses proven single-slot renderer (no complex table copying)
- **Flexibility**: Each slot can be reviewed/printed independently
- **Simplicity**: Avoids `python-docx` limitations with table element manipulation
- **User Control**: Teachers can combine files manually if needed (Word merge, PDF tools)
- **Performance**: Parallel rendering possible in future (currently sequential)

### Trade-offs
- **Pro**: Immediate working solution, no data loss, proper formatting
- **Pro**: Each slot maintains complete template fidelity
- **Pro**: Easy to debug individual slot issues
- **Con**: Multiple files instead of one (user requested this approach)
- **Con**: Manual combination needed if single file required

### Future Enhancements (Phase 2)
- Optional: Implement DOCX merge using `docxcompose` library
- Optional: Add "Combine All" button in UI to merge files post-generation
- Optional: PDF export with all slots in one document

### File Resolution Architecture
Implemented hybrid file resolution with clear priority:
1. Direct absolute path (if exists)
2. Relative to week folder (if exists)  
3. Pattern-based search in week folder
4. Fallback to `input/` for testing

Database schema enhanced with `week_folder_path` column in `weekly_plans` table for explicit folder control.


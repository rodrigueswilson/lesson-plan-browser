# November Expansion - Master Index

**Created**: 2025-11-XX  
**Status**: PLANNING PHASE  
**Purpose**: Architectural enhancements for enhanced lesson plan generation, vocabulary management, and new modules

---

## 📚 Document Overview

This folder contains the planning and architecture documents for the November expansion of the Lesson Plan Builder application. These documents describe new features and architectural changes that will be implemented in phases.

> **Implementation status (Nov 2025 reality check)**  
> A review of the production codebase (`backend/api.py`, `backend/database.py`, `tools/batch_processor.py`, `frontend/src/components`) shows that:
> - ✅ Existing FastAPI + Tauri functionality (multi-slot batch processing, schedule CRUD, current lesson browser) matches the pre-expansion product.
> - ⚠️ Lesson Plan Browser MVP (week/day/lesson modes) exists, but none of the schedule-based filtering, “current lesson” auto-focus, or mobile React Native port described in Phase 4 have shipped yet (`LessonPlanBrowser`, `WeekView`, `DayView`).
> - ❌ Database sync enhancements (Supabase JSONB columns, local caches, vector clocks, new vocabulary/RAG tables) are not present in `backend/database.py`.
> - ❌ FileSearch/RAG integration, vocabulary generation/approvals, multimedia workers, and SCORM/game modules are entirely absent from backend/services and tooling.
> - ❌ Containerized worker stack (Redis/Celery), Agent Skills/MCP sandboxing, and code-execution safeguards have not been implemented.
> - ❌ Cross-platform strategy (React Native/Capacitor targets) remains planning-only; `frontend/` contains only the Tauri webview app.

| Feature Area | Doc Reference | Reality (Nov 2025) |
|--------------|---------------|--------------------|
| Database + Sync | `DATABASE_ARCHITECTURE_AND_SYNC.md` | Legacy SQLite schema only; no Supabase JSONB columns, vector clocks, or P2P security. |
| FileSearch RAG | `ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md` | Not implemented; `batch_processor` calls LLM directly without retrieval context. |
| Vocabulary Module | same | No vocab tables/endpoints/UI; multimedia pipeline absent. |
| Containerization | `CONTAINERIZATION_STRATEGY.md` | Monitoring compose only; no worker containers or Redis/Celery stack. |
| Agent Skills / MCP | `AGENT_SKILLS_AND_CODE_EXECUTION.md` | No skill folders, sandbox, or MCP integration in backend. |
| Lesson Plan Browser | `LESSON_PLAN_BROWSER_MODULE.md`, `UI_PLANNING_*` | Partial (week/day/lesson views). Missing filtering, time-aware defaults, advanced lesson mode, mobile parity. |
| Cross-Platform | `CROSS_PLATFORM_TECHNOLOGY_ANALYSIS.md` | Only Windows Tauri client exists; no RN/Capacitor projects. |

### Core Documents

1. **[ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md](./ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md)**
   - **Purpose**: Main architectural document for enhanced lesson plan generation with RAG and vocabulary module
   - **Key Features**:
     - Google FileSearch RAG integration
     - Vocabulary module with multimedia support
     - Teacher approval workflow
     - Game generation modules (browser games, SCORM packages)
   - **Status**: ✅ Complete
   - **Dependencies**: References DATABASE_ARCHITECTURE_AND_SYNC.md, CONTAINERIZATION_STRATEGY.md, AGENT_SKILLS_AND_CODE_EXECUTION.md

2. **[DATABASE_ARCHITECTURE_AND_SYNC.md](./DATABASE_ARCHITECTURE_AND_SYNC.md)**
   - **Purpose**: Database schema and synchronization strategy (local-first, P2P, cloud backup)
   - **Key Features**:
     - Local-first architecture
     - P2P synchronization (WiFi/Bluetooth)
     - Supabase cloud backup
     - Conflict resolution strategies
   - **Status**: ✅ Complete
   - **Dependencies**: None (foundational document)

3. **[CONTAINERIZATION_STRATEGY.md](./CONTAINERIZATION_STRATEGY.md)**
   - **Purpose**: Docker and Kubernetes evaluation and recommendations
   - **Key Features**:
     - Docker containerization for background workers
     - Kubernetes evaluation (deferred)
     - Worker communication architecture (Redis + Celery)
   - **Status**: ✅ Complete
   - **Dependencies**: References ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md

4. **[AGENT_SKILLS_AND_CODE_EXECUTION.md](./AGENT_SKILLS_AND_CODE_EXECUTION.md)**
   - **Purpose**: How Anthropic's Agent Skills and Code Execution with MCP can optimize workflows
   - **Key Features**:
     - 9 proposed Agent Skills
     - Code execution sandboxing
     - Performance optimization strategies
   - **Status**: ✅ Complete
   - **Dependencies**: References ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md

5. **[CRITICAL_ANALYSIS_RESPONSE.md](./CRITICAL_ANALYSIS_RESPONSE.md)**
   - **Purpose**: Response to critical analysis of the four architecture documents
   - **Key Features**:
     - Addresses security concerns
     - Corrects misunderstandings
     - Provides actionable improvements
   - **Status**: ✅ Complete
   - **Dependencies**: References all four core documents

6. **[LESSON_PLAN_BROWSER_MODULE.md](./LESSON_PLAN_BROWSER_MODULE.md)**
   - **Purpose**: Architecture for schedule-based lesson plan browser/navigation module
   - **Key Features**:
     - Time-aware display (shows current lesson based on schedule)
     - Schedule-based navigation (order varies by day and user)
     - Multiple navigation modes (Schedule, Day, Week, Subject, Slot)
     - Comprehensive filtering system
     - Integration with existing lesson plan data
   - **Status**: ✅ Complete
   - **Dependencies**: References DATABASE_ARCHITECTURE_AND_SYNC.md

7. **[CROSS_PLATFORM_TECHNOLOGY_ANALYSIS.md](./CROSS_PLATFORM_TECHNOLOGY_ANALYSIS.md)**
   - **Purpose**: Technology stack analysis for Windows 11 and Android 16 implementations
   - **Key Features**:
     - Evaluation of cross-platform solutions (Tauri Mobile, React Native, Flutter, Capacitor, KMM)
     - Recommended hybrid approach (Tauri + React Native or Tauri + Capacitor)
     - Code sharing architecture
     - FastAPI backend integration strategy
     - Implementation timeline and migration path
   - **Status**: ✅ Complete
   - **Dependencies**: References LESSON_PLAN_BROWSER_MODULE.md

---

## 🔗 Document Relationships

```
┌─────────────────────────────────────────────────────────────┐
│              DATABASE_ARCHITECTURE_AND_SYNC.md              │
│              (Foundational - No dependencies)                │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│     ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md           │
│     (Main architectural document)                            │
│                                                              │
│     References:                                              │
│     • DATABASE_ARCHITECTURE_AND_SYNC.md                     │
│     • CONTAINERIZATION_STRATEGY.md                          │
│     • AGENT_SKILLS_AND_CODE_EXECUTION.md                    │
└───────┬───────────────────────────────┬─────────────────────┘
        │                               │
        ▼                               ▼
┌──────────────────────────┐  ┌──────────────────────────────┐
│ CONTAINERIZATION_STRATEGY│  │ AGENT_SKILLS_AND_CODE_       │
│ .md                      │  │ EXECUTION.md                 │
│                          │  │                              │
│ References:              │  │ References:                  │
│ • ENHANCED_GENERATION... │  │ • ENHANCED_GENERATION...     │
└──────────────────────────┘  └──────────────────────────────┘
        │                               │
        └───────────────┬───────────────┘
                        ▼
        ┌───────────────────────────────┐
        │ CRITICAL_ANALYSIS_RESPONSE.md │
        │                               │
        │ References all four documents │
        └───────────────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │ LESSON_PLAN_BROWSER_MODULE.md │
        │                               │
        │ References:                   │
        │ • DATABASE_ARCHITECTURE...    │
        └───────────────┬───────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │ CROSS_PLATFORM_TECHNOLOGY_    │
        │ ANALYSIS.md                   │
        │                               │
        │ References:                   │
        │ • LESSON_PLAN_BROWSER...      │
        └───────────────────────────────┘
```

---

## 📋 Implementation Roadmap

### Phase 1: Foundation (Completed ✅)
- [x] Database schema updates (lesson_json column)
- [x] JSON file storage alongside DOCX
- [x] Objectives print module
- [x] Test suite for JSON storage

### Phase 2: Enhanced Generation (Planned – **not started in codebase**)
- [ ] Google FileSearch RAG integration (no `file_search_service.py`, no FileSearch API usage)
- [ ] Document management UI / backend (`userApi` exposes no document endpoints)
- [ ] Query profile system (LLM prompts don’t reference stored profiles)
- [ ] Retrieval storage/auditing tables (missing from `backend/database.py`)

### Phase 3: Vocabulary Module (Planned – **not started**)
- [ ] Vocabulary database schema / APIs (no `vocabulary_items` tables or endpoints)
- [ ] Image collection service (no Unsplash/Pixabay integration)
- [ ] Audio generation (no TTS clients or job workers)
- [ ] Image normalization/cache (absent)
- [ ] Teacher approval workflow UI (no components in `frontend/src/components`)
- [ ] Per-teacher image preferences (store has no related state)

### Phase 4: Game Generation (Planned – **not started**)
- [ ] Browser game modules (matching, crossword, etc.)
- [ ] SCORM 2004 package generation
- [ ] Game configuration UI

### Phase 5: Infrastructure (Planned – **not started**)
- [ ] Docker containerization for workers (only monitoring compose exists)
- [ ] Redis + Celery setup (rate limiter only; no worker queues)
- [ ] Agent Skills implementation (no `skills/` runtime code)
- [ ] Code execution sandboxing (no RestrictedPython or executor service)

### Phase 6: Lesson Plan Browser (Partially implemented)
- [ ] Schedule management (basic CRUD exists in `/api/schedules`, but no versioning UI)
- [ ] Time-based current lesson display (**missing** – no auto-focus on current slot)
- [ ] Schedule order navigation (**missing** – navigation limited to manual week/day/lesson)
- [ ] Multiple navigation modes (**partially** – only week/day/lesson; no subject/slot views)
- [ ] Filtering system (**missing**)
- [x] Lesson plan integration (lesson JSON display available in `LessonDetailView`)

### Phase 7: Sync Architecture (Planned – **not started**)
- [ ] P2P sync implementation
- [ ] Supabase cloud backup beyond manual exports
- [ ] Conflict resolution w/ vector clocks
- [ ] Device pairing and security handshake

---

## 🎯 Missing Documents (To Be Created)

Based on the implementation roadmap, the following documents should be created:

### 1. **IMPLEMENTATION_ROADMAP.md** (Recommended)
   - **Purpose**: Detailed step-by-step implementation plan
   - **Content**:
     - Phase-by-phase breakdown
     - Dependencies between features
     - Resource requirements
     - Timeline estimates
   - **Status**: ⏳ To be created

### 2. **API_SPECIFICATIONS.md** (Recommended)
   - **Purpose**: API endpoint specifications for new features
   - **Content**:
     - Vocabulary API endpoints
     - Document management API
     - Game generation API
     - Request/response schemas
   - **Status**: ⏳ To be created

### 3. **UI_UX_SPECIFICATIONS.md** (Recommended)
   - **Purpose**: UI/UX specifications for new features
   - **Content**:
     - Vocabulary approval interface
     - Document management UI
     - Game configuration UI
     - User flows and wireframes
   - **Status**: ⏳ To be created

### 4. **TESTING_STRATEGY.md** (Recommended)
   - **Purpose**: Testing strategy for new features
   - **Content**:
     - Unit test requirements
     - Integration test scenarios
     - E2E test cases
     - Performance testing
   - **Status**: ⏳ To be created

### 5. **MIGRATION_GUIDE.md** (Recommended)
   - **Purpose**: Guide for migrating existing data to new schema
   - **Content**:
     - Database migration scripts
     - Data transformation steps
     - Rollback procedures
   - **Status**: ⏳ To be created

### 6. **SECURITY_AUDIT.md** (Recommended)
   - **Purpose**: Security considerations for new features
   - **Content**:
     - PII scrubbing requirements
     - API security
     - Image storage security
     - Code execution sandboxing security
   - **Status**: ⏳ To be created (partially covered in CRITICAL_ANALYSIS_RESPONSE.md)

---

## 📖 How to Use These Documents

### For Planning
1. Start with **ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md** for the big picture
2. Review **DATABASE_ARCHITECTURE_AND_SYNC.md** for data storage strategy
3. Check **CONTAINERIZATION_STRATEGY.md** for infrastructure decisions
4. Read **AGENT_SKILLS_AND_CODE_EXECUTION.md** for optimization strategies
5. Review **CRITICAL_ANALYSIS_RESPONSE.md** for security and reliability considerations

### For Implementation
1. Follow the **Implementation Roadmap** (Phase 1 → Phase 6)
2. Reference specific sections in each document as needed
3. Create missing documents as you progress through phases
4. Update this README as new documents are added

### For Review
1. All documents cross-reference each other
2. Use the document relationships diagram to understand dependencies
3. Check **CRITICAL_ANALYSIS_RESPONSE.md** for known issues and improvements

---

## 🔄 Document Status

| Document | Status | Last Updated | Notes |
|----------|--------|--------------|-------|
| ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md | ✅ Complete | 2025-11-XX | Main architectural document |
| DATABASE_ARCHITECTURE_AND_SYNC.md | ✅ Complete | 2025-11-XX | Foundational, includes P2P security |
| CONTAINERIZATION_STRATEGY.md | ✅ Complete | 2025-11-XX | Includes worker architecture |
| AGENT_SKILLS_AND_CODE_EXECUTION.md | ✅ Complete | 2025-11-XX | Includes sandboxing implementation |
| CRITICAL_ANALYSIS_RESPONSE.md | ✅ Complete | 2025-11-XX | Addresses security concerns |
| LESSON_PLAN_BROWSER_MODULE.md | ✅ Complete | 2025-11-XX | Schedule-based navigation |
| CROSS_PLATFORM_TECHNOLOGY_ANALYSIS.md | ✅ Complete | 2025-11-XX | Windows + Android tech stack |
| IMPLEMENTATION_ROADMAP.md | ⏳ To be created | - | Detailed implementation plan |
| API_SPECIFICATIONS.md | ⏳ To be created | - | API endpoint specs |
| UI_UX_SPECIFICATIONS.md | ⏳ To be created | - | UI/UX designs |
| TESTING_STRATEGY.md | ⏳ To be created | - | Testing approach |
| MIGRATION_GUIDE.md | ⏳ To be created | - | Data migration steps |
| SECURITY_AUDIT.md | ⏳ To be created | - | Security considerations |

---

## 📝 Notes

- All documents use relative paths for cross-references (e.g., `./DATABASE_ARCHITECTURE_AND_SYNC.md`)
- Documents are designed to be read in any order, but the recommended order is listed above
- Each document includes a "Related Documents" section for easy navigation
- The **CRITICAL_ANALYSIS_RESPONSE.md** document addresses concerns raised about the initial four documents

---

## 🚀 Next Steps

1. **Review this README** to understand the document structure
2. **Read ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md** for the main architecture
3. **Create missing documents** as needed for your implementation phase
4. **Update this README** when new documents are added or status changes

## Recommended Implementation & Testing Priorities (Updated Nov 2025)
1. **Phase 1 – Foundation & Security**
   - Ship database migrations (Supabase JSONB columns, sync metadata) and P2P pairing/TLS per `DATABASE_ARCHITECTURE_AND_SYNC.md`.
   - Testing: migration dry-runs on SQLite/Supabase, pairing handshake integration tests, lint new schemas.
2. **Phase 2 – RAG Integration**
   - Build `FileSearchService`, retrieval logging tables, and basic document management UI before touching the LLM pipeline.
   - Testing: mock FileSearch responses, fallback cache tests, regression tests for `BatchProcessor`.
3. **Phase 3 – Vocabulary Platform**
   - Add vocabulary tables/APIs, enqueue multimedia workers (image/audio/normalizer), and expose the teacher approval UX.
   - Testing: API contract tests, worker smoke tests, UI approval flows.
4. **Phase 4 – Lesson Plan Browser Enhancements**
   - Implement filters, “current lesson” auto-focus, quick navigation, and integrate schedule versioning; begin React Native prototype.
   - Testing: component/unit tests for new views, end-to-end navigation tests, accessibility checks for Lesson Mode.
5. **Phase 5 – Sync & Infra**
   - Deliver Redis/Celery worker stack, Supabase backup jobs, conflict resolution, and container health checks.
   - Testing: load tests for queue throughput, sync conflict simulations, observability dashboards.
6. **Phase 6 – Advanced Features**
   - Game/SCORM generation, Agent Skills/MCP execution, sandboxed code runner, full mobile parity.
   - Testing: SCORM validator runs, sandbox security tests, mobile device QA.

---

## 📞 Questions?

If you have questions about:
- **Architecture**: See ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md
- **Database/Sync**: See DATABASE_ARCHITECTURE_AND_SYNC.md
- **Infrastructure**: See CONTAINERIZATION_STRATEGY.md
- **Optimization**: See AGENT_SKILLS_AND_CODE_EXECUTION.md
- **Security/Reliability**: See CRITICAL_ANALYSIS_RESPONSE.md


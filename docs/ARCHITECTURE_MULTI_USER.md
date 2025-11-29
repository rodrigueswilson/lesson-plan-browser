# Multi-User System Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Bilingual Lesson Plan Builder             │
│                      Multi-User System v1.0                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                         FRONTEND                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ User Selector│  │ Slot Config  │  │ Batch Process│      │
│  │   (Tauri)    │  │   (React)    │  │   (React)    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/SSE
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      BACKEND API                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              FastAPI (backend/api.py)                 │   │
│  │                                                        │   │
│  │  /api/users          /api/users/{id}/slots           │   │
│  │  /api/users/{id}     /api/slots/{id}                 │   │
│  │  /api/process-week   /api/users/{id}/plans           │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│   DATABASE MODULE        │  │   BATCH PROCESSOR        │
│  (backend/database.py)   │  │ (tools/batch_processor.py│
│                          │  │                          │
│  ┌────────────────────┐  │  │  ┌────────────────────┐ │
│  │ SQLite Database    │  │  │  │ Process User Week  │ │
│  │                    │  │  │  │                    │ │
│  │ • users            │  │  │  │ For each slot:     │ │
│  │ • class_slots      │  │  │  │  1. Parse DOCX     │ │
│  │ • weekly_plans     │  │  │  │  2. Transform LLM  │ │
│  └────────────────────┘  │  │  │  3. Render DOCX    │ │
│                          │  │  │  4. Combine All    │ │
│  CRUD Operations:        │  │  └────────────────────┘ │
│  • create_user()         │  │                          │
│  • get_user_slots()      │  │  Dependencies:           │
│  • create_class_slot()   │  │  • DOCX Parser           │
│  • create_weekly_plan()  │  │  • LLM Service           │
│  • update_weekly_plan()  │  │  • DOCX Renderer         │
└──────────────────────────┘  └──────────────────────────┘
                                            │
                              ┌─────────────┴─────────────┐
                              ▼                           ▼
                    ┌──────────────────┐        ┌──────────────────┐
                    │  DOCX PARSER     │        │   LLM SERVICE    │
                    │ (tools/          │        │ (backend/        │
                    │  docx_parser.py) │        │  llm_service.py) │
                    │                  │        │                  │
                    │ • Parse DOCX     │        │ • OpenAI         │
                    │ • Extract text   │        │ • Anthropic      │
                    │ • Find subjects  │        │ • Mock (testing) │
                    │ • Get components │        │                  │
                    │   - Objectives   │        │ Transform:       │
                    │   - Activities   │        │ Primary → ESL    │
                    │   - Assessments  │        │                  │
                    │   - Materials    │        │ • Add WIDA       │
                    └──────────────────┘        │ • Add strategies │
                                                │ • Bilingual plan │
                                                └──────────────────┘
                                                          │
                                                          ▼
                                                ┌──────────────────┐
                                                │  DOCX RENDERER   │
                                                │ (tools/          │
                                                │  docx_renderer.py│
                                                │                  │
                                                │ • Load template  │
                                                │ • Fill metadata  │
                                                │ • Fill daily     │
                                                │   plans (Mon-Fri)│
                                                │ • Preserve format│
                                                └──────────────────┘
```

## Data Flow

### 1. User Setup (One-Time)

```
User → Create User → Database
                        │
                        ├─ users table
                        │   └─ (id, name, email)
                        │
User → Configure Slots → Database
                        │
                        ├─ class_slots table
                        │   └─ (user_id, slot_number, subject, grade, 
                        │       homeroom, primary_teacher_file)
```

### 2. Weekly Processing

```
User → Select Week → Batch Processor
                          │
                          ├─ Get user's 6 slots from database
                          │
                          ├─ For each slot:
                          │   │
                          │   ├─ DOCX Parser
                          │   │   └─ Extract subject content
                          │   │
                          │   ├─ LLM Service
                          │   │   └─ Transform to bilingual plan
                          │   │
                          │   └─ DOCX Renderer
                          │       └─ Render to temp DOCX
                          │
                          ├─ Combine all temp DOCXs
                          │
                          ├─ Add signature box
                          │
                          └─ Save: {Name}_Lesson plan_W##_{dates}.docx
                              │
                              └─ Update database (weekly_plans table)
```

### 3. History & Retrieval

```
User → View History → Database
                        │
                        └─ weekly_plans table
                            └─ (user_id, week_of, output_file, 
                                status, generated_at)
```

## Database Schema

```sql
┌─────────────────────────────────────────────────────────┐
│                        users                             │
├─────────────────────────────────────────────────────────┤
│ id          TEXT PRIMARY KEY                             │
│ name        TEXT NOT NULL                                │
│ email       TEXT                                         │
│ created_at  TIMESTAMP                                    │
│ updated_at  TIMESTAMP                                    │
└─────────────────────────────────────────────────────────┘
                              │
                              │ 1:N
                              ▼
┌─────────────────────────────────────────────────────────┐
│                     class_slots                          │
├─────────────────────────────────────────────────────────┤
│ id                    TEXT PRIMARY KEY                   │
│ user_id               TEXT FK → users(id)                │
│ slot_number           INTEGER (1-6)                      │
│ subject               TEXT                               │
│ grade                 TEXT                               │
│ homeroom              TEXT                               │
│ proficiency_levels    TEXT (JSON)                        │
│ primary_teacher_file  TEXT                               │
│ created_at            TIMESTAMP                          │
│ updated_at            TIMESTAMP                          │
└─────────────────────────────────────────────────────────┘

                              │
                              │ 1:N
                              ▼
┌─────────────────────────────────────────────────────────┐
│                    weekly_plans                          │
├─────────────────────────────────────────────────────────┤
│ id            TEXT PRIMARY KEY                           │
│ user_id       TEXT FK → users(id)                        │
│ week_of       TEXT (MM/DD-MM/DD)                         │
│ generated_at  TIMESTAMP                                  │
│ output_file   TEXT                                       │
│ status        TEXT (pending|processing|completed|failed) │
│ error_message TEXT                                       │
└─────────────────────────────────────────────────────────┘
```

## File Structure

```
d:\LP\
│
├── backend/
│   ├── api.py              # FastAPI endpoints
│   ├── database.py         # SQLite operations (NEW)
│   ├── models.py           # Pydantic models (UPDATED)
│   ├── llm_service.py      # LLM integration
│   ├── mock_llm_service.py # Mock for testing
│   ├── config.py           # Configuration
│   ├── errors.py           # Error handling
│   └── progress.py         # SSE progress
│
├── tools/
│   ├── docx_parser.py      # Parse primary teacher DOCX (NEW)
│   ├── batch_processor.py  # Multi-slot processing (NEW)
│   ├── docx_renderer.py    # Render to DOCX
│   ├── validate_schema.py  # JSON validation
│   └── json_repair.py      # JSON repair
│
├── tests/
│   ├── test_user_profiles.py  # Database tests (NEW)
│   ├── test_docx_parser.py    # Parser tests (NEW)
│   └── test_llm_workflow.py   # LLM tests
│
├── docs/
│   ├── USER_PROFILE_GUIDE.md  # Multi-user guide (NEW)
│   └── DOCX_PARSER_GUIDE.md   # Parser guide (NEW)
│
├── data/
│   └── lesson_planner.db   # SQLite database (AUTO-CREATED)
│
├── input/
│   ├── Lesson Plan Template SY'25-26.docx  # District template
│   ├── primary_math.docx                    # Primary teacher files
│   ├── primary_science.docx
│   └── ...
│
├── output/
│   └── {Name}_Lesson plan_W##_{dates}.docx  # Generated plans
│
└── test_user_workflow.py   # Integration test (NEW)
```

## API Endpoints

### User Management

```
POST   /api/users              Create user
GET    /api/users              List all users
GET    /api/users/{user_id}    Get user by ID
```

### Class Slots

```
POST   /api/users/{user_id}/slots   Create slot
GET    /api/users/{user_id}/slots   Get user's slots
PUT    /api/slots/{slot_id}          Update slot
DELETE /api/slots/{slot_id}          Delete slot
```

### Weekly Plans

```
GET    /api/users/{user_id}/plans    Get plan history
POST   /api/process-week             Process all slots
```

### Legacy Endpoints (Still Available)

```
GET    /api/health              Health check
POST   /api/validate            Validate JSON
POST   /api/render              Render DOCX
POST   /api/transform           LLM transform
```

## Multi-User Workflow

### Scenario: Two Teachers

```
┌─────────────────────────────────────────────────────────┐
│                    Maria Garcia (User 1)                 │
├─────────────────────────────────────────────────────────┤
│ Slot 1: Math, Grade 6, Room 6A                          │
│ Slot 2: Science, Grade 6, Room 6B                       │
│ Slot 3: ELA, Grade 6, Room 6C                           │
│ Slot 4: Social Studies, Grade 6, Room 6A                │
│ Slot 5: Math, Grade 7, Room 7A                          │
│ Slot 6: Science, Grade 7, Room 7B                       │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
                    Process Week: 10/07-10/11
                              │
                              ▼
        Output: Maria_Garcia_Lesson plan_W06_10-07-10-11.docx

┌─────────────────────────────────────────────────────────┐
│                    John Smith (User 2)                   │
├─────────────────────────────────────────────────────────┤
│ Slot 1: Math, Grade 7, Room 7C                          │
│ Slot 2: Science, Grade 7, Room 7D                       │
│ Slot 3: ELA, Grade 7, Room 7E                           │
│ Slot 4: Social Studies, Grade 7, Room 7C                │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
                    Process Week: 10/07-10/11
                              │
                              ▼
        Output: John_Smith_Lesson plan_W06_10-07-10-11.docx
```

## Processing Pipeline

```
┌─────────────────────────────────────────────────────────┐
│                  BATCH PROCESSING PIPELINE               │
└─────────────────────────────────────────────────────────┘

Input: User ID + Week of (MM/DD-MM/DD)
│
├─ Step 1: Get User & Slots
│   └─ Query database for user's 6 configured slots
│
├─ Step 2: For Each Slot (1-6)
│   │
│   ├─ 2.1: Parse Primary Teacher DOCX
│   │   ├─ Open DOCX file
│   │   ├─ Extract text and tables
│   │   ├─ Find subject section
│   │   ├─ Parse components:
│   │   │   ├─ Objectives
│   │   │   ├─ Activities
│   │   │   ├─ Assessments
│   │   │   └─ Materials
│   │   └─ Return structured content
│   │
│   ├─ 2.2: Transform with LLM
│   │   ├─ Send primary content to LLM
│   │   ├─ Add WIDA standards
│   │   ├─ Add bilingual strategies
│   │   ├─ Generate ESL objectives
│   │   └─ Return lesson JSON
│   │
│   ├─ 2.3: Validate JSON
│   │   └─ Check against schema
│   │
│   └─ 2.4: Render to DOCX
│       ├─ Load district template
│       ├─ Fill metadata
│       ├─ Fill daily plans (Mon-Fri)
│       └─ Save temp DOCX
│
├─ Step 3: Combine All Slots
│   ├─ Load first DOCX
│   ├─ Add page break
│   ├─ Append remaining DOCXs
│   └─ Add signature box
│
├─ Step 4: Save Final Output
│   └─ Filename: {Name}_Lesson plan_W##_{dates}.docx
│
└─ Step 5: Update Database
    └─ Record in weekly_plans table
```

## Error Handling

```
┌─────────────────────────────────────────────────────────┐
│                    ERROR RECOVERY                        │
└─────────────────────────────────────────────────────────┘

Slot Processing Error
│
├─ Log error details
│
├─ Continue with next slot (don't stop batch)
│
├─ Collect all errors
│
└─ At end:
    ├─ If any slots succeeded:
    │   ├─ Generate partial output
    │   └─ Mark as "completed with errors"
    │
    └─ If all slots failed:
        └─ Mark as "failed"

Error Types:
• File not found → Skip slot, continue
• Parse error → Try alternative parsing, continue
• LLM timeout → Retry once, then skip
• Render error → Skip slot, continue
• Combine error → Return individual DOCXs
```

## Performance Characteristics

### Current (Sequential)
- DOCX parsing: ~50ms per file
- LLM transform: 2-3s per slot (real LLM)
- Rendering: ~70ms per slot
- **Total (6 slots): ~15-20s**

### Future (Parallel)
- Parse all DOCXs in parallel: ~50ms total
- Transform all in parallel: ~3s total
- Render all in parallel: ~70ms total
- **Total (6 slots): ~4-5s** ⚡

## Security & Privacy

```
┌─────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                       │
└─────────────────────────────────────────────────────────┘

1. Local-Only Storage
   └─ SQLite database on local machine
   └─ No cloud sync, no network exposure

2. API Key Management
   └─ Stored in OS keychain (not in database)
   └─ Never logged or transmitted

3. PII Scrubbing
   └─ Student names removed before LLM
   └─ Only lesson content sent to API

4. File Access
   └─ Validated file paths
   └─ Sandboxed to input/output directories

5. Database Security
   └─ Foreign key constraints
   └─ Transaction safety
   └─ Backup recommended
```

## Scalability

### Current Capacity
- **Users:** Unlimited (SQLite supports millions)
- **Slots per user:** 6 (configurable)
- **Plans per user:** Unlimited
- **Database size:** ~1KB per plan, ~10MB per year

### Performance Limits
- **Concurrent users:** 1 (desktop app)
- **Batch size:** 6 slots
- **Processing time:** < 30s per batch
- **Memory usage:** < 500MB

---

**Architecture Status:** ✅ Complete and Production Ready

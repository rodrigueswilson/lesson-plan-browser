# Application Workflow Summary

## Overview

The Bilingual Lesson Plan Builder is a desktop application that transforms primary teachers' lesson plans into bilingual (Portuguese-English) weekly plans with WIDA enhancements. Here's how it works from start to finish.

---

## High-Level Workflow

```
1. Setup (One-Time)
   ↓
2. Weekly Processing
   ↓
3. Download & Review
```

---

## Step-by-Step Workflow

### Phase 1: Initial Setup (One-Time Configuration)

#### Step 1.1: Create User Profile
- **What happens**: Teacher creates their profile in the system
- **Data stored**: Name, email, base path to lesson plan folder
- **Database**: Creates a record in the `users` table
- **Example**: Maria Rodriguez creates her profile

#### Step 1.2: Configure Class Slots
- **What happens**: Teacher sets up their class schedule (typically 6 periods per day)
- **For each slot, teacher provides**:
  - Slot number (1-6)
  - Subject (Math, Science, ELA, etc.)
  - Grade level
  - Homeroom/class identifier
  - Primary teacher's name (whose lesson plan they'll use)
  - File pattern to match primary teacher's files
- **Database**: Creates records in the `class_slots` table (one per slot)
- **Example**: Maria configures:
  - Slot 1: Math, Grade 6, Homeroom 6A, Primary Teacher: Ms. Johnson
  - Slot 2: Science, Grade 7, Homeroom 7B, Primary Teacher: Dr. Smith
  - ... (up to 6 slots)

**Result**: The system now knows which classes Maria teaches and where to find the primary teacher's lesson plans.

---

### Phase 2: Weekly Processing (Repeated Each Week)

#### Step 2.1: Select Week
- **What happens**: Teacher selects which week to process (e.g., "Week of 9/15-9/19")
- **System**: Automatically detects available weeks from the lesson plan folder
- **UI**: Teacher picks from a dropdown or calendar

#### Step 2.2: Trigger Batch Processing
- **What happens**: Teacher clicks "Generate Lesson Plans" button
- **System**: 
  - Creates a `weekly_plans` record in database (status: "pending")
  - Begins processing all configured slots

#### Step 2.3: Process Each Slot (Happens for Each Class)

For each of the teacher's slots (e.g., 6 slots), the system:

**A. Parse Primary Teacher's DOCX File**
- **What happens**: System finds and reads the primary teacher's lesson plan file
- **Process**:
  - Searches week folder for matching file (based on file pattern)
  - Extracts content from DOCX (objectives, activities, assessments, etc.)
  - Identifies subject-specific content
  - Handles different DOCX formats (tables, headers, text)
- **Output**: Structured data extracted from the DOCX

**B. Transform with AI (LLM Service)**
- **What happens**: System sends extracted content to AI (OpenAI or Anthropic)
- **AI Enhancement Process**:
  1. Analyzes the primary teacher's lesson plan
  2. Adds bilingual (Portuguese-English) support strategies
  3. Incorporates WIDA 2020 framework elements
  4. Applies research-backed bilingual teaching strategies (33 strategies available)
  5. Adds co-teaching model specifications (6 Friend & Cook models)
  6. Includes proficiency-responsive scaffolding for levels 1-6
  7. Prevents Portuguese→English linguistic misconceptions
  8. Preserves original assessments with WIDA overlay
- **Output**: Enhanced bilingual lesson plan in JSON format
- **Tracking**: Performance metrics recorded (tokens used, cost, time)

**C. Validate JSON**
- **What happens**: System validates the AI-generated JSON against schema
- **Checks**: Required fields, data types, format correctness
- **If invalid**: Attempts JSON repair, retries if needed

**D. Render to DOCX**
- **What happens**: System converts JSON to formatted DOCX document
- **Process**:
  - Loads district template
  - Fills in metadata (teacher names, dates, subject, grade)
  - Populates Monday-Friday plans with bilingual content
  - Preserves template formatting and structure
- **Output**: Temporary DOCX file for this slot

#### Step 2.4: Combine All Slots
- **What happens**: After processing all slots, system combines them into one document
- **Process**:
  - Merges all slot DOCX files
  - Adds signature box
  - Creates final filename: `{TeacherName}_Lesson plan_W##_{dates}.docx`
- **Output**: Single consolidated DOCX file

#### Step 2.5: Save & Update Database
- **What happens**: System saves final file and updates database
- **File location**: Saved to the week folder
- **Database**: Updates `weekly_plans` record:
  - Status: "completed"
  - Output file path
  - Processing time, token usage, cost
- **Performance metrics**: All operation details saved to `performance_metrics` table

#### Step 2.6: Real-Time Progress Updates
- **What happens**: Throughout processing, system sends progress updates via SSE (Server-Sent Events)
- **UI Updates**: Progress bar shows:
  - Which slot is being processed
  - Percentage complete
  - Current operation (parsing, transforming, rendering)
  - Estimated time remaining

---

### Phase 3: Review & Download

#### Step 3.1: View Results
- **What happens**: Teacher sees completed plan in the UI
- **Information shown**:
  - Week processed
  - Status (completed/failed)
  - File location
  - Processing time and cost

#### Step 3.2: Download/Open File
- **What happens**: Teacher can download or open the generated DOCX
- **File contains**:
  - All 5 days (Monday-Friday) for all configured slots
  - Bilingual support strategies
  - WIDA language objectives
  - Co-teaching model details
  - Proficiency-responsive scaffolding

#### Step 3.3: Review History
- **What happens**: Teacher can view past generated plans
- **Database**: Queries `weekly_plans` table filtered by user_id
- **Shows**: Recent weeks, status, dates

---

## Data Flow Diagram

```
┌─────────────┐
│   Teacher   │
│   (User)    │
└──────┬──────┘
       │
       │ 1. Create Profile
       ▼
┌──────────────────┐
│   Database       │
│   (users table)  │
└──────┬───────────┘
       │
       │ 2. Configure Slots
       ▼
┌──────────────────┐
│   Database       │
│ (class_slots)    │
└──────┬───────────┘
       │
       │ 3. Select Week & Process
       ▼
┌──────────────────┐
│ Batch Processor  │
└──────┬───────────┘
       │
       ├─► Parse DOCX
       │   └─► Extract content
       │
       ├─► LLM Transform
       │   └─► Enhance with bilingual strategies
       │
       ├─► Validate JSON
       │   └─► Check schema
       │
       ├─► Render DOCX
       │   └─► Fill template
       │
       └─► Combine & Save
           │
           ▼
┌──────────────────┐
│   Database       │
│ (weekly_plans +  │
│ performance_     │
│  metrics)        │
└──────────────────┘
```

---

## Key Components & Their Roles

### Frontend (Tauri + React)
- **User interface**: Displays forms, progress bars, file lists
- **User actions**: Create profile, configure slots, trigger processing
- **Progress display**: Shows real-time updates via SSE

### Backend API (FastAPI)
- **REST endpoints**: Handle HTTP requests from frontend
- **SSE streaming**: Sends progress updates to frontend
- **Orchestration**: Coordinates all processing steps

### Database (SQLite)
- **User data**: Stores profiles and configurations
- **Processing history**: Tracks all generated plans
- **Performance tracking**: Records metrics for analysis

### Batch Processor
- **Orchestration**: Manages the entire weekly processing workflow
- **Slot iteration**: Processes each slot sequentially
- **Error handling**: Manages failures and retries

### DOCX Parser
- **File reading**: Extracts content from primary teacher's DOCX
- **Format handling**: Supports multiple DOCX structures
- **Content extraction**: Identifies lesson components

### LLM Service
- **AI integration**: Connects to OpenAI/Anthropic APIs
- **Transformation**: Converts primary plans to bilingual plans
- **Strategy application**: Applies research-backed strategies

### DOCX Renderer
- **Template loading**: Uses district template
- **Content filling**: Populates template with enhanced content
- **Format preservation**: Maintains original formatting

---

## Example: Complete Workflow

**Scenario**: Maria Rodriguez wants to generate plans for Week of September 15-19, 2025

### Monday Morning:
1. Maria opens the app
2. Selects "Week of 9/15-9/19" from dropdown
3. Clicks "Generate Lesson Plans"
4. Progress bar shows: "Processing Slot 1/6: Math, Grade 6..."

### During Processing:
1. **Slot 1 (Math)**: 
   - Parses Ms. Johnson's Math plan
   - Transforms with AI (adds bilingual strategies)
   - Renders to DOCX
   - Progress: 16% complete

2. **Slot 2 (Science)**:
   - Parses Dr. Smith's Science plan
   - Transforms with AI
   - Renders to DOCX
   - Progress: 33% complete

3. ... (continues for all 6 slots)

4. **Final Step**:
   - Combines all 6 DOCX files
   - Adds signature box
   - Saves: `Rodriguez_Lesson plan_W38_09-15-09-19.docx`
   - Progress: 100% complete

### Tuesday Morning:
- Maria reviews the generated plan
- Opens the DOCX file
- Sees all 5 days with bilingual enhancements
- Uses it for her co-teaching sessions

---

## Important Concepts

### Multi-User Support
- Each teacher has their own profile and configurations
- Database keeps data separate by user_id
- Teachers can't see each other's plans

### Week Folder Organization
- System organizes files by week folders
- Each week folder contains:
  - Primary teacher's original DOCX files
  - Generated bilingual lesson plan DOCX
  - Extracted JSON data (optional)

### Real-Time Progress
- SSE (Server-Sent Events) provides live updates
- Teacher sees exactly what's happening
- No need to refresh or wait blindly

### Error Handling
- If a slot fails, system continues with other slots
- Failed slots are logged with error messages
- Teacher can retry specific slots

### Performance Tracking
- Every operation is tracked
- Metrics include: time, tokens, cost
- Useful for optimization and cost analysis

---

## Summary

**Simple Flow**:
1. **Setup** → Create profile, configure class slots (one time)
2. **Generate** → Select week, click process, wait for completion
3. **Use** → Download and use the bilingual lesson plan

**Technical Flow**:
1. **Parse** → Extract content from primary teacher's DOCX
2. **Transform** → Enhance with AI (bilingual strategies, WIDA)
3. **Validate** → Check JSON structure
4. **Render** → Convert to formatted DOCX
5. **Combine** → Merge all slots into one document
6. **Save** → Store file and update database

The entire process typically takes **under 10 minutes** for a full week with 6 slots, with most time spent on AI transformation steps.


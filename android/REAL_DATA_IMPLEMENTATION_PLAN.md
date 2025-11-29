# Real Data Implementation Assessment & Plan

## Current Status Assessment

### ✅ What's Already Implemented

1. **Infrastructure (Complete)**
   - ✅ Supabase connection configured (Project 1 & Project 2)
   - ✅ Room database (local storage)
   - ✅ SyncManager with network-aware sync
   - ✅ RemotePlanRepository (fetches from Supabase)
   - ✅ LocalPlanRepository (stores in Room)
   - ✅ Data models (WeeklyPlan, LessonStep, ScheduleEntry, User)
   - ✅ Mappers (Entity ↔ Domain)

2. **UI Components (Complete)**
   - ✅ Browser views (Week/Day/Lesson)
   - ✅ Lesson Detail View
   - ✅ Lesson Mode with Timer
   - ✅ Resource displays (Vocabulary, Sentence Frames, Materials)

3. **Data Flow (Partially Working)**
   - ✅ Sync triggers (manual refresh, background worker)
   - ✅ Sample data fallback (for testing)
   - ⚠️ **Real data sync works, but needs verification**

### ❌ What's Missing or Needs Fixing

1. **Real Data Access Issues**
   - ❌ **Supabase tables may be empty** (users, weekly_plans, lesson_steps, schedule_entries)
   - ❌ **RLS (Row Level Security) policies** may be blocking anonymous access
   - ❌ **lesson_json parsing** - Currently stored but not parsed/displayed
   - ❌ **Data verification** - No way to confirm real data is flowing through

2. **lesson_json Field Not Utilized**
   - The `lesson_json` field in `weekly_plans` table contains structured lesson data
   - Currently only checking if it exists, but not parsing it
   - Need to parse JSON and extract:
     - Objectives
     - Vocabulary
     - Sentence frames
     - Materials
     - Instruction steps

3. **Testing & Verification**
   - No diagnostic tools to check Supabase connection
   - No way to see what data is actually in the database
   - Sample data masks real data issues

---

## Implementation Plan: Real Data Access

### Phase 1: Data Verification & Diagnostics (Priority: HIGH) ✅ COMPLETE

**Goal**: Verify Supabase connection and data availability

**Tasks**:
1. ✅ **Create Diagnostic Screen**
   - Created `DataDiagnosticsScreen` accessible from BrowserScreen (bug icon)
   - Displays:
     - Table row counts (users, plans, steps, schedule)
     - Sample data from each table
     - lesson_json preview (first 200 chars)
     - Plan details (ID, weekOf, status)

2. ✅ **Enhanced Logging**
   - Added detailed logging in `SyncManager`:
     - What data is fetched from Supabase (counts, samples)
     - What data is saved locally
     - Error details with type and message
     - Warnings for empty results with possible causes

3. ✅ **Navigation Integration**
   - Added diagnostic screen to navigation
   - Added bug icon button in BrowserScreen top bar
   - Accessible when user is selected

**Deliverables**:
- ✅ Diagnostic screen showing data status
- ✅ Enhanced logging for data flow
- ✅ Navigation to diagnostic screen

---

### Phase 2: Fix RLS & Data Access (Priority: HIGH)

**Goal**: Ensure the app can read data from Supabase

**Tasks**:
1. **RLS Policy Check**
   - Document current RLS policies in Supabase
   - Identify if anonymous access is allowed
   - If not, either:
     - Update RLS policies to allow SELECT for authenticated/anonymous users
     - OR implement proper authentication (if needed)

2. **Data Population Verification**
   - Check if Supabase tables have data:
     - `users` table
     - `weekly_plans` table
     - `lesson_steps` table
     - `schedule_entries` table
   - If empty, document how to populate them

3. **Error Handling**
   - Better error messages when data is empty
   - Distinguish between:
     - Connection errors
     - Empty tables
     - RLS policy errors
     - Network errors

**Deliverables**:
- RLS policies documented/updated
- Data population guide
- Improved error handling

---

### Phase 3: Parse & Display lesson_json (Priority: MEDIUM)

**Goal**: Extract and display content from lesson_json field

**Tasks**:
1. **Create LessonJsonParser**
   - Parse the JSON structure from `lesson_json` field
   - Extract:
     - Objectives (content + language)
     - Vocabulary & cognates
     - Sentence frames
     - Materials needed
     - Instruction steps (if not in lesson_steps table)
   - Handle both formats (if structure varies)

2. **Update LessonDetailView**
   - Use parsed lesson_json data
   - Fallback to lesson_steps table if lesson_json is null
   - Display all sections from JSON

3. **Update LessonModeScreen**
   - Use parsed lesson_json for step content
   - Ensure timer and adjustment work with real data

**Deliverables**:
- LessonJsonParser utility
- Updated UI to display parsed JSON content
- Fallback logic for missing data

---

### Phase 4: Data Sync Verification (Priority: MEDIUM)

**Goal**: Ensure data flows correctly from Supabase → Local → UI

**Tasks**:
1. **Sync Flow Testing**
   - Test full sync cycle:
     - Fetch from Supabase
     - Save to Room
     - Read from Room
     - Display in UI
   - Verify data integrity at each step

2. **Incremental Sync Testing**
   - Test timestamp-based incremental sync
   - Verify only updated records are fetched
   - Test sync metadata tracking

3. **Offline Testing**
   - Verify app works with cached data
   - Test sync when network becomes available
   - Verify data persistence across app restarts

**Deliverables**:
- Verified sync flow
- Tested offline functionality
- Data integrity confirmed

---

### Phase 5: Remove Sample Data Fallback (Priority: LOW)

**Goal**: Remove test data once real data is confirmed working

**Tasks**:
1. **Conditional Sample Data**
   - Only generate sample data in DEBUG builds
   - Remove from RELEASE builds
   - Add flag to disable sample data

2. **Better Empty States**
   - Show helpful messages when no data
   - Guide users on how to populate data
   - Link to documentation

**Deliverables**:
- Sample data only in debug mode
- Improved empty state messages

---

## Implementation Strategy

### Step 1: Immediate Actions (This Session)

1. **Create Diagnostic Tools**
   - Add logging to see what's being fetched
   - Create a simple data status display

2. **Verify Supabase Connection**
   - Test if we can actually read from Supabase
   - Check what data exists in tables

3. **Document Current State**
   - What data is in Supabase?
   - What RLS policies exist?
   - What's the structure of lesson_json?

### Step 2: Fix Data Access (Next Session)

1. **Fix RLS or Authentication**
2. **Populate test data if needed**
3. **Verify data flow**

### Step 3: Parse lesson_json (Following Session)

1. **Understand JSON structure**
2. **Create parser**
3. **Update UI to use parsed data**

---

## Questions to Answer

1. **Does Supabase have real data?**
   - Check `weekly_plans` table
   - Check `lesson_steps` table
   - Check `schedule_entries` table

2. **What's the structure of lesson_json?**
   - Is it a JSON object?
   - What fields does it contain?
   - How does it relate to lesson_steps?

3. **Are RLS policies blocking access?**
   - Can anonymous users SELECT?
   - Do we need authentication?

4. **How is data populated in Supabase?**
   - Is there a script or process?
   - Is it manual?
   - Is it from the PC app?

---

## Next Steps

**Immediate**: Create diagnostic tools to assess current state
**Short-term**: Fix data access issues (RLS, connection)
**Medium-term**: Parse and display lesson_json
**Long-term**: Remove sample data, optimize sync


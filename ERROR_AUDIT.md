# Error Audit Report
Generated during app runtime monitoring

## Status
- **Audit Start Time**: 2025-12-07 18:29:00
- **Backend Status**: ✅ Running (PID 34028, port 8000)
- **Frontend Status**: ✅ Running (multiple Node processes active)
- **Active Connections**: Multiple ESTABLISHED connections between frontend and backend
- **Current Status**: ✅ **ALL FIXES COMPLETED AND TESTED**
- **Fix Completion Date**: 2025-12-07

## Identified Errors and Issues

### 1. Database Table Missing Warnings (Backend)
**Location**: `backend/supabase_database.py` and `backend/api.py`

**Missing Tables**:
1. **`lesson_steps`** - Stores lesson step data (vocabulary, sentence frames, materials, etc.)
2. **`lesson_mode_sessions`** - Stores lesson mode session data (active sessions, timing adjustments, etc.)

**Issue**: 
- Multiple warnings logged about missing database tables:
  - `lesson_steps_table_missing`
  - `lesson_steps_table_missing_for_create`
  - `lesson_steps_table_missing_for_delete`
  - `lesson_mode_sessions_table_missing`

**Details**:
- These warnings appear when using Supabase database and the tables don't exist
- The code handles this gracefully by returning empty lists or None, but the warnings are logged repeatedly
- SQL creation scripts exist but haven't been run:
  - `sql/create_lesson_steps_table_supabase.sql`
  - `sql/create_lesson_mode_sessions_table_supabase.sql`
- This happens in multiple locations:
  - `supabase_database.py` lines 1158, 1200, 1243, 1285, 1321, 1371
  - `api.py` line 2339

**Impact**: 
- **`lesson_steps`**: Steps are stored in memory instead of database (data lost on restart)
- **`lesson_mode_sessions`**: Session tracking functionality doesn't work
- Non-critical - functionality degrades gracefully, but features are limited
- Excessive logging can clutter logs and make debugging harder
- Indicates database schema not properly initialized in Supabase

**Recommendation**: 
- Run the SQL creation scripts in Supabase to create the missing tables
- Ensure database tables are created during initialization
- Consider reducing log level for expected missing table scenarios
- Add table existence check before operations

---

## Runtime Errors (To be populated during lesson plan generation)

### Backend Runtime Errors
**Status**: No new runtime errors detected during monitoring
- Backend health check: ✅ Healthy (200 OK)
- Server process: ✅ Running successfully
- Error log monitoring: Active, no new errors detected

### Frontend Runtime Errors  
**Status**: Monitoring in progress
- Frontend processes: ✅ Active (multiple Node processes)
- Backend connections: ✅ Multiple ESTABLISHED connections
- No connection errors detected

### Lesson Plan Generation Errors
**Status**: ✅ Generation completed - CRITICAL ERROR FOUND

**CRITICAL ERROR IDENTIFIED**:
1. **ModelPrivateAttr Not Iterable Error** (CRITICAL - Generation Failed)
   - **Error Message**: `"Slot 6 (Science): argument of type 'ModelPrivateAttr' is not iterable"`
   - **Location**: `backend/models_slot.py` line 190
   - **Impact**: ⚠️ **CRITICAL** - Batch processing failed, lesson plan generation did not complete successfully
   - **Details**: 
     - Error occurred during batch processing of Slot 6 (Science)
     - The code attempts to check `domain not in allowed_domains` where `allowed_domains` is a ModelPrivateAttr instead of a set
     - There are checks for ModelPrivateAttr at line 186, but they may not be working correctly
     - The validation code has fallback logic, but it's not being triggered properly
   - **Root Cause**: Pydantic ModelPrivateAttr is being used in an `in` operator check, which requires an iterable
   - **Status**: Generation failed with 0 successful slots out of 1 attempted

**Other Issues Identified**:
1. **Slot Matching Logic** (lines 2632-2669 in `api.py`):
   - If requested slot number doesn't match, code falls back to first slot
   - This could silently use wrong slot data
   - Warning is logged but may not be visible to user
   
2. **Vocabulary Cognates Missing Warning** (lines 2677-2696):
   - Code checks for `vocabulary_cognates` and logs warnings if missing
   - Suggests plan may need regeneration
   - This is informational, not an error, but indicates potential data completeness issues

---

## Additional Observations

### 2. Potential Database Initialization Issue
**Location**: `backend/api.py` startup event (lines 142-161)

**Issue**:
- Startup event catches exceptions but doesn't raise them, allowing app to start even if database initialization fails
- This could lead to runtime errors when database operations are attempted

**Details**:
- The startup handler uses `get_db()` which may fail if database schema is not properly initialized
- Errors are logged but app continues to start, which could mask critical issues

**Impact**: 
- Medium - App may start but fail on first database operation
- Could lead to confusing error messages for users

**Recommendation**:
- Consider making database initialization failure a startup blocker for critical operations
- Or ensure graceful degradation with clear error messages

### 3. Error Handling in Supabase Database Operations
**Location**: `backend/supabase_database.py`

**Issue**:
- Multiple database operations catch `APIError` and check for missing tables
- When tables are missing, operations return empty results or None instead of raising errors
- This silent degradation may hide real issues

**Details**:
- `create_lesson_step()` raises `LessonStepsTableMissingError` when table is missing
- `get_lesson_steps()` returns empty list when table is missing
- `create_lesson_mode_session()` returns None when table is missing
- Inconsistent error handling patterns

**Impact**:
- Medium - Operations may appear to succeed but actually fail silently
- Could lead to data loss or inconsistent state

**Recommendation**:
- Standardize error handling for missing tables
- Consider auto-creating tables if they don't exist
- Or provide clear error messages to users when tables are missing

---

## Notes
- ✅ All errors have been identified and fixed
- ✅ All fixes have been tested and verified
- ✅ See `FIXES_SUMMARY.md` for complete details on all fixes
- ⚠️ Manual action required: Create missing database tables in Supabase (see SQL scripts in `sql/` directory)

## Fix Status Summary
- ✅ **CRITICAL**: ModelPrivateAttr error - FIXED (11 tests passing)
- ✅ **HIGH**: Slot matching logic - FIXED
- ✅ **MEDIUM**: Error handling standardization - FIXED
- ✅ **MEDIUM**: Database initialization - IMPROVED
- ✅ **LOW**: Vocabulary warning levels - ADJUSTED
- ⚠️ **MANUAL**: Database tables - SQL scripts ready, needs manual execution


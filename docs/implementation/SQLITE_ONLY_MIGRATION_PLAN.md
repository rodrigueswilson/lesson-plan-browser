# SQLite-Only Migration Plan

**Goal:** Remove redundant JSON file storage and use SQLite database `lesson_json` column as single source of truth.

**Status:** ✅ Complete  
**Date:** 2025-01-27  
**Completed:** 2025-01-27

---

## Overview

Currently, the system stores lesson plans in two places:
1. **SQLite database** - `weekly_plans.lesson_json` column (TEXT/JSONB)
2. **JSON files** - Written to disk alongside DOCX files (redundant)

**Migration Goal:** Eliminate JSON files, use database only.

---

## PC App Implementation

### Phase 1: Remove JSON File Writing (1-2 hours)

**Files to Modify:**
- `tools/batch_processor.py`

**Changes:**
1. **Remove JSON file writing** (lines 2273-2279, 2671-2677)
   - Delete: `json_path = Path(output_path).with_suffix(".json")`
   - Delete: `json.dump(lesson_json, f, indent=2, ensure_ascii=False)`
   - Keep: Database update with `lesson_json`

2. **Ensure database always has lesson_json**
   - Verify `update_weekly_plan()` is called with `lesson_json` parameter
   - Add logging if `lesson_json` is None

**Testing:**
- Generate new lesson plan
- Verify `lesson_json` exists in database
- Verify no `.json` file created
- Verify PDF generation still works (objectives, sentence frames)

---

### Phase 2: Update Week Detection (1-2 hours)

**Files to Modify:**
- `backend/api.py` (endpoint: `/api/recent-weeks`)
- `backend/week_detector.py` (optional - can be deprecated)

**Changes:**
1. **Replace file system scan with database query**
   ```python
   # Current: Scans file system folders
   # New: Query database
   SELECT DISTINCT week_of 
   FROM weekly_plans 
   WHERE user_id = ? 
   AND week_of IS NOT NULL
   ORDER BY week_of DESC 
   LIMIT ?
   ```

2. **Update `get_recent_weeks()` endpoint**
   - Remove `detect_weeks_from_folder()` call
   - Add database query via `database.get_user_plans()`
   - Format response same as before

3. **Deprecate `week_detector.py`** (optional)
   - Mark as deprecated
   - Can be removed in future cleanup

**Testing:**
- Call `/api/recent-weeks` endpoint
- Verify returns weeks from database
- Verify no file system access
- Verify frontend week selector still works

---

### Phase 3: Verify PDF Generation (30 minutes)

**Files to Check:**
- `backend/services/objectives_pdf_generator.py`
- `backend/services/sentence_frames_pdf_generator.py`

**Verification:**
- Both generators already read from database `lesson_json`
- No changes needed
- Test to confirm they work with database-only data

**Testing:**
- Generate objectives PDF
- Generate sentence frames PDF
- Verify both work correctly

---

### Phase 4: Data Migration (Optional - 1-2 hours)

**If needed:** Populate `lesson_json` for existing plans that have NULL values.

**Script:** `tools/migrate_json_files_to_database.py` (create if needed)

**Process:**
1. Scan existing JSON files in output directories
2. Match JSON files to database records (by `week_of`, `user_id`)
3. Read JSON file content
4. Update database: `UPDATE weekly_plans SET lesson_json = ? WHERE id = ?`
5. Log migrated plans

**Testing:**
- Run migration script
- Verify old plans now have `lesson_json` populated
- Verify browser can display old plans

---

## Android App Implementation

### Phase 1: Remove JSON File Fallbacks (2-3 hours)

**Files to Modify:**
- `shared/lesson-api/src/index.ts`

**Changes:**

1. **Remove `getRecentWeeksFromLocalFiles()` fallback** (lines 912-915)
   ```typescript
   // DELETE THIS BLOCK:
   if (isStandaloneMode()) {
     const fileWeeks = await getRecentWeeksFromLocalFiles(userId, limit);
     fileWeeks.forEach(pushWeek);
   }
   ```
   - Database query already exists (lines 885-910)
   - Just remove the file fallback

2. **Remove JSON file fallback in `getPlanDetail()`** (lines 1343-1348)
   ```typescript
   // DELETE THIS BLOCK:
   if (!lessonJson) {
     const storedLesson = await readLessonPlanFromStorage(row.user_id, row.week_of, row.id);
     if (storedLesson) {
       lessonJson = storedLesson;
     }
   }
   ```
   - If `lesson_json` is null, return error or empty object
   - Don't fall back to JSON files

3. **Update `cacheLessonPlanDetailLocally()`** (lines 1274-1288)
   - Instead of writing JSON file, ensure database has `lesson_json`
   - Use `upsertWeeklyPlanRecord()` with `lesson_json` populated

**Testing:**
- Test week detection in standalone mode
- Test plan detail loading in standalone mode
- Verify no file system access
- Verify error handling when `lesson_json` is null

---

### Phase 2: Update Sync Mechanism (3-4 hours)

**Files to Modify:**
- Rust backend: `lesson-plan-browser/frontend/src-tauri/src/db_commands.rs` (or sync implementation)
- `shared/lesson-api/src/index.ts` (sync-related functions)

**Changes:**

1. **Update WiFi Sync**
   - Current: Downloads JSON files → Writes to disk
   - New: Fetch `lesson_json` from PC → Save to database
   ```rust
   // Instead of: write_json_file(path, content)
   // Do: UPDATE weekly_plans SET lesson_json = ? WHERE id = ?
   ```

2. **Update USB Sync**
   - Current: Import JSON files from USB
   - New: Import database file directly (or sync database records)

3. **Remove JSON file operations from sync**
   - Remove `write_json_file()` calls
   - Remove `read_json_file()` calls
   - Use database operations only

**Testing:**
- Test WiFi sync from PC to tablet
- Verify plans appear in tablet database
- Verify no JSON files created
- Test USB sync (if implemented)
- Test offline operation after sync

---

### Phase 3: Deprecate JSON File Commands (30 minutes)

**Files to Modify:**
- `lesson-plan-browser/frontend/src-tauri/src/db_commands.rs`

**Changes:**
1. **Mark as deprecated** (don't delete yet - for migration period)
   ```rust
   #[deprecated(note = "Use database lesson_json column instead")]
   pub async fn read_json_file(...) { ... }
   
   #[deprecated(note = "Use database lesson_json column instead")]
   pub async fn write_json_file(...) { ... }
   
   #[deprecated(note = "Use database query instead")]
   pub async fn list_json_files(...) { ... }
   ```

2. **Remove from exports** (after migration complete)
   - Remove from `main.rs` and `lib.rs` command lists
   - Delete function implementations

**Testing:**
- Verify deprecated warnings appear if commands are called
- Verify app still works without these commands

---

### Phase 4: Remove Unused Functions (1 hour)

**Files to Modify:**
- `shared/lesson-api/src/index.ts`

**Changes:**
1. **Remove unused functions:**
   - `listStoredLessonPlanFiles()` (line 183)
   - `readLessonPlanFile()` (line 204)
   - `writeLessonPlanFile()` (line 226)
   - `readLessonPlanFromStorage()` (line 1291)
   - `getRecentWeeksFromLocalFiles()` (line 496)
   - `buildLessonPlanFileName()` (line 249)
   - `parseLessonPlanFileName()` (line 255)

2. **Clean up imports:**
   - Remove unused Tauri API imports related to file operations

**Testing:**
- Verify no compilation errors
- Verify app builds successfully
- Verify all functionality still works

---

## Implementation Order

### Week 1: PC App
1. ✅ Phase 1: Remove JSON file writing - **COMPLETE**
2. ✅ Phase 2: Update week detection - **COMPLETE**
3. ✅ Phase 3: Verify PDF generation - **COMPLETE**
4. ⏭️ Phase 4: Data migration (optional - skipped)

### Week 2: Android App
1. ✅ Phase 1: Remove JSON file fallbacks - **COMPLETE**
2. ✅ Phase 2: Update sync mechanism - **COMPLETE** (core JSON operations removed)
3. ✅ Phase 3: Deprecate JSON file commands - **COMPLETE**
4. ✅ Phase 4: Remove unused functions - **COMPLETE**

**Testing Status:**
- ✅ PC App Backend: Working correctly
- ✅ PC App Frontend: Working correctly
- ✅ Android App: Working correctly (standalone mode with database)

---

## Testing Checklist

### PC App Testing
- [x] Generate new lesson plan → Verify no JSON file created ✅
- [x] Verify `lesson_json` in database is populated ✅
- [x] Test `/api/recent-weeks` → Returns weeks from database ✅
- [x] Test objectives PDF generation → Works correctly ✅
- [x] Test sentence frames PDF generation → Works correctly ✅
- [x] Test lesson plan browser → Displays plans correctly ✅
- [x] Test lesson steps generation → Works correctly ✅

### Android App Testing
- [x] Test week detection in standalone mode → Uses database ✅
- [x] Test plan detail loading → Uses database `lesson_json` ✅
- [x] Test WiFi sync → Saves to database, not files ✅
- [x] Test offline operation → Works without network ✅
- [x] Test error handling → Graceful when `lesson_json` is null ✅
- [x] Test app build → No compilation errors ✅

---

## Rollback Plan

If issues arise:

1. **PC App:**
   - Re-enable JSON file writing in `batch_processor.py`
   - Revert week detection to file system scan
   - No data loss (database still has `lesson_json`)

2. **Android App:**
   - Re-enable JSON file fallbacks
   - Revert sync to write JSON files
   - No data loss (database still has `lesson_json`)

**Note:** Since database already has `lesson_json`, rollback is safe and doesn't lose data.

---

## Success Criteria

✅ **PC App:**
- No JSON files written to disk
- All week detection uses database
- All PDF generation works
- All features work as before

✅ **Android App:**
- No JSON file fallbacks
- Sync saves to database only
- Offline operation works
- All features work as before

---

## Estimated Total Time

- **PC App:** 4-6 hours
- **Android App:** 6-9 hours
- **Total:** 10-15 hours

---

## Notes

- Database `lesson_json` column already exists and is populated
- JSON files are redundant - not actively used by application
- Migration is low-risk (can rollback easily)
- Benefits: Simpler architecture, better performance, easier sync

---

**Last Updated:** 2025-01-27  
**Status:** ✅ **COMPLETE - All systems tested and working perfectly**

**Summary:**
- PC App (Backend & Frontend): ✅ **Tested and working perfectly**
- Android App (Standalone): ✅ **Tested and working perfectly**
- SQLite-only storage: ✅ **Working perfectly on both platforms**
- No JSON files written or read
- Database `lesson_json` column is single source of truth
- All fallbacks removed
- All unused functions removed

**Testing Confirmation:**
- ✅ Both PC and Android platforms tested
- ✅ SQLite-only implementation verified working perfectly
- ✅ No issues reported


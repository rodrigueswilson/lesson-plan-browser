# Continue: Lesson Mode Content Fix

## Context
This document provides instructions for continuing the fix for missing Vocabulary and Sentence Frames content in Lesson Mode.

## Problem Summary
Vocabulary and Sentence Frames were not appearing in Lesson Mode for Wilson Rodrigues, Monday, Slot 1, despite the data existing in the `lesson_json` field of the `weekly_plans` table.

## Root Cause Identified
The `lesson_steps` table in `data/lesson_planner.db` was missing two critical columns:
- `vocabulary_cognates` (JSON)
- `sentence_frames` (JSON)

This caused structured data to be lost when lesson steps were generated and saved to the database.

## Work Completed

### 1. Database Schema Fix ✅
- Created migration script: `scripts/add_missing_columns.py`
- Successfully added `vocabulary_cognates` column to `lesson_steps` table
- The `sentence_frames` column already existed

### 2. Backend Code Update ✅
- Modified `backend/api.py` in the `generate_lesson_steps` endpoint (around line 2808)
- Updated sentence frames step creation to include a robust fallback in `display_content`
- The fallback combines strategy text with the actual frames list for better display
- Added debug logging to track vocabulary and sentence frames counts

### 3. Scripts Created ✅
- `scripts/add_missing_columns.py` - Database migration
- `scripts/regenerate_steps.py` - API call to regenerate steps
- `scripts/verify_db_content.py` - Verify database content

## Current Status
The backend server has been restarted (there are now 2 instances running). The code changes have been applied but **verification is incomplete**.

## Next Steps for Continuation

### Step 1: Clean Up Running Processes
There are currently 2 backend server instances running. Kill the older one:
```powershell
# Check which processes are running on port 8000
Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess
# Kill the older process (the one running for 23m34s)
Stop-Process -Id <PID>
```

### Step 2: Verify Backend is Running with New Code
```bash
# Check the logs to confirm the server loaded the updated code
Get-Content -Tail 50 d:\LP\backend_debug.log
# Look for the "DEBUG: Generating steps..." message
```

### Step 3: Regenerate Lesson Steps
```bash
cd d:\LP
python scripts/regenerate_steps.py
```

### Step 4: Verify Database Content
```bash
python scripts/verify_db_content.py
```

Expected output should show:
- `vocabulary_cognates` column populated with JSON array (6 items)
- `sentence_frames` column populated with JSON array (8 items)
- `display_content` for sentence frames should include both strategy text AND the frames list

### Step 5: Test in Browser
1. Navigate to `http://localhost:1420/`
2. Select user "Wilson Rodrigues"
3. Navigate to Lesson Mode for Monday, Slot 1
4. Verify that:
   - "Vocabulary" section appears and shows 6 vocabulary items
   - "Sentence Frames" section appears and shows 8 sentence frames

## Key Files Modified
- `backend/api.py` (lines 2740-2830) - Added debug logging and improved fallback
- `backend/schema.py` - Already had `vocabulary_cognates` and `sentence_frames` columns defined
- `data/lesson_planner.db` - Schema updated with migration

## Important Notes
- The `lesson_json` in `weekly_plans` table DOES contain the correct data (verified)
- The issue was purely in the `lesson_steps` table schema
- The frontend components (`VocabularyDisplay.tsx`, `SentenceFramesDisplay.tsx`) are working correctly
- Plan ID for testing: `plan_20251122160826`

## Troubleshooting

### If vocabulary_cognates is still NULL in DB:
Check if the `LessonStep` model in `backend/schema.py` properly defines the column with `sa_column=Column(JSON)`.

### If sentence frames display_content is empty:
The code update in `backend/api.py` should have fixed this. Verify the changes were applied around line 2808-2830.

### If frontend still shows nothing:
1. Check browser console for errors
2. Verify the API response includes the structured data
3. Check that `VocabularyDisplay` and `SentenceFramesDisplay` components can parse the data

## Reference
- Implementation Plan: `C:\Users\rodri\.gemini\antigravity\brain\05c3ec32-a0ca-410d-95e5-70c75d2aba07\implementation_plan.md`
- Task List: `C:\Users\rodri\.gemini\antigravity\brain\05c3ec32-a0ca-410d-95e5-70c75d2aba07\task.md`

# Bug Fix: File Download Returns 404 - Path Issue

## Problem

File download in Plan History opened a new page with:
```json
{"detail":"Not Found"}
```

**Root Cause:**
The `output_file` field contains a full path (e.g., `F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W41\Wilson_Rodrigues_Lesson_plan_W01_10-06-10-10.docx`), but the `/api/render/{filename}` endpoint only looks for files in the `output/` directory using just the filename.

## Solution

Created a new endpoint `/api/plans/{plan_id}/download` that:
1. Gets the plan from database by ID
2. Verifies user authorization
3. Uses the stored `output_file` path (full path)
4. Serves the file from its actual location

This is safer than allowing arbitrary file paths and properly handles the full path format.

## Changes Made

### Backend

1. **New endpoint:** `/api/plans/{plan_id}/download`
   - Gets plan by ID
   - Verifies authorization
   - Serves file from stored path

2. **New database method:** `get_weekly_plan(plan_id)`
   - Added to `SQLiteDatabase`
   - Added to `SupabaseDatabase`
   - Added to `DatabaseInterface` (abstract)

### Frontend

1. **Updated `handleDownload`:**
   - Now accepts `planId` parameter
   - Uses new `/api/plans/{plan_id}/download` endpoint
   - Fetches file as blob for proper browser download
   - Falls back to old method if planId not provided

## Files Changed

- `backend/api.py`: Added `/api/plans/{plan_id}/download` endpoint
- `backend/database.py`: Added `get_weekly_plan()` method
- `backend/supabase_database.py`: Added `get_weekly_plan()` method
- `backend/database_interface.py`: Added abstract `get_weekly_plan()` method
- `frontend/src/components/PlanHistory.tsx`: Updated download logic

## Verification

**Before Fix:**
- Browser: ❌ 404 error - file not found

**After Fix:**
- Browser: ✅ Downloads file correctly from actual path
- Desktop: ✅ Still uses Tauri file dialog

## Security

- ✅ Authorization check: Verifies user owns the plan
- ✅ Path validation: Uses stored path from database (not user input)
- ✅ File existence check: Verifies file exists before serving

## Status

✅ **FIXED** - File downloads now work correctly using plan ID endpoint

---

**Date Fixed:** 2025-11-07  
**Impact:** High (blocked file downloads)


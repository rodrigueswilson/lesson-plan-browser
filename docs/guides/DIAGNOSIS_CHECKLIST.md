# Multi-Slot Detection Failure - Diagnosis Checklist

## Problem Summary

Your screenshot shows **single-slot behavior** (Math links in ELA, no slot headers), which means:
- The renderer is using `_fill_single_slot_day()` instead of `_fill_multi_slot_day()`
- The detection check `if "slots" in day_data` is returning `False`
- The merged JSON doesn't have the `slots` array structure

---

## Checklist

### ✅ Step 1: Restart Backend

**Why:** FastAPI auto-reload is unreliable. The backend might be running old code.

```bash
# Stop backend (Ctrl+C)
# Start fresh:
python -m uvicorn backend.api:app --reload --port 8000
```

**Verify:**
- Look for: `✓ Cache cleared on startup`
- Confirm: `INFO: Application startup complete.`

---

### ✅ Step 2: Check Merged JSON Structure

**Run diagnostic:**
```bash
python tools\diagnostics\check_json_structure.py output/your_merged_file.json
```

**What to look for:**

#### ✅ GOOD (Multi-slot will work):
```
monday:
  ✓ Has 'slots' array with 2 slots
    - Slot 1: ELA
    - Slot 2: Math
```

#### ❌ BAD (Single-slot behavior):
```
monday:
  ✗ No 'slots' array - will be treated as SINGLE-SLOT
    Keys: ['unit_lesson', 'objective', ...]
```

---

### ✅ Step 3: Find the Merged JSON File

**Where to look:**
```bash
# Check output folder
ls -lt output/*merged*.json | head -5

# Or on Windows:
dir output\*merged*.json /O-D
```

**Expected filename pattern:**
- `Wilson_W44_10-27-10-31_merged.json`
- `Lang_W44_10-27-10-31_merged.json`

**If no merged file exists:**
- The batch processor didn't run
- Or it failed before creating the merged JSON
- Check backend logs for errors

---

### ✅ Step 4: Check Backend Logs

**Look for these log entries:**

#### During Processing:
```
INFO: merge_lesson_jsons called with 2 lessons
INFO: Merged JSON created with slots structure
```

#### During Rendering:
```
# GOOD - Multi-slot detected:
DEBUG: Day monday has slots array with 2 slots
INFO: Using _fill_multi_slot_day for monday

# BAD - Single-slot detected:
DEBUG: Day monday has no slots array
INFO: Using _fill_single_slot_day for monday
```

---

### ✅ Step 5: Verify JSON Merger is Called

**Check batch_processor.py line 864:**
```python
merged_json = merge_lesson_jsons(lessons)
```

**This should:**
1. Take multiple lesson JSONs
2. Create a `slots` array for each day
3. Return merged JSON with proper structure

**If this isn't being called:**
- You might be processing a single-slot document
- Or the batch processor is using a different code path

---

## Common Issues & Solutions

### Issue 1: Backend Not Restarted
**Symptom:** Code changes don't take effect  
**Solution:** Manually restart backend (Ctrl+C, then restart)

### Issue 2: No Merged JSON File
**Symptom:** Can't find `*merged*.json` in output/  
**Solution:** Check if processing completed successfully, check logs for errors

### Issue 3: Merged JSON Has No Slots
**Symptom:** `tools\diagnostics\check_json_structure.py` shows "No 'slots' array"  
**Solution:** 
- Check if `json_merger.py` was called
- Check if input lessons have proper structure
- Verify `batch_processor.py` line 864 is executing

### Issue 4: Processing Single File Instead of Batch
**Symptom:** Only one teacher's file processed  
**Solution:** Make sure you're using batch processing mode with multiple slots selected

---

## Quick Diagnostic Commands

```bash
# 1. Check if backend is running new code
curl http://localhost:8000/api/health

# 2. Find most recent merged JSON
ls -lt output/*merged*.json | head -1

# 3. Check JSON structure
python tools\diagnostics\check_json_structure.py output/[your_file].json

# 4. Check for hyperlink metadata
python diagnose_cross_contamination.py output/[your_file].json
```

---

## Expected Flow

### Correct Multi-Slot Flow:
1. **Frontend:** User selects multiple slots (ELA + Math)
2. **Backend:** Processes each slot separately → 2 lesson JSONs
3. **JSON Merger:** Combines into merged JSON with `slots` arrays
4. **Renderer:** Detects `slots` array → uses `_fill_multi_slot_day()`
5. **Output:** DOCX with slot headers, proper hyperlink filtering

### Broken Single-Slot Flow:
1. **Frontend:** User selects multiple slots
2. **Backend:** Processes each slot separately → 2 lesson JSONs
3. **JSON Merger:** ❌ NOT CALLED or creates wrong structure
4. **Renderer:** No `slots` array → uses `_fill_single_slot_day()`
5. **Output:** ❌ DOCX with cross-contamination, no slot headers

---

## Next Steps

1. ✅ **Restart backend** (most likely fix)
2. ✅ **Check merged JSON structure** with diagnostic script
3. ✅ **Reprocess your W44 files** through the frontend
4. ✅ **Verify output** has slot headers and proper filtering

---

## If Still Not Working

If after following all steps you still see single-slot behavior:

1. **Share the merged JSON file** - I can inspect it
2. **Share backend logs** - Look for errors during merging
3. **Share processing request** - What slots were selected?

The issue is either:
- Backend not restarted (most common)
- Merged JSON doesn't have `slots` arrays (merger issue)
- Frontend sending wrong request format (rare)

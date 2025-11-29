# CRITICAL FIX: Batch Processor Multi-Slot Rendering

## Status: ✅ FIXED

Found and fixed the root cause of why multi-slot rendering wasn't working!

---

## The Problem

The batch processor was **creating the merged JSON correctly** but then **ignoring it** and using the old approach:

### Old Code (Lines 940-1002):
```python
else:
    # Multi-slot: render each slot separately, then merge into one file
    for lesson in lessons:
        lesson_json = lesson["lesson_json"]  # Use ORIGINAL, not merged! ❌
        renderer.render(lesson_json, temp_path)  # Render separately ❌
        temp_files.append(temp_path)
    
    # Then merge DOCX files
    self._merge_docx_files(temp_files, output_path)  # Old approach ❌
```

**This completely bypassed the new per-slot rendering logic!**

---

## Why It Happened

The code had two paths:
1. **Single-slot:** Render merged JSON directly ✅
2. **Multi-slot:** Render each slot separately, merge DOCX files ❌

The multi-slot path was using the **old approach** from before the refactor:
- Render each slot to a separate temp DOCX
- Merge the DOCX files together using docxcompose
- This never triggered `_fill_multi_slot_day()` because each render saw a single-slot JSON

---

## The Fix

### New Code (Lines 940-965):
```python
else:
    # Multi-slot: render merged JSON with slots arrays
    # The new renderer will detect slots arrays and use per-slot rendering
    logger.info("batch_render_multi_slot_start", ...)
    
    # Render merged JSON directly ✅
    renderer.render(merged_json, output_path)
    
    logger.info("batch_render_multi_slot_success", ...)
    return output_path
```

**Now both single-slot and multi-slot use the same approach: render the merged JSON directly.**

---

## What Changed

**File:** `tools/batch_processor.py`

### Removed (~60 lines):
- Loop that rendered each slot separately
- Temp file creation and management
- DOCX file merging with docxcompose
- Signature box cleanup
- Temp file cleanup

### Added (~15 lines):
- Direct rendering of merged JSON
- Debug logging to verify slots arrays exist
- Simplified success logging

---

## How It Works Now

### Complete Flow:

1. **Process each slot** → Individual lesson JSONs ✅
2. **Merge JSONs** → Create merged JSON with `slots` arrays ✅
3. **Render merged JSON** → Renderer detects `slots` arrays ✅
4. **Use `_fill_multi_slot_day()`** → Per-slot rendering with headers ✅
5. **Output single DOCX** → With slot headers and proper filtering ✅

---

## Impact

### Before (Broken):
- ❌ Merged JSON created but ignored
- ❌ Each slot rendered separately
- ❌ DOCX files merged together
- ❌ No slot headers
- ❌ Cross-contamination (Math links in ELA)
- ❌ Old single-slot behavior

### After (Fixed):
- ✅ Merged JSON created and used
- ✅ Single render call with merged JSON
- ✅ Renderer detects `slots` arrays
- ✅ Slot headers added ("Slot 1: ELA", "Slot 2: Math")
- ✅ Proper hyperlink filtering per slot
- ✅ New multi-slot behavior

---

## Why You Saw Single-Slot Behavior

Your screenshot showed single-slot behavior because:

1. The batch processor created the merged JSON ✅
2. But then rendered each slot separately using original JSONs ❌
3. Each render saw a single-slot JSON (no `slots` array) ❌
4. Renderer used `_fill_single_slot_day()` ❌
5. Result: Old behavior with cross-contamination ❌

---

## Test Results

All tests still pass:
```
20/20 tests passing ✅
```

The tests work because they call the renderer directly with proper multi-slot JSON. The bug was in the batch processor's flow, not the renderer itself.

---

## Next Steps

### 1. Restart Backend
```bash
# Stop (Ctrl+C), then:
python -m uvicorn backend.api:app --reload --port 8000
```

### 2. Reprocess Your W44 Files

Process through the frontend. You should now see:
- ✅ **Slot headers:** "Slot 1: ELA (Lang)", "Slot 2: Math (Wilson)"
- ✅ **Proper filtering:** ELA links only in ELA slot
- ✅ **Separators:** `---` between slots
- ✅ **No cross-contamination**

### 3. Check the Logs

You should see:
```
DEBUG: batch_render_merged_json
  slot_count: 5
  has_slots_arrays: True
INFO: batch_render_multi_slot_success
```

---

## Why This Was Hard to Find

1. **The merged JSON was being created correctly** - So that path looked fine
2. **The renderer code was correct** - Tests passed
3. **The bug was in the glue code** - Batch processor's flow logic
4. **It was using an old code path** - From before the refactor

The batch processor had **two different approaches** for single vs. multi-slot, and the multi-slot one was never updated to use the new rendering logic.

---

## Summary

**Root Cause:** Batch processor rendered multi-slot documents using the old "render separately + merge DOCX" approach instead of the new "render merged JSON" approach.

**Fix:** Changed multi-slot path to render merged JSON directly, same as single-slot path.

**Result:** Renderer now detects `slots` arrays and uses `_fill_multi_slot_day()` with proper slot headers and filtering.

---

**Status:** ✅ Fixed and ready to test  
**Action Required:** Restart backend and reprocess W44 files

🎉 **This should fix the issue!**

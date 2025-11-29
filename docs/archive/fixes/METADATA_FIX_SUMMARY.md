# Metadata Fixes Applied

## Status: ✅ PARTIALLY FIXED

Fixed the "Multiple Teachers/Subjects" issue. The "Referenced Links" issue requires investigation.

---

## Fix 1: Header Metadata ✅

### Problem
Header showed:
```
Name: Multiple Teachers
Subject: Multiple Subjects
```

### Solution
Changed lines 909-912 in `batch_processor.py`:

**Before:**
```python
if len(teachers) > 1:
    merged_json["metadata"]["teacher_name"] = "Multiple Teachers"
if len(subjects) > 1:
    merged_json["metadata"]["subject"] = "Multiple Subjects"
```

**After:**
```python
if len(teachers) > 1:
    merged_json["metadata"]["teacher_name"] = " / ".join(sorted(teachers))
if len(subjects) > 1:
    merged_json["metadata"]["subject"] = " / ".join(sorted(subjects))
```

### Result
Header will now show:
```
Name: Caitlin Davies / Donna Savoca / Kelsey Lang
Subject: ELA / ELA/SS / Math / Science
```

---

## Fix 2: Referenced Links Section ⚠️

### Problem
Some hyperlinks still appear in "Referenced Links" section at the end.

### Root Cause
The strict filtering (added earlier) now **requires** `_source_slot` and `_source_subject` metadata. Hyperlinks without this metadata are skipped and fall back to "Referenced Links".

### Why This Happens
The `json_merger.py` correctly adds metadata to all hyperlinks it receives. But if hyperlinks are missing from the individual lesson JSONs (before merging), they won't get tagged.

### Investigation Needed

**Check the logs for warnings:**
```
WARNING: hyperlink_missing_slot_metadata
WARNING: hyperlink_missing_subject_metadata
```

These warnings tell us which hyperlinks don't have metadata.

**Run diagnostic:**
```bash
# Find the most recent merged JSON
python diagnose_cross_contamination.py output/[your_merged_file].json
```

This will show:
- How many hyperlinks have metadata
- Which ones are missing metadata
- What their text/URLs are

### Possible Causes

1. **Parser doesn't extract all hyperlinks** - Some hyperlinks in the input DOCX aren't being found
2. **Hyperlinks added after parsing** - LLM adds new hyperlinks that don't exist in input
3. **Metadata not preserved** - Hyperlinks lose metadata during processing

### Next Steps

1. ✅ **Restart backend** (to load the metadata fix)
2. ✅ **Reprocess W44 files**
3. ✅ **Check the output** - Header should show actual names
4. ⚠️ **Check logs** - Look for metadata warnings
5. ⚠️ **Run diagnostic** - Identify which hyperlinks are missing metadata
6. ⚠️ **Fix parser** - Ensure all hyperlinks get metadata

---

## Expected Improvements

### After Restart:
- ✅ Header shows actual teacher names (e.g., "Caitlin Davies / Donna Savoca")
- ✅ Header shows actual subjects (e.g., "ELA / Math / Science")
- ✅ Slot headers still work ("Slot 1: ELA (Lang)")
- ⚠️ "Referenced Links" may still appear (needs investigation)

---

## Commands

### Restart Backend:
```bash
cd d:\LP
python -m uvicorn backend.api:app --reload --port 8000
```

### After Processing, Check Logs:
Look for lines like:
```
WARNING: hyperlink_missing_slot_metadata
  text: "LESSON 10: SOLVE AREA PROBLEMS"
  url: "..."
  current_slot: 5
```

### Run Diagnostic:
```bash
python diagnose_cross_contamination.py output/Wilson_Weekly_W44_10-27-10-31_[timestamp].json
```

---

## Summary

**Fix 1 (Metadata):** ✅ Complete - Restart backend and reprocess  
**Fix 2 (Referenced Links):** ⚠️ Needs investigation - Check logs and run diagnostic

The header will look correct after restart. The "Referenced Links" issue requires understanding which hyperlinks are missing metadata and why.

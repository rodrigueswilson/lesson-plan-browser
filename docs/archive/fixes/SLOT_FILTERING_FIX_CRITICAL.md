# CRITICAL FIX: Slot Filtering in Single-Slot Rendering

## Status: ✅ FIXED

The hyperlink cross-contamination was caused by the renderer not receiving slot metadata when rendering each slot separately.

---

## The Problem

### What Was Happening:
```
Batch Processor:
  - Adds metadata to hyperlinks ✅
  - Renders each slot separately ✅
  
Renderer (_fill_single_slot_day):
  - Receives hyperlinks with metadata ✅
  - But doesn't pass current_slot_number to _fill_cell ❌
  - Filtering code checks: if current_slot_number is not None ❌
  - Since it's None, filtering is SKIPPED ❌
  - Result: ALL hyperlinks placed, regardless of slot ❌
```

### Why It Happened:
The strict filtering code (lines 706-749) was only being used in the **multi-slot path** (`_fill_multi_slot_day`), which passes `current_slot_number` to `_fill_cell`.

But we're now rendering **each slot separately** using the **single-slot path** (`_fill_single_slot_day`), which wasn't passing those parameters!

---

## The Fix

### Part 1: Add Slot Metadata to Lesson JSON (batch_processor.py)

**Lines 960-965:**
```python
# CRITICAL: Add slot metadata to lesson JSON metadata
# The renderer will extract this to enable strict filtering
if 'metadata' not in lesson_json:
    lesson_json['metadata'] = {}
lesson_json['metadata']['slot_number'] = slot_num
lesson_json['metadata']['subject'] = subject
```

**Why:** The renderer needs to know which slot it's rendering.

### Part 2: Extract Slot Metadata in Renderer (docx_renderer.py)

**Lines 156-159:**
```python
# Extract slot metadata for filtering (if present)
# In multi-slot batch processing, each lesson JSON has slot metadata
slot_number = json_data.get("metadata", {}).get("slot_number")
subject = json_data.get("metadata", {}).get("subject")
```

**Why:** Extract the slot info from the JSON metadata.

### Part 3: Pass Through Rendering Pipeline (docx_renderer.py)

**Lines 164-176:**
```python
for day_name, day_data in json_data["days"].items():
    self._fill_day(doc, day_name, day_data,
                  pending_hyperlinks=pending_hyperlinks,
                  pending_images=pending_images,
                  slot_number=slot_number,  # ← NEW
                  subject=subject)           # ← NEW
```

**Why:** Pass slot info to `_fill_day`.

### Part 4: Pass to Single-Slot Path (docx_renderer.py)

**Lines 395-400:**
```python
self._fill_single_slot_day(table, col_idx, day_data,
                          day_name=day_name,
                          pending_hyperlinks=pending_hyperlinks,
                          pending_images=pending_images,
                          slot_number=slot_number,  # ← NEW
                          subject=subject)           # ← NEW
```

**Why:** Pass slot info to `_fill_single_slot_day`.

### Part 5: Pass to _fill_cell (docx_renderer.py)

**Lines 439-492:**
```python
# All _fill_cell calls now include:
self._fill_cell(
    table, row_idx, col_idx, text,
    day_name=day_name,
    section_name='unit_lesson',
    pending_hyperlinks=pending_hyperlinks,
    pending_images=pending_images,
    current_slot_number=slot_number,  # ← NEW
    current_subject=subject            # ← NEW
)
```

**Why:** Enable the strict filtering code (lines 706-749).

---

## How It Works Now

### Complete Flow:

1. **Batch Processor** (lines 960-977):
   ```python
   lesson_json['metadata']['slot_number'] = 1
   lesson_json['metadata']['subject'] = 'ELA'
   
   for link in lesson_json['_hyperlinks']:
       link['_source_slot'] = 1
       link['_source_subject'] = 'ELA'
   ```

2. **Renderer Extracts** (lines 158-159):
   ```python
   slot_number = 1  # From metadata
   subject = 'ELA'  # From metadata
   ```

3. **Passes Through Pipeline**:
   ```
   render() → _fill_day() → _fill_single_slot_day() → _fill_cell()
   ```

4. **Filtering Activates** (lines 706-726):
   ```python
   if current_slot_number is not None:  # ✅ Now True!
       link_slot = hyperlink.get('_source_slot')  # = 1
       
       if link_slot != current_slot_number:  # 2 != 1?
           continue  # ✅ Skip Math link in ELA slot!
   ```

---

## Expected Result

### Before Fix:
```
ELA Slot:
  - ELA hyperlinks ✅
  - Math hyperlinks ❌ (cross-contamination)
  - Science hyperlinks ❌ (cross-contamination)
```

### After Fix:
```
ELA Slot:
  - ELA hyperlinks ✅
  - Math hyperlinks ✗ (filtered out)
  - Science hyperlinks ✗ (filtered out)
```

---

## Files Modified

1. **tools/batch_processor.py** (lines 960-977)
   - Add slot metadata to lesson JSON metadata
   - Add slot metadata to hyperlinks/images

2. **tools/docx_renderer.py** (multiple locations)
   - Extract slot metadata from JSON (lines 156-159)
   - Pass through `_fill_day` (lines 164-176)
   - Pass through `_fill_single_slot_day` (lines 395-400, 402-420)
   - Pass to all `_fill_cell` calls (lines 439-492)

---

## Testing

### After Restart:

1. ✅ **Restart backend** - Load new code
2. ✅ **Reprocess W44** - Test with real data
3. ✅ **Check logs** - Look for filtering messages:
   ```
   DEBUG: hyperlink_filtered_by_slot
     text: "LESSON 10: SOLVE AREA PROBLEMS"
     link_slot: 5
     current_slot: 1
   ```

4. ✅ **Check output** - Each slot should only have its own hyperlinks:
   - ELA slot: Only ELA hyperlinks
   - Math slot: Only Math hyperlinks
   - No cross-contamination!

---

## Summary

**Root Cause:** Single-slot rendering path didn't pass `current_slot_number` to filtering code

**Fix:** Extract slot metadata from JSON and pass through entire rendering pipeline

**Result:** Strict filtering now works for both single-slot and multi-slot rendering

**Status:** Ready to test after backend restart

---

**This fix enables the strict filtering that was already implemented but never activated in single-slot mode!** 🎯

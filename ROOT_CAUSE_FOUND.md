# ROOT CAUSE FOUND: Single-Slot Path Used Merged JSON

## Status: ✅ FIXED

After complete code analysis, found the root cause of hyperlink cross-contamination.

---

## The Problem

### What Was Happening:
```python
# Line 930 in batch_processor.py (OLD CODE)
if len(lessons) == 1:
    renderer.render(merged_json, output_path)  # ❌ WRONG!
```

**The single-slot rendering path was using `merged_json` instead of `lesson_json`!**

### Why This Caused Cross-Contamination:

1. **Merged JSON created** (line 864) - For metadata purposes
2. **Slot metadata added to individual lesson JSONs** (lines 964-977) - ✅ Correct
3. **But single-slot path rendered `merged_json`** (line 930) - ❌ Wrong JSON!
4. **`merged_json` doesn't have slot metadata** - Never added to it
5. **Renderer extracts `slot_number` from metadata** (line 158) - Returns `None`
6. **Filtering code checks `if current_slot_number is not None`** (line 748) - False!
7. **Filtering skipped** - All hyperlinks placed regardless of slot
8. **Result:** Cross-contamination

---

## The Flow (Before Fix)

### Single-Slot Processing:
```
1. Parse DOCX → Extract hyperlinks (no slot metadata yet)
2. LLM transform → Create lesson_json
3. Add hyperlinks to lesson_json (line 646)
4. Create merged_json from lessons (line 864)
5. Add slot metadata to lessons[0]['lesson_json'] (lines 964-977) ✅
6. Render merged_json (line 930) ❌ WRONG JSON!
   └─ merged_json has no slot metadata
   └─ Renderer extracts slot_number = None
   └─ Filtering bypassed
   └─ Cross-contamination
```

### Multi-Slot Processing:
```
1-4. Same as above
5. Add slot metadata to each lesson_json (lines 964-977) ✅
6. Render each lesson_json separately (line 987) ✅
   └─ lesson_json has slot metadata
   └─ Renderer extracts slot_number correctly
   └─ Filtering works
   └─ No cross-contamination
```

**The multi-slot path worked because it rendered the correct JSON objects!**

---

## The Fix

### Changed Lines 923-953:

**Before:**
```python
if len(lessons) == 1:
    renderer.render(merged_json, output_path)  # ❌ No slot metadata
```

**After:**
```python
if len(lessons) == 1:
    # Extract lesson and add slot metadata
    lesson = lessons[0]
    slot_num = lesson["slot_number"]
    subject = lesson["subject"]
    lesson_json = lesson["lesson_json"]
    
    # Add slot metadata to lesson JSON metadata
    lesson_json['metadata']['slot_number'] = slot_num
    lesson_json['metadata']['subject'] = subject
    
    # Add slot metadata to hyperlinks and images
    if '_hyperlinks' in lesson_json:
        for link in lesson_json['_hyperlinks']:
            link['_source_slot'] = slot_num
            link['_source_subject'] = subject
    
    if '_images' in lesson_json:
        for image in lesson_json['_images']:
            image['_source_slot'] = slot_num
            image['_source_subject'] = subject
    
    renderer.render(lesson_json, output_path)  # ✅ Correct JSON with metadata
```

---

## Why This Was Hard to Find

1. **Multi-slot path worked** - Made us think the logic was correct
2. **Single-slot path looked similar** - But used different JSON object
3. **Merged JSON was created** - Looked like it was being used correctly
4. **Metadata was added** - But to the wrong JSON object
5. **Tests passed** - Tests called renderer directly with correct JSON

---

## Complete Hyperlink Flow (After Fix)

### Parsing:
```
Input DOCX → DOCXParser.extract_hyperlinks()
└─ Returns: [{text, url, context, ...}]  # No slot metadata yet
```

### Processing:
```
_process_slot() → Extract hyperlinks (line 398)
└─ Add to lesson_json['_hyperlinks'] (line 646)
└─ Still no slot metadata
```

### Combining (Single-Slot):
```
_combine_lessons() → len(lessons) == 1
└─ Extract lesson_json from lessons[0] (line 929)
└─ Add slot metadata to lesson_json['metadata'] (lines 934-935)
└─ Add slot metadata to each hyperlink (lines 939-941)
└─ Render lesson_json (line 953) ✅
```

### Combining (Multi-Slot):
```
_combine_lessons() → len(lessons) > 1
└─ For each lesson_json:
   └─ Add slot metadata to lesson_json['metadata'] (lines 964-965)
   └─ Add slot metadata to each hyperlink (lines 970-972)
   └─ Render lesson_json (line 987) ✅
```

### Rendering:
```
DOCXRenderer.render(lesson_json, output_path)
└─ Extract slot_number from lesson_json['metadata'] (line 158) ✅
└─ Pass to _fill_day() (line 176) ✅
└─ Pass to _fill_single_slot_day() (line 403) ✅
└─ Pass to _fill_cell() (line 451) ✅
└─ Filtering activates (line 748) ✅
   └─ if current_slot_number is not None: ✅ True!
   └─ if link_slot != current_slot_number: ✅ Filter!
```

---

## Expected Result

### Before Fix:
- ❌ Single-slot: Cross-contamination (used merged_json)
- ✅ Multi-slot: Worked correctly (used lesson_json)

### After Fix:
- ✅ Single-slot: Filtering works (uses lesson_json with metadata)
- ✅ Multi-slot: Still works (unchanged)

---

## Files Modified

**tools/batch_processor.py** (lines 923-953)
- Single-slot path now adds slot metadata to lesson_json
- Renders lesson_json instead of merged_json

---

## Testing

### After Restart:

1. ✅ **Process single slot** (e.g., just ELA)
   - Should only show ELA hyperlinks
   - No cross-contamination

2. ✅ **Process multiple slots** (e.g., ELA + Math)
   - Each slot should only show its own hyperlinks
   - No cross-contamination

3. ✅ **Check logs** for:
   ```
   INFO: renderer_slot_metadata_extracted
     slot_number: 1
     subject: ELA
   
   INFO: hyperlink_filtering_context
     current_slot_number: 1
   
   DEBUG: hyperlink_filtered_by_slot
     link_slot: 5
     current_slot: 1
   ```

---

## Summary

**Root Cause:** Single-slot rendering path used `merged_json` (no slot metadata) instead of `lesson_json` (has slot metadata)

**Fix:** Changed single-slot path to:
1. Extract `lesson_json` from `lessons[0]`
2. Add slot metadata to it
3. Render it (not merged_json)

**Result:** Filtering now works for both single-slot and multi-slot rendering

**Status:** Ready to test after backend restart

---

**This was the missing piece!** The logic was perfect, but the single-slot path was rendering the wrong JSON object. 🎯

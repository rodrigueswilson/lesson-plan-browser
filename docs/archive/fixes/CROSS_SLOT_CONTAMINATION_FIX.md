# Cross-Slot Contamination Fix - CRITICAL

## Status: ✅ FIXED

**Root Cause Found:** Content extraction was NOT slot-aware, causing cross-slot contamination.

---

## The Problem

### What Happened
User reported Math hyperlinks ("2.2.2 Teacher Guide.pdf", "2.2.3 Teacher Guide.pdf") appearing in ELA/SS slot output, even though they should be isolated.

### Root Cause
```python
# OLD CODE - NOT SLOT-AWARE
content = await asyncio.to_thread(parser.extract_subject_content, slot["subject"])
```

The `extract_subject_content()` method searches the **entire document** for tables matching the subject name. When multiple slots have the same subject (e.g., two Math slots), it extracts content from **all matching tables**, not just the slot's specific tables.

### Why Hyperlink Extraction Worked
```python
# This was already slot-aware
hyperlinks = await asyncio.to_thread(parser.extract_hyperlinks_for_slot, slot_num)
images = await asyncio.to_thread(parser.extract_images_for_slot, slot_num)
```

Hyperlink and image extraction were correctly limited to slot-specific tables, which is why the dry run showed correct counts (10 hyperlinks for Slot 2, 0 for Slot 4).

### The Mismatch
- **Hyperlinks extracted:** Only from Slot 2's tables (correct)
- **Content extracted:** From ALL tables matching "Math" subject (wrong!)
- **Result:** LLM sees Math content from other slots, includes it in output

---

## The Fix

### New Method: `extract_subject_content_for_slot()`

```python
def extract_subject_content_for_slot(self, slot_number: int, subject: str, strip_urls: bool = True) -> Dict[str, Any]:
    """
    Extract content for a specific slot only (slot-aware).
    
    This prevents cross-slot contamination by only extracting from the slot's tables.
    """
    # Validate slot structure and get table indices
    table_start, table_end = validate_slot_structure(self.doc, slot_number)
    
    # The daily plans table is at table_end
    daily_table_idx = table_end
    
    # Extract content from the slot's daily plans table ONLY
    table_content = self.extract_table_lesson(daily_table_idx)
    
    # ... rest of processing ...
    
    return {
        'subject': subject,
        'full_text': full_text,
        'table_content': table_content,
        'slot_number': slot_number,  # Track which slot
        'table_idx': daily_table_idx  # Track which table
    }
```

### Updated Batch Processor

```python
# NEW CODE - SLOT-AWARE
print(f"DEBUG: _process_slot - Extracting subject content (SLOT-AWARE)")
content = await asyncio.to_thread(parser.extract_subject_content_for_slot, slot_num, slot["subject"])
print(f"DEBUG: _process_slot - Content extracted, length: {len(content.get('full_text', ''))}, slot: {slot_num}")
```

---

## Key Differences

### Before (Wrong)
```
extract_subject_content("Math")
  → Searches entire document for "Math" tables
  → Finds tables 3, 7, 11 (all Math slots)
  → Returns content from ALL Math tables
  → LLM sees mixed content from multiple slots
```

### After (Correct)
```
extract_subject_content_for_slot(slot_number=2, "Math")
  → Validates slot 2 structure
  → Gets table indices: table_start=2, table_end=3
  → Extracts ONLY from table 3 (slot 2's daily plans)
  → LLM sees only slot 2's content
```

---

## Files Modified

1. **tools/docx_parser.py** (+70 lines)
   - Added `extract_subject_content_for_slot()` method
   - Uses `validate_slot_structure()` to get correct tables
   - Logs slot number and table index for diagnostics

2. **tools/batch_processor.py** (+3 lines)
   - Changed from `extract_subject_content()` to `extract_subject_content_for_slot()`
   - Passes `slot_num` as first parameter
   - Updated debug logging

---

## Expected Behavior After Fix

### Slot 2 (ELA/SS) - Savoca File
**Before Fix:**
```
Anticipatory Set:
2.2.2 Teacher Guide.pdf  ← FROM MATH SLOT!
2.2.3 Teacher Guide.pdf  ← FROM MATH SLOT!
Refer to the second grade ELA curriculum...
```

**After Fix:**
```
Anticipatory Set:
Refer to the second grade ELA curriculum...
(Only ELA/SS content, no Math contamination)
```

### Slot 4 (Math) - Savoca File
**Before Fix:**
```
(Would also have mixed content)
```

**After Fix:**
```
(Only Math content from Slot 4's table)
```

---

## Validation

### Dry Run Showed Correct Hyperlink Counts
```
Slot 2 (ELA/SS): 10 hyperlinks from table 3 ✅
Slot 4 (Math):    0 hyperlinks from table 7 ✅
```

This proved hyperlink extraction was slot-aware. The issue was **content extraction** wasn't.

### After Fix - All Extraction Slot-Aware
```
✅ Hyperlinks: extract_hyperlinks_for_slot(slot_num)
✅ Images: extract_images_for_slot(slot_num)
✅ Content: extract_subject_content_for_slot(slot_num, subject)
```

---

## Testing Required

1. **Re-run the same W44 files**
   - Slot 2 (ELA/SS) should NOT have Math hyperlinks
   - Each slot should only have its own content
   
2. **Check output files**
   - Anticipatory Set should match source slot
   - No cross-slot contamination
   
3. **Verify logs**
   - Should see "SLOT-AWARE" in debug output
   - `slot_content_extracted` events with correct table_idx

---

## Why This Wasn't Caught Earlier

1. **Dry run only tested hyperlink/image extraction** - which were already slot-aware
2. **Tests didn't check content extraction** - focused on media preservation
3. **Single-subject files worked fine** - contamination only happens with duplicate subjects

---

## Impact

**Severity:** CRITICAL - Causes incorrect content in output files

**Scope:** Any file with multiple slots of the same subject

**Fix Complexity:** Medium - New method + 1-line change in batch processor

**Risk:** Low - New method follows same pattern as existing slot-aware methods

---

## Next Steps

1. ✅ Code fixed
2. 🔄 **Re-run W44 processing** to verify fix
3. 🔄 Check output files for contamination
4. 🔄 Add test case for duplicate subjects

---

**Status:** Ready for re-test! The fix ensures all three extraction methods (hyperlinks, images, content) are now slot-aware and use the same table indices.

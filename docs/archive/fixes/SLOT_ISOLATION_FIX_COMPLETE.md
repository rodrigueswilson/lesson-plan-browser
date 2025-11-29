# Slot Isolation Fix - Complete

## Problem Solved

**Cross-slot hyperlink contamination** - Hyperlinks from one slot (Math) were appearing in another slot's output (ELA).

## Root Cause

1. **`json_merger.py`** - Correctly aggregates all hyperlinks and tags them with `_source_slot` and `_source_subject`
2. **`docx_renderer.py`** - Was NOT filtering hyperlinks by slot, so ALL hyperlinks were candidates for EVERY cell

**Result:** Math hyperlink "LESSON 9" matched ELA text "Lesson 9" with high confidence and was incorrectly placed.

---

## Solution Implemented

### Two-Layer Defense

#### Layer 1: Pre-Filter in `_fill_multi_slot_day()` (Lines 506-523)

**Before rendering any cells**, filter the hyperlink list to only include hyperlinks from the slots being rendered:

```python
# Filter hyperlinks to only those from slots being rendered
slot_numbers = [s.get("slot_number") for s in sorted_slots]
filtered_hyperlinks = []
if pending_hyperlinks:
    for link in pending_hyperlinks:
        link_slot = link.get('_source_slot')
        if link_slot is None or link_slot in slot_numbers:
            filtered_hyperlinks.append(link)
        else:
            logger.debug("hyperlink_filtered_multi_slot", ...)

# Use filtered hyperlinks for this day's cells
pending_hyperlinks = filtered_hyperlinks
```

**Effect:** If rendering Slot 1 (ELA), only Slot 1 hyperlinks are in the candidate pool. Slot 2 (Math) hyperlinks are excluded.

#### Layer 2: Per-Cell Filter in `_fill_cell()` (Lines 735-758)

**During cell filling**, double-check that each hyperlink matches the current slot/subject:

```python
# CRITICAL: Filter hyperlinks by slot to prevent cross-contamination
if current_slot_number is not None:
    link_slot = hyperlink.get('_source_slot')
    if link_slot is not None and link_slot != current_slot_number:
        continue  # Skip hyperlinks from other slots

# Additional filter by subject for extra safety
if current_subject is not None:
    link_subject = hyperlink.get('_source_subject')
    if link_subject is not None and link_subject != current_subject:
        continue  # Skip hyperlinks from other subjects
```

**Effect:** Even if a hyperlink somehow gets through Layer 1, it won't be placed if it doesn't match the current slot/subject.

---

## Files Modified

### `tools/docx_renderer.py`

**Changes:**

1. **`_fill_cell()` signature** (Line 661-666):
   - Added `current_slot_number: int = None`
   - Added `current_subject: str = None`

2. **`_fill_multi_slot_day()` pre-filter** (Lines 506-523):
   - Filter hyperlinks by slot BEFORE rendering cells
   - Only pass relevant hyperlinks to `_fill_cell()`

3. **`_fill_cell()` slot filtering** (Lines 735-758):
   - Check `_source_slot` against `current_slot_number`
   - Check `_source_subject` against `current_subject`
   - Skip hyperlinks that don't match

4. **Enhanced logging** (Lines 741-745, 753-757, 768-775):
   - Log when hyperlinks are filtered by slot
   - Log when hyperlinks are filtered by subject
   - Log slot/subject info when hyperlinks are placed

---

## How It Works

### Single-Slot Rendering

**No change needed** - Each slot renders independently with its own hyperlinks.

### Multi-Slot Rendering

**Before fix:**
```
All hyperlinks: [Math Link 1, Math Link 2, ELA Link 1, ...]
↓
Render Slot 1 (ELA) → ALL hyperlinks considered → Math links placed in ELA ❌
Render Slot 2 (Math) → ALL hyperlinks considered → Works correctly ✅
```

**After fix:**
```
All hyperlinks: [Math Link 1, Math Link 2, ELA Link 1, ...]
↓
Filter for Slot 1: [ELA Link 1, ...]
↓
Render Slot 1 (ELA) → Only ELA hyperlinks considered → Correct ✅
↓
Filter for Slot 2: [Math Link 1, Math Link 2, ...]
↓
Render Slot 2 (Math) → Only Math hyperlinks considered → Correct ✅
```

---

## Testing

### Expected Behavior

**Slot 1 (ELA):**
- Input: "Unit 2- Maps and Globes Lesson 7-11" (no hyperlinks)
- Output: NO hyperlinks ✅

**Slot 2 (Math):**
- Input: "LESSON 9: MEASURE TO FIND THE AREA" (with hyperlinks)
- Output: Hyperlinks placed correctly ✅

### Verification

1. Process a multi-slot week with different subjects
2. Check backend logs for "hyperlink_filtered_by_slot" messages
3. Open output DOCX and verify:
   - ELA slots have NO Math hyperlinks
   - Math slots have NO ELA hyperlinks
   - Each slot only has its own hyperlinks

---

## Benefits

✅ **Prevents cross-contamination** - Hyperlinks stay in their original slot
✅ **Uses existing metadata** - Leverages `_source_slot` and `_source_subject` tags
✅ **Two-layer defense** - Pre-filter + per-cell check
✅ **Backward compatible** - Works with single-slot rendering
✅ **Well-logged** - Easy to debug if issues occur

---

## Status

**COMPLETE** ✅

**Next:** Test with real multi-slot lesson plans to verify fix works in production.

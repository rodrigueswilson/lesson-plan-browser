# Schedule Ordering Verification Results

## Summary

**Problem Verified**: PDF objectives and sentence frames were NOT following day-specific schedule order because enrichment was only applied to multi-slot plans, not single-slot plans.

## Root Cause

The `enrich_lesson_json_with_times()` function was only being called for multi-slot plans in `_combine_lessons_impl()`:

- **Multi-slot path** (line 4280): `enrich_lesson_json_with_times(merged_json, user_id)` ✓
- **Single-slot path** (line 4590): `lesson_json_for_pdf = self._sanitize_value(lesson_json)` ✗ (no enrichment)

This meant single-slot lesson plans never got day-specific times assigned, causing incorrect ordering in PDFs.

## Verification Tests

1. **Enrichment Function Works Correctly**: 
   - Tested `enrich_lesson_json_with_times()` and confirmed it correctly sets day-specific times
   - Monday: Slot order [1(08:30), 2(09:18), 6(11:42), 5(12:30), 4(14:06)]
   - Wednesday: Slot order [1(08:30), 2(09:18), 6(12:30), 4(13:18), 5(14:06)]
   - Times vary by day as expected

2. **Database Contains Correct Schedule Data**:
   - Schedule entries exist for all days with correct times
   - Matching by (subject, grade, homeroom) works correctly

3. **Lesson JSON Structure Supports Enrichment**:
   - Slots structure is present in both single and multi-slot plans
   - Enrichment function can process both structures

## Fixes Applied

### Fix 1: Added enrichment for single-slot plans
Added enrichment call for single-slot plans in `tools/batch_processor.py` before PDF generation (line ~4595):

```python
# CRITICAL: Enrich single-slot lesson_json with day-specific start_time/end_time from schedule
from backend.api import enrich_lesson_json_with_times
user_id = user.get("id") or user.get("user_id")
if user_id:
    enrich_lesson_json_with_times(lesson_json, user_id)
```

### Fix 2: Removed conditional check in enrichment function
Removed conditional check in `backend/api.py` (line 397-398) that could prevent slots from being updated:

```python
# Before: Only updated if slots was already a list
if isinstance(day_data.get("slots"), list):
    day_data["slots"] = final_slots

# After: Always update with enriched and sorted slots
day_data["slots"] = final_slots
```

## Current Issue

The PDF file `Wilson_Rodrigues_Objectives_01_19_01_23_20260118_150616.pdf` shows the same order `[1, 2, 4, 5, 6]` for all days, indicating enrichment may not be applying correctly during PDF generation.

**Possible causes:**
1. Enrichment runs but `_sanitize_value` loses the enriched data (unlikely - it should preserve dict values)
2. Enrichment runs but slots don't match schedule entries correctly
3. Enrichment runs but PDF generator is using a cached or different JSON

## Next Steps

1. Verify enrichment is actually running during PDF generation
2. Check if `_sanitize_value` preserves `start_time` values in slots
3. Add logging to see what order PDF generator receives
4. Test with a newly generated plan to confirm fixes work

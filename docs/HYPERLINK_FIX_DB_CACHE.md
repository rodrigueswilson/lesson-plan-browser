# Hyperlink Fix: DB Cache Issue

**Date:** 2025-12-28  
**Issue:** Hyperlinks missing in parallel processing when DB cache is used  
**Root Cause:** DB cache restores empty hyperlinks and skips extraction

---

## Problem

When parallel processing uses DB cache:
1. Cache is checked first (line 5491-5505)
2. If cache exists, hyperlinks are restored from `db_record.content_json.get("_extracted_hyperlinks", [])`
3. If cache doesn't have hyperlinks (from previous failed runs), empty list is restored
4. Code `continue`s, skipping actual extraction
5. Result: No hyperlinks in context → No hyperlinks in output

---

## Solution

### Fix 1: Extract Hyperlinks if Missing from Cache
- Check if cached hyperlinks exist
- If missing, add slot to `remaining_group` to extract hyperlinks
- Don't skip extraction if hyperlinks are missing

### Fix 2: Use Cached Hyperlinks if Available
- When extracting from file, check if context already has hyperlinks
- If yes, use cached hyperlinks instead of re-extracting
- This preserves hyperlinks from cache when they exist

---

## Code Changes

### File: `tools/batch_processor.py`

**Lines 5499-5505:** Modified DB cache restoration to check for missing hyperlinks
```python
# Restore media from cache metadata
if db_record.content_json:
    context.slot["_extracted_images"] = db_record.content_json.get("_extracted_images", [])
    cached_hyperlinks = db_record.content_json.get("_extracted_hyperlinks", [])
    context.slot["_extracted_hyperlinks"] = cached_hyperlinks
    
    # CRITICAL: If cache doesn't have hyperlinks, we still need to extract them
    if not cached_hyperlinks:
        # Don't continue - add to remaining_group to extract hyperlinks
        remaining_group.append((i, slot, context))
        continue
```

**Lines 5548-5565:** Modified extraction to use cached hyperlinks if available
```python
# CRITICAL: If context already has hyperlinks from cache, use those; otherwise extract
if "_extracted_hyperlinks" in context.slot and context.slot["_extracted_hyperlinks"]:
    # Hyperlinks already in context from cache, use them
    hyperlinks = context.slot["_extracted_hyperlinks"]
else:
    # Extract hyperlinks from file
    hyperlinks = await asyncio.to_thread(parser.extract_hyperlinks_for_slot, actual_slot_num)
```

---

## Testing

1. **Test with fresh cache (no hyperlinks):**
   - Should extract hyperlinks from file
   - Should store hyperlinks in cache for next run

2. **Test with cache containing hyperlinks:**
   - Should use cached hyperlinks
   - Should not re-extract

3. **Test with multiple slots:**
   - Each slot should have hyperlinks
   - Hyperlinks should appear in final output

---

## Expected Behavior After Fix

1. **Cache Hit with Hyperlinks:**
   - Use cached hyperlinks
   - Skip extraction (performance optimization)

2. **Cache Hit without Hyperlinks:**
   - Extract hyperlinks from file
   - Store in cache for next run

3. **No Cache:**
   - Extract hyperlinks from file
   - Store in cache for next run

---

## Impact

- **Fixes:** Hyperlinks missing in parallel processing when DB cache is used
- **Preserves:** Performance optimization of using cached hyperlinks when available
- **Improves:** Reliability by ensuring hyperlinks are always extracted if missing from cache

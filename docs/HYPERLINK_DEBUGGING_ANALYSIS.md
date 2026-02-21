# Hyperlink Debugging Analysis

**Date:** 2025-12-28  
**Issue:** Hyperlinks are missing from generated DOCX files  
**Status:** Added comprehensive logging to trace hyperlink flow

---

## Architecture Review

### Hyperlink Flow Paths

#### Sequential Path (`_process_slot`)
1. **Extraction** (lines 2391-2393):
   - `hyperlinks = await asyncio.to_thread(parser.extract_hyperlinks_for_slot, slot_num)`
   - Stores in local variable `hyperlinks`

2. **No School Check** (line 2544):
   - If `parser.is_no_school_day()` → filters out ALL hyperlinks (line 2560)
   - Returns early with minimal JSON

3. **No School Day Filtering** (lines 2761-2777):
   - Filters hyperlinks for specific No School days
   - Preserves hyperlinks without `day_hint`

4. **Attachment** (lines 2999-3017):
   - Attaches hyperlinks to `lesson_json["_hyperlinks"]`
   - Adds slot/subject metadata

5. **Return** (line 3055):
   - Returns `lesson_json` with hyperlinks

#### Parallel Path (`_extract_slots_parallel_db` → `_process_file_group` → `_transform_slot_with_llm`)

**Phase 1: Extraction** (`_process_file_group`, lines 5431-5449):
1. Extracts hyperlinks (line 5432)
2. Filters for No School days (lines 5435-5442)
3. Stores in `context.slot["_extracted_hyperlinks"]` (line 5449)

**Phase 2: Transformation** (`_transform_slot_with_llm`, lines 1792-1809):
1. Retrieves hyperlinks from `context.slot.get("_extracted_hyperlinks", [])` (line 1793)
2. Adds slot/subject metadata (lines 1798-1804)
3. Attaches to `lesson_json["_hyperlinks"]` (line 1809)
4. Stores in `context.lesson_json` (line 1863)

**Phase 3: Collection** (lines 547-554):
1. Collects `context.lesson_json` from each context
2. Appends to `lessons` list

---

## Potential Issues Identified

### Issue 1: No School Detection
- **Location:** Sequential path line 2544, Parallel path line 5435
- **Problem:** If `parser.is_no_school_day()` incorrectly returns `True`, all hyperlinks are filtered out
- **Impact:** All hyperlinks lost before attachment
- **Fix:** Verify `is_no_school_day()` logic is correct

### Issue 2: No School Day Filtering
- **Location:** Sequential path lines 2761-2777, Parallel path lines 5437-5442
- **Problem:** Hyperlinks with `day_hint` matching No School days are filtered out
- **Impact:** Some hyperlinks may be incorrectly filtered
- **Fix:** Verify filtering logic matches expected behavior

### Issue 3: Missing Hyperlinks in Context
- **Location:** Parallel path line 1793
- **Problem:** If hyperlinks aren't stored in `context.slot["_extracted_hyperlinks"]` during extraction, they won't be available during transformation
- **Impact:** Hyperlinks lost between phases
- **Fix:** Verify extraction phase stores hyperlinks correctly

### Issue 4: Hyperlinks Not Attached
- **Location:** Both paths (sequential line 3017, parallel line 1809)
- **Problem:** If `hyperlinks` list is empty, `lesson_json["_hyperlinks"]` is never set
- **Impact:** Empty hyperlinks list results in missing `_hyperlinks` key
- **Fix:** Verify hyperlinks list is not empty before attachment

---

## Logging Added

### Sequential Path Logging
- **Extraction:** Logs count and details of extracted hyperlinks (line 2395)
- **No School Filtering:** Logs when hyperlinks are filtered (line 2562)
- **Attachment:** Logs when hyperlinks are attached (line 3014)
- **Collection:** Logs hyperlink count when collecting results (line 670)

### Parallel Path Logging
- **Extraction (`_process_file_group`):** Logs extraction and filtering (lines 5432-5449)
- **Transformation (`_transform_slot_with_llm`):** Logs retrieval and attachment (lines 1793-1809)
- **Collection:** Logs hyperlink count when collecting results (line 547)

### JSON Merger Logging
- **Diagnostic:** Logs details about each lesson when no hyperlinks found (line 120)

---

## Next Steps

1. **Run Test Generation:**
   - Generate a lesson plan with hyperlinks
   - Monitor logs for hyperlink extraction, filtering, and attachment

2. **Check Logs For:**
   - `[DEBUG] _process_slot (SEQUENTIAL): Extracted X hyperlinks`
   - `[DEBUG] _process_file_group (PARALLEL): Extracted X hyperlinks`
   - `[DEBUG] _transform_slot_with_llm (PARALLEL): Retrieved X hyperlinks`
   - `[DEBUG] Adding X hyperlinks to lesson_json`
   - `[WARN] No hyperlinks extracted!`

3. **Identify Where Hyperlinks Are Lost:**
   - If extraction shows 0 hyperlinks → Parser issue
   - If extraction shows hyperlinks but attachment shows 0 → Filtering issue
   - If attachment shows hyperlinks but merger shows 0 → Collection issue

4. **Fix Based on Findings:**
   - Adjust No School detection if needed
   - Fix filtering logic if hyperlinks incorrectly filtered
   - Fix attachment logic if hyperlinks not being attached

---

## Code Changes Made

1. **Added comprehensive logging** throughout hyperlink flow
2. **Added diagnostic logging** in JSON merger when no hyperlinks found
3. **Added path identification** (SEQUENTIAL vs PARALLEL) in all log messages
4. **Added hyperlink count verification** at collection points

---

## Testing Checklist

- [ ] Run lesson plan generation
- [ ] Check logs for hyperlink extraction counts
- [ ] Check logs for hyperlink filtering (if any)
- [ ] Check logs for hyperlink attachment
- [ ] Check logs for hyperlink collection
- [ ] Verify hyperlinks appear in final DOCX
- [ ] Identify root cause if hyperlinks still missing

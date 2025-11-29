# Diagnostic Logging System

## Status: ✅ IMPLEMENTED (Partial - needs renderer fix)

Created comprehensive diagnostic logging system to track hyperlink flow and detect cross-contamination.

---

## What Was Added

### 1. Diagnostic Logger Module
**File:** `tools/diagnostic_logger.py`

**Features:**
- Creates timestamped session directories
- Logs each processing stage to separate JSON files
- Records hyperlink metadata at every step
- Tracks filtering decisions
- Generates session summary

**Output Location:** `logs/diagnostics/session_YYYYMMDD_HHMMSS/`

---

## Logging Points Added

### ✅ Batch Processor (Complete)

1. **After Parser Extraction** (line 404)
   - Logs: Hyperlinks extracted from DOCX
   - File: `01_parser_slot{N}.json`
   - Shows: Count, sample hyperlinks, metadata presence

2. **After Lesson JSON Created** (line 658)
   - Logs: Hyperlinks added to lesson JSON
   - File: `02_lesson_json_slot{N}.json`
   - Shows: Metadata presence, slot distribution

3. **Before Single-Slot Rendering** (line 970)
   - Logs: Lesson JSON just before rendering
   - File: `03_before_render_slot{N}.json`
   - Shows: All metadata, hyperlink distribution

4. **Before Multi-Slot Rendering** (line 1038)
   - Logs: Each slot before rendering
   - File: `03_before_render_slot{N}.json`
   - Shows: Same as single-slot

### ✅ Renderer (Partial - needs fix)

5. **Metadata Extraction** (line 172)
   - Logs: Slot metadata extracted by renderer
   - File: `04_renderer_metadata_extracted.json`
   - Shows: slot_number, subject, whether filtering will activate

6. **Filtering Context** (line 757)
   - Logs: Context when filtering hyperlinks
   - File: `05_filtering_context.json`
   - Shows: current_slot_number, pending count

7. **Filtered Hyperlinks** (line 788)
   - Logs: Each hyperlink filtered out
   - File: `06_hyperlink_filtered.json`
   - Shows: Which slot it belonged to, why filtered

8. **Placed Hyperlinks** (needs to be added)
   - Logs: Each hyperlink placed inline
   - File: `07_hyperlink_placed.json`
   - Shows: Where placed, confidence

---

## How to Use

### After Processing:

1. **Check session directory:**
   ```
   logs/diagnostics/session_20251026_195400/
   ```

2. **Review files in order:**
   - `01_parser_slot1.json` - Hyperlinks extracted
   - `02_lesson_json_slot1.json` - Added to lesson JSON
   - `03_before_render_slot1.json` - Before rendering
   - `04_renderer_metadata_extracted.json` - Renderer setup
   - `05_filtering_context.json` - Filtering context
   - `06_hyperlink_filtered.json` - Filtered hyperlinks
   - `07_hyperlink_placed.json` - Placed hyperlinks

3. **Check session_log.json** for complete timeline

4. **Check summary.json** for overview

---

## What to Look For

### If Cross-Contamination Persists:

#### Check `02_lesson_json_slot1.json`:
```json
{
  "hyperlinks_with_slot_metadata": 99,  // Should equal hyperlink_count
  "hyperlinks_with_subject_metadata": 99,  // Should equal hyperlink_count
  "sample_hyperlinks": [
    {
      "text": "LESSON 10...",
      "has_source_slot": true,  // Should be true
      "source_slot": 1,  // Should match slot_number
      "has_source_subject": true,  // Should be true
      "source_subject": "ELA"  // Should match subject
    }
  ]
}
```

**If `has_source_slot` is false:** Metadata not added in batch processor

#### Check `03_before_render_slot1.json`:
```json
{
  "metadata_slot_number": 1,  // Should be present
  "metadata_subject": "ELA",  // Should be present
  "all_hyperlinks_have_slot": true,  // Should be true
  "all_hyperlinks_have_subject": true,  // Should be true
  "hyperlink_slot_distribution": {
    "1": 99  // All should be in this slot
  }
}
```

**If `metadata_slot_number` is null:** Metadata not added to lesson JSON metadata
**If `all_hyperlinks_have_slot` is false:** Some hyperlinks missing metadata

#### Check `04_renderer_metadata_extracted.json`:
```json
{
  "slot_number": 1,  // Should NOT be null
  "slot_number_is_none": false,  // Should be false
  "subject": "ELA",  // Should NOT be null
  "filtering_will_activate": true  // Should be true
}
```

**If `slot_number_is_none` is true:** Renderer didn't extract metadata correctly

#### Check `05_filtering_context.json`:
```json
{
  "current_slot_number": 1,  // Should NOT be null
  "current_slot_number_is_none": false,  // Should be false
  "filtering_active": true  // Should be true
}
```

**If `current_slot_number_is_none` is true:** Metadata not passed through pipeline

#### Check `06_hyperlink_filtered.json`:
```json
{
  "text": "LESSON 10...",
  "link_slot": 5,  // Math slot
  "current_slot": 1,  // ELA slot
  "reason": "slot_mismatch"
}
```

**Should see many of these** - Math links filtered from ELA slot

---

## Current Status

### ✅ Implemented:
- Diagnostic logger module
- Batch processor logging (4 points)
- Renderer metadata extraction logging
- Renderer filtering context logging
- Renderer filtered hyperlink logging

### ⚠️ Needs Fix:
- Renderer has syntax error (line 836)
- Hyperlink placement logging not added
- Unmatched hyperlinks logging not added

---

## Next Steps

1. **Fix renderer syntax error** at line 836
2. **Add hyperlink placement logging**
3. **Add unmatched hyperlinks logging**
4. **Restart backend**
5. **Process W44 files**
6. **Review diagnostic logs**

---

## Benefits

### For Debugging:
- ✅ Complete audit trail of hyperlink flow
- ✅ Pinpoint exact stage where metadata is lost
- ✅ Verify filtering is working
- ✅ Identify which hyperlinks are problematic

### For Analysis:
- ✅ JSON files can be programmatically analyzed
- ✅ Compare before/after processing
- ✅ Track metadata through entire pipeline
- ✅ Verify fix effectiveness

---

## Example Session Output

```
logs/diagnostics/session_20251026_195400/
├── 01_parser_slot1.json
├── 01_parser_slot2.json
├── 01_parser_slot3.json
├── 01_parser_slot4.json
├── 01_parser_slot5.json
├── 02_lesson_json_slot1.json
├── 02_lesson_json_slot2.json
├── 02_lesson_json_slot3.json
├── 02_lesson_json_slot4.json
├── 02_lesson_json_slot5.json
├── 03_before_render_slot1.json
├── 03_before_render_slot2.json
├── 03_before_render_slot3.json
├── 03_before_render_slot4.json
├── 03_before_render_slot5.json
├── 04_renderer_metadata_extracted.json
├── 05_filtering_context.json (multiple)
├── 06_hyperlink_filtered.json (multiple)
├── 07_hyperlink_placed.json (multiple)
├── session_log.json
└── summary.json
```

---

**This diagnostic system will definitively show where metadata is lost or filtering fails!** 🔍

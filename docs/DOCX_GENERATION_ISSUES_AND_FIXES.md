# DOCX Generation Issues and Fixes

## Issues Identified

### Issue 1: Two DOCX Files Generated Instead of One

**Problem:**
When processing multiple slots, the system was generating two DOCX files:
1. The final merged lesson plan DOCX file
2. Temporary DOCX files (`_temp_slot{slot_number}_{subject}.docx`) that weren't being cleaned up properly

**Root Cause:**
In the multi-slot processing path (`_combine_lessons_impl`), the code:
1. Creates temporary DOCX files for each slot (line ~1745)
2. Merges them into a final DOCX file
3. Attempts to clean up temp files (line ~1834), but:
   - The cleanup only checked if `unlink()` succeeded, not if the file existed
   - If cleanup failed silently, temp files remained in the output folder

**Fix Applied:**
- Enhanced temp file cleanup to check if file exists before attempting deletion
- Added debug logging to track successful temp file deletions
- Ensured cleanup happens even if there are errors in other parts of the process

**Location:** `tools/batch_processor.py` lines 1858-1872

---

### Issue 2: Objectives DOCX File Not Generated

**Problem:**
The objectives DOCX file (with student goal in large bold text and WIDA objective in 50% gray) was not being generated, even though the code exists in `backend/services/objectives_printer.py`.

**Root Cause:**
The `ObjectivesPrinter.generate_docx()` method exists and is fully implemented, but it was never called from the batch processor after the main lesson plan DOCX was created.

**Fix Applied:**
Added objectives DOCX generation in two places:
1. **Single-slot path** (line ~1699): After saving the main DOCX and JSON, generate objectives DOCX
2. **Multi-slot path** (line ~1833): After saving the merged DOCX and JSON, generate objectives DOCX

The objectives file is named: `{main_filename}_objectives.docx`

**Location:** 
- Single-slot: `tools/batch_processor.py` lines 1699-1722
- Multi-slot: `tools/batch_processor.py` lines 1833-1856

**Error Handling:**
- Objectives generation failures are logged as warnings but don't fail the entire process
- This ensures lesson plan generation succeeds even if objectives generation has issues

---

## File Differences Explained

### Main Lesson Plan DOCX
- **Purpose:** Full lesson plan with all details (objectives, anticipatory set, tailored instruction, etc.)
- **Content:** Complete lesson plan tables with bilingual enhancements
- **Format:** Uses the lesson plan template

### Objectives DOCX
- **Purpose:** Simplified objectives-only document for quick reference
- **Content:** 
  - Header: Date | Subject | Grade | Homeroom (10pt)
  - Student Goal: Large bold text (48pt base, auto-scaled to fit 3/4 of page)
  - Separator: Thin gray line
  - WIDA Objective: Smaller text in 50% gray (14pt base, auto-scaled to fit 1/4 of page)
- **Format:** Landscape orientation, one lesson per page
- **Naming:** `{main_filename}_objectives.docx`

### Temporary DOCX Files (Should Be Deleted)
- **Purpose:** Intermediate files created during multi-slot processing
- **Naming:** `_temp_slot{slot_number}_{subject}.docx`
- **Status:** Should be automatically deleted after merging
- **Issue:** Were sometimes left behind if cleanup failed

---

## Testing Recommendations

1. **Test single-slot generation:**
   - Verify main DOCX is created
   - Verify objectives DOCX is created with `_objectives.docx` suffix
   - Verify JSON file is created
   - Verify no temp files remain

2. **Test multi-slot generation:**
   - Verify merged DOCX is created
   - Verify objectives DOCX is created with `_objectives.docx` suffix
   - Verify JSON file is created
   - Verify all temp files (`_temp_slot*.docx`) are deleted
   - Verify only 3 files remain: main DOCX, objectives DOCX, JSON

3. **Test objectives DOCX content:**
   - Verify student goal appears in large bold text
   - Verify WIDA objective appears in 50% gray
   - Verify header contains correct date, subject, grade, homeroom
   - Verify one page per lesson/slot

---

## Code References

- Objectives Printer: `backend/services/objectives_printer.py`
- Batch Processor: `tools/batch_processor.py`
- Main DOCX Renderer: `tools/docx_renderer.py`


# Objectives PDF Metadata Mismatch - FIX COMPLETE

## Problem Identified
The HTML/PDF generation for Student Goals and WIDA objectives had a metadata mismatch issue where the headers displayed incorrect subject information that didn't match the actual lesson content.

### Root Cause
1. **ObjectivesPDFGenerator** was using only the top-level `metadata.subject` field for all days
2. **ObjectivesPrinter** was using slot-level subject but could fall back to incorrect metadata
3. In multi-subject weeks (e.g., "ELA / Math"), headers would show the same subject for all days regardless of actual content

## Solution Implemented

### 1. Added Subject Detection Function
Created `extract_subject_from_unit_lesson()` function that:
- Parses the `unit_lesson` text to detect the actual subject
- Uses pattern matching for explicit subject prefixes (Math, ELA, Science, etc.)
- Uses keyword matching for subject-specific terms
- Falls back to "Unknown" if no subject is detected

### 2. Updated ObjectivesPDFGenerator
- Modified `extract_objectives()` to use detected subject from `unit_lesson`
- Only falls back to metadata if `unit_lesson` exists but no subject is detected
- Headers now correctly match the lesson content

### 3. Updated ObjectivesPrinter
- Improved subject detection logic with proper priority:
  1. Slot subject (if different from metadata)
  2. Detected from `unit_lesson`
  3. Metadata subject (as last resort)
- Better handling of multi-slot scenarios

## Test Results
✅ All main tests passing
- Mixed subjects in a single week: Correctly detected
- Multi-subject metadata: Properly handled
- "No School" days: Correctly skipped
- Edge cases: Acceptably handled

## Examples of Fixed Behavior

### Before Fix:
```
Metadata: subject="ELA / Math"
Monday Header: "11/17/2024 | ELA / Math | Grade 3 | Room 15"
Tuesday Header: "11/18/2024 | ELA / Math | Grade 3 | Room 15"
Wednesday Header: "11/19/2024 | ELA / Math | Grade 3 | Room 15"
```

### After Fix:
```
Monday Unit: "Unit 3 Lesson 9: MEASURE TO FIND THE AREA"
Monday Header: "11/17/2024 | Math | Grade 3 | Room 15"

Tuesday Unit: "ELA Unit 2: READING COMPREHENSION STRATEGIES"
Tuesday Header: "11/18/2024 | ELA | Grade 3 | Room 15"

Wednesday Unit: "Science Lab: PLANT GROWTH EXPERIMENT"
Wednesday Header: "11/19/2024 | Science | Grade 3 | Room 15"
```

## Files Modified
1. `backend/services/objectives_pdf_generator.py`
   - Added `extract_subject_from_unit_lesson()` function
   - Updated `extract_objectives()` to use detected subject

2. `backend/services/objectives_printer.py`
   - Added `extract_subject_from_unit_lesson()` function
   - Updated `extract_objectives()` with improved subject detection logic

## Impact
- Headers in generated HTML/PDF documents now accurately reflect the lesson content
- Teachers can easily identify the subject for each day's objectives
- Multi-subject weeks are properly handled
- No breaking changes - existing functionality preserved

## Future Considerations
- The subject detection patterns can be expanded if new subjects are added
- The function could be moved to a shared utility module to avoid duplication
- Consider adding unit tests for the detection patterns

# Enhanced Warning Messages

**Date:** 2025-12-13  
**Status:** ✅ Implemented

## Overview

Enhanced slot mismatch warning messages to provide clearer, more actionable guidance. Warnings now distinguish between expected and unexpected mismatches, and provide context about document structure.

## Changes Made

### 1. Enhanced `slot_subject_mismatch` Warning

**Before:**
- Generic warning with minimal context
- No distinction between expected and unexpected mismatches
- No actionable guidance

**After:**
- Two distinct warning types:
  - `slot_subject_mismatch_single_slot`: For single-slot documents (expected behavior)
  - `slot_subject_mismatch_multi_slot`: For multi-slot documents (informational)
- Includes human-readable message
- Provides document structure context
- Suggests fixes for multi-slot mismatches

### 2. Enhanced `slot_auto_mapped` Warning

**Before:**
- Basic information about auto-mapping
- No context about why it happened

**After:**
- Includes human-readable message explaining the behavior
- Clarifies this is expected for single-slot documents
- Provides document structure context

## Warning Types

### `slot_subject_mismatch_single_slot`

**When:** Slot number mismatch in a single-slot document

**Example:**
```
Slot 2 requested, but document 'T. Santiago SS Plans 12_15.docx' has only 1 slot. 
Content correctly extracted from slot 1. This is expected behavior for single-slot documents.
```

**Extra Fields:**
- `requested_slot`: User's configured slot number
- `actual_slot`: Always 1 for single-slot documents
- `subject`: Subject name
- `file`: Document filename
- `available_slots`: Always 1
- `is_single_slot`: true
- `is_expected`: true
- `message`: Human-readable explanation
- `teacher`: Teacher name
- `grade`: Grade level
- `homeroom`: Homeroom identifier

**Action:** None required - this is expected behavior

---

### `slot_subject_mismatch_multi_slot`

**When:** Slot number mismatch in a multi-slot document

**Example:**
```
Slot 4 requested for 'Science', but document 'Morais 12_15 - 12_19.docx' has 'Science' 
in slot 3. Content correctly extracted via subject-based detection. 
Consider updating slot configuration to match document structure (slot 3).
```

**Extra Fields:**
- `requested_slot`: User's configured slot number
- `actual_slot`: Actual slot number in document
- `subject`: Subject name
- `file`: Document filename
- `available_slots`: Total slots in document
- `is_single_slot`: false
- `is_expected`: false (informational only)
- `message`: Human-readable explanation with fix suggestion
- `teacher`: Teacher name
- `grade`: Grade level
- `homeroom`: Homeroom identifier

**Action:** Optional - consider updating slot configuration to match document structure

---

### `slot_auto_mapped`

**When:** Requested slot exceeds available slots, auto-mapped to slot 1

**Example:**
```
Slot 5 requested, but document 'Mrs. Grande Science 12_15 12_19.docx' has only 1 slot(s). 
Auto-mapped to slot 1. This is expected behavior for single-slot documents.
```

**Extra Fields:**
- `requested_slot`: User's configured slot number
- `available_slots`: Total slots in document
- `mapped_to`: Always 1
- `subject`: Subject name
- `file`: Document filename
- `message`: Human-readable explanation
- `teacher`: Teacher name
- `grade`: Grade level
- `homeroom`: Homeroom identifier

**Action:** None required - this is expected behavior

## Benefits

1. **Clearer Communication:**
   - Users understand why warnings appear
   - Distinction between expected and unexpected behavior
   - Human-readable messages in logs

2. **Actionable Guidance:**
   - Multi-slot mismatches include fix suggestions
   - Context about document structure
   - Clear indication of expected vs unexpected

3. **Better Debugging:**
   - More context in log fields
   - Easier to filter and analyze warnings
   - Document structure information included

4. **Reduced Confusion:**
   - Single-slot warnings clearly marked as expected
   - Multi-slot warnings provide context
   - Users know when action is needed vs when it's informational

## Usage in Logs

### Filtering Warnings

**Expected warnings (can be filtered out):**
```python
# Filter single-slot mismatches (expected)
logger.warning("slot_subject_mismatch_single_slot", ...)

# Filter auto-mapping (expected)
logger.warning("slot_auto_mapped", ...)
```

**Informational warnings (review but not critical):**
```python
# Multi-slot mismatches (informational)
logger.warning("slot_subject_mismatch_multi_slot", ...)
```

### Log Analysis

**Example log entry:**
```json
{
  "event": "slot_subject_mismatch_multi_slot",
  "level": "warning",
  "timestamp": "2025-12-13T10:30:00Z",
  "extra": {
    "requested_slot": 4,
    "actual_slot": 3,
    "subject": "Science",
    "file": "Morais 12_15 - 12_19.docx",
    "available_slots": 4,
    "is_single_slot": false,
    "is_expected": false,
    "message": "Slot 4 requested for 'Science', but document 'Morais 12_15 - 12_19.docx' has 'Science' in slot 3. Content correctly extracted via subject-based detection. Consider updating slot configuration to match document structure (slot 3).",
    "teacher": "Catarina Morais",
    "grade": "2",
    "homeroom": "310"
  }
}
```

## Migration Notes

**No breaking changes:**
- Old `slot_subject_mismatch` warnings still work
- New warning types are more specific
- Log analysis tools can filter by new types

**Recommended:**
- Update log analysis to use new warning types
- Filter out expected warnings (single-slot, auto-mapped)
- Review multi-slot mismatches for configuration improvements

## Testing

**Test Cases:**
1. ✅ Single-slot document with slot mismatch → `slot_subject_mismatch_single_slot`
2. ✅ Multi-slot document with slot mismatch → `slot_subject_mismatch_multi_slot`
3. ✅ Requested slot > available slots → `slot_auto_mapped`
4. ✅ Perfect match → No warning

## Future Enhancements

**Potential improvements:**
1. Add warning severity levels (INFO, WARNING, ERROR)
2. Include document structure summary in warnings
3. Provide one-click fix suggestions in UI
4. Track warning frequency per user/slot

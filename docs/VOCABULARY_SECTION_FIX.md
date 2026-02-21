# Vocabulary / Cognate Awareness Section Fix

## Problem Summary

The 'Vocabulary / Cognate Awareness:' section was missing from some lessons (initially observed on Wednesday lessons) while the 'Sentence Frames / Stems / Questions:' section appeared consistently for all lessons.

## Root Cause Analysis

### Primary Issue
In `backend/api.py` (line 2907), the Vocabulary / Cognate Awareness section was only created if `vocabulary_cognates` was truthy:

```python
if vocabulary_cognates:
    # Create vocabulary step...
```

This meant:
- If `vocabulary_cognates` was `None`, the section was not created
- If `vocabulary_cognates` was an empty list `[]`, the section was not created
- Only when `vocabulary_cognates` had items would the section appear

### Why Some Days Were Affected
The pattern of missing vocabulary sections on certain days (initially observed on Wednesday) suggests:
1. The LLM may have been generating empty arrays `[]` for some days' `vocabulary_cognates` instead of 6 items
2. Validation might not have been catching empty arrays properly
3. There could be a parsing issue where some days' data was being lost during processing

### Why Sentence Frames Always Appeared
Sentence Frames had the same conditional check, but `sentence_frames` was consistently being generated correctly by the LLM, indicating the issue was specific to `vocabulary_cognates` generation or extraction.

## Solutions Implemented

### 1. Made Vocabulary Section Mandatory (backend/api.py)

**Change**: Modified the code to always create the Vocabulary / Cognate Awareness section, even if `vocabulary_cognates` is empty.

**Before**:
```python
if vocabulary_cognates:
    # Only create if vocabulary_cognates exists
```

**After**:
```python
should_create_vocab_step = True
if not vocabulary_cognates or (isinstance(vocabulary_cognates, list) and len(vocabulary_cognates) == 0):
    # Log warning but still create the section
    logger.warning(...)
    
if should_create_vocab_step:
    # Always create the section
    # Use placeholder content if vocabulary_cognates is empty
```

**Benefits**:
- Ensures consistency across all lesson plans
- The section will always appear, even if vocabulary data is missing
- Provides a placeholder message when vocabulary is missing, alerting users to the issue

### 2. Enhanced Validation (backend/llm_service.py)

**Change**: Added explicit check for empty arrays in validation logic.

**Before**:
```python
elif len(vocab) != 6:
    missing_fields.append(f"{day_name}.vocabulary_cognates (has {len(vocab)} items, need exactly 6)")
```

**After**:
```python
elif len(vocab) == 0:
    missing_fields.append(f"{day_name}.vocabulary_cognates (empty array - must have exactly 6 items)")
elif len(vocab) != 6:
    missing_fields.append(f"{day_name}.vocabulary_cognates (has {len(vocab)} items, need exactly 6)")
```

**Benefits**:
- Catches empty arrays explicitly
- Provides clearer error messages
- Forces LLM to regenerate with proper vocabulary data

### 3. Strengthened Prompt (docs/prompt_v4.md & backend/llm_service.py)

**Change**: Added explicit reminders that all days require vocabulary_cognates.

**Additions**:
- Multiple reminders that vocabulary_cognates is mandatory for ALL days
- Clear emphasis that no day should be skipped
- Generic requirement that applies to all days equally

**Benefits**:
- Reduces likelihood of LLM skipping vocabulary for any day
- Makes requirements crystal clear
- Ensures consistent application across all days

### 4. Enhanced Logging (backend/api.py)

**Change**: Added warning logs when vocabulary_cognates is missing.

**Benefits**:
- Tracks when and why vocabulary sections are missing
- Helps identify patterns in missing data
- Provides debugging information for future issues

## Expected Behavior After Fix

1. **Vocabulary / Cognate Awareness section will ALWAYS appear** in all lesson plans, regardless of whether `vocabulary_cognates` data is present
2. **If vocabulary_cognates is missing or empty**, the section will display a placeholder message alerting that vocabulary should be included
3. **Validation will catch empty arrays** and force the LLM to regenerate with proper vocabulary data
4. **Enhanced prompts** reduce the likelihood of the LLM omitting vocabulary for any day, especially Wednesday

## Testing Recommendations

1. Generate a new lesson plan and verify that all days (Monday-Friday) have the Vocabulary / Cognate Awareness section
2. Check logs for any warnings about missing vocabulary_cognates
3. Verify that validation catches and rejects lesson plans with empty vocabulary_cognates arrays
4. Test with Wednesday lessons specifically to ensure the pattern is resolved

## Related Files Modified

- `backend/api.py` - Main logic for creating vocabulary sections
- `backend/llm_service.py` - Validation and error feedback
- `docs/prompt_v4.md` - LLM prompt enhancements

## Additional Notes

- The fix maintains backward compatibility - existing lesson plans with vocabulary_cognates will continue to work as before
- The placeholder message in empty vocabulary sections serves as a visual indicator that vocabulary data should be added
- This fix ensures consistency with the Sentence Frames section, which was already appearing for all lessons


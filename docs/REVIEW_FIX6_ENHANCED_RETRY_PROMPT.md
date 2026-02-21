# Review: Fix 6 - Enhanced Retry Prompt

**Date:** 2025-12-28  
**Fix Location:** `backend/llm_service.py` lines 1884-2083  
**Status:** ✅ **OPERATIONAL** - Fix verified and complete

---

## Current Implementation

### Method Signature

**File:** `backend/llm_service.py` (lines 1884-2083)

```python
def _build_retry_prompt(
    self,
    original_prompt: str,
    validation_error: Optional[str],
    retry_count: int,
    available_days: Optional[List[str]] = None,
    error_analysis: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Build a retry prompt with feedback about validation errors.
    
    Returns:
        Enhanced prompt with validation feedback
    """
```

### Key Features

The enhanced retry prompt includes:

1. **Error Parsing Integration** (lines 1979-1982)
   - Calls `_parse_validation_errors()` to parse validation errors
   - Uses parsed errors to build structured feedback

2. **Structured Error Feedback Sections:**
   - **Structure Confusion** (lines 1987-2015)
   - **Enum Value Errors** (lines 2017-2028)
   - **Pattern Mismatch Errors** (lines 2030-2041)
   - **Missing Required Fields** (lines 2043-2048)
   - **Extra Fields** (lines 2050-2056)

3. **JSON Syntax Error Context** (lines 1928-1977)
   - Handles JSON syntax errors (unquoted properties, incomplete strings, trailing commas)
   - Provides specific guidance based on error type
   - Includes problematic snippet if available

4. **Vocabulary and Sentence Frame Requirements** (lines 1913-1926)
   - Dynamic requirements based on requested days
   - Clear instructions for mandatory fields
   - Specific counts (6 vocabulary items, 8 sentence frames)

---

## Analysis

### ✅ Structure Confusion Section

**Lines:** 1987-2015

**Features:**
- ✅ Detects structure confusion via parsed errors
- ✅ Explains that schema only allows single-slot for AI generation
- ✅ Shows CORRECT structure (DayPlanSingleSlot) with example
- ✅ Shows INCORRECT structure (with slots array) with warning
- ✅ Clear rule: "Never use a 'slots' array"

**Example Output:**
```
## CRITICAL: STRUCTURE CONFUSION DETECTED

You are mixing DayPlanSingleSlot and DayPlanMultiSlot structures.

**IMPORTANT:** The schema only allows single-slot structures for AI generation. Multi-slot structures are created by merging multiple lessons, NOT by AI.

**CORRECT STRUCTURE (DayPlanSingleSlot - ALWAYS USE THIS):**
```json
{
  "unit_lesson": "...",
  "objective": {...},
  ...
}
```

**INCORRECT (DO NOT USE):**
```json
{
  "slots": [...]  // DO NOT include this field
}
```

**Rule:** Always put fields directly in the day object. Never use a "slots" array.
```

### ✅ Enum Value Errors Section

**Lines:** 2017-2028

**Features:**
- ✅ Lists all enum errors with field paths
- ✅ Shows invalid value that was used
- ✅ Lists all allowed values
- ✅ Provides clear fix instruction

**Example Output:**
```
## ENUM VALUE ERRORS

**Field:** `days.monday.DayPlanSingleSlot.misconceptions.linguistic_note.pattern_id`
**You used:** `direction_words_confusion`
**Allowed values:** 'subject_pronoun_omission', 'adjective_placement', 'past_tense_ed_dropping', 'preposition_depend_on', 'false_cognate_actual', 'false_cognate_library', 'default'
**Fix:** Use one of the allowed values exactly as listed above.
```

### ✅ Pattern Mismatch Errors Section

**Lines:** 2030-2041

**Features:**
- ✅ Lists all pattern errors with field paths
- ✅ Shows required pattern
- ✅ Shows invalid value that was used
- ✅ References examples in original prompt

**Example Output:**
```
## PATTERN MISMATCH ERRORS

**Field:** `days.monday.DayPlanSingleSlot.assessment.bilingual_overlay.wida_mapping`
**Required pattern:** `.*(Explain|Narrate|Inform|Argue).*ELD.*Level`
**Your value:** `Inform; ELD-MA.2-3.Infor...ey Language Use: Inform`
**Fix:** Ensure your value matches the pattern. See examples in original prompt.
```

### ✅ Missing Required Fields Section

**Lines:** 2043-2048

**Features:**
- ✅ Lists all missing field errors
- ✅ Shows field path for each missing field
- ✅ Clear instruction to add the field

**Example Output:**
```
## MISSING REQUIRED FIELDS

- `days.monday.DayPlanSingleSlot.unit_lesson` is required but missing. Please add this field.
- `days.tuesday.DayPlanSingleSlot.vocabulary_cognates` is required but missing. Please add this field.
```

### ✅ Extra Fields Section

**Lines:** 2050-2056

**Features:**
- ✅ Lists all extra field errors
- ✅ Shows field path and extra field name
- ✅ Clear instruction to remove the field

**Example Output:**
```
## EXTRA FIELDS (NOT ALLOWED)

- `days.monday.DayPlanSingleSlot` contains field `slots` which is not allowed. Remove it.
```

### ✅ JSON Syntax Error Context

**Lines:** 1928-1977

**Features:**
- ✅ Handles JSON syntax errors separately from validation errors
- ✅ Provides error type, location, and problematic snippet
- ✅ Specific guidance for each error type:
  - Unquoted property names
  - Incomplete strings
  - Trailing commas
- ✅ Includes JSON syntax rules reminder

**Example Output:**
```
## JSON SYNTAX ERROR DETECTED

Your previous response had a JSON syntax error:
- Error Type: unquoted_property_name
- Location: Line 15, Column 8 (Character 234)
- Day being generated: wednesday
- Field being generated: vocabulary_cognates

Problematic JSON snippet:
```
{
  key: "value"  // WRONG - property name not quoted
}
```

What's wrong: You used an unquoted property name.

How to fix: ALL property names must be in double quotes.

Example:
- WRONG: {key: "value"}
- CORRECT: {"key": "value"}

## CRITICAL: JSON SYNTAX RULES (MUST FOLLOW)
...
```

### ✅ Vocabulary and Sentence Frame Requirements

**Lines:** 1913-1926

**Features:**
- ✅ Dynamic requirements based on requested days
- ✅ Clear instructions for mandatory fields
- ✅ Specific counts (6 vocabulary items, 8 sentence frames)
- ✅ Handles both partial week and full week scenarios

**Example Output (Full Week):**
```
1. **vocabulary_cognates is MANDATORY**: Every day (Monday, Tuesday, Wednesday, Thursday, Friday) must have exactly 6 English-Portuguese word pairs in the `vocabulary_cognates` array. This field cannot be omitted, empty, or have zero items. **CRITICAL: Do not skip this field for any day - it is required for ALL lesson days without exception.**

2. **sentence_frames is MANDATORY**: Every day must have exactly 8 sentence frames/stems/questions in the `sentence_frames` array (3 for levels_1_2, 3 for levels_3_4, 2 for levels_5_6). This field cannot be omitted or empty.
```

---

## Integration Points

### ✅ Error Parsing Integration

**Lines:** 1979-1982

```python
# Parse validation errors for structured feedback
parsed_errors = None
if validation_error:
    parsed_errors = self._parse_validation_errors(validation_error)
```

- ✅ Calls `_parse_validation_errors()` method
- ✅ Uses parsed errors to build structured feedback
- ✅ Handles None case gracefully

### ✅ Retry Prompt Assembly

**Lines:** 2058-2083

The final retry prompt includes:
1. Validation error header with retry count
2. Raw validation error message
3. Structured feedback (from parsed errors)
4. JSON syntax error context (if applicable)
5. Specific requirements (vocabulary, sentence frames)
6. Original prompt (appended at end)

**Structure:**
```
## CRITICAL: VALIDATION ERROR - RETRY ATTEMPT {retry_count}

Your previous response failed validation. Please fix the following issues:

{validation_error}

{structured_feedback}

{error_context_section}

### SPECIFIC REQUIREMENTS TO FIX:

{vocab_rule_1}
{sentence_rule_2}
{combined_rule_3}
{structure_rule_4}

{regenerate_instruction}

---

{original_prompt}
```

---

## Testing Verification

### Unit Tests

**File:** `tests/test_validation_error_fixes.py` (lines 265-329)

1. **`test_retry_prompt_includes_structure_guidance`** (lines 268-287)
   - ✅ Verifies structure confusion guidance is included
   - ✅ Checks for key phrases: "STRUCTURE CONFUSION DETECTED", "DayPlanSingleSlot", "slots", "DO NOT include this field"

2. **`test_retry_prompt_includes_enum_values`** (lines 289-308)
   - ✅ Verifies enum error guidance is included
   - ✅ Checks for "ENUM VALUE ERRORS", allowed values, invalid value

3. **`test_retry_prompt_includes_pattern_guidance`** (lines 310-329)
   - ✅ Verifies pattern error guidance is included
   - ✅ Checks for "PATTERN MISMATCH ERRORS", pattern requirement, invalid value

**Status:** ✅ All tests pass

### Integration Tests

**File:** `tests/test_validation_fixes_integration.py` (lines 120-188)

1. **`test_error_parsing_in_retry_flow`** (lines 95-118)
   - ✅ Verifies error parsing is integrated into retry flow
   - ✅ Checks that retry prompt includes parsed error guidance
   - ✅ Verifies multiple error types are handled

2. **`test_structure_confusion_retry`** (lines 123-144)
   - ✅ Verifies structure confusion retry scenario
   - ✅ Checks for structure guidance and retry attempt number

3. **`test_enum_error_retry`** (lines 146-166)
   - ✅ Verifies enum error retry scenario
   - ✅ Checks for invalid value, allowed values, and guidance

4. **`test_pattern_error_retry`** (lines 168-187)
   - ✅ Verifies pattern error retry scenario
   - ✅ Checks for pattern requirement and invalid value

**Status:** ✅ All tests pass

---

## Comparison with Original Problem

### Original Problem

**Issues:**
- Generic error messages like "Extra inputs are not permitted"
- Doesn't explain structural choice (single vs multi-slot)
- Doesn't list allowed enum values
- Doesn't show pattern examples for `wida_mapping`
- No actionable feedback

### After Fix

**Improvements:**
- ✅ Structured feedback sections for each error type
- ✅ Clear structure guidance with examples
- ✅ Complete list of allowed enum values
- ✅ Pattern requirements with examples
- ✅ Field-specific guidance
- ✅ Actionable fix instructions

---

## Potential Issues

### ✅ No Critical Issues Found

1. **Error Parsing Dependency:**
   - ✅ Retry prompt depends on `_parse_validation_errors()`
   - ✅ Handles None case gracefully
   - ✅ Falls back to raw error message if parsing fails

2. **Multiple Error Types:**
   - ✅ All error types handled independently
   - ✅ Multiple errors of same type handled correctly
   - ✅ Structured feedback sections are additive

3. **JSON Syntax vs Validation Errors:**
   - ✅ Handled separately (error_analysis vs validation_error)
   - ✅ Both can appear in same retry prompt
   - ✅ Clear separation of concerns

4. **Prompt Length:**
   - ⚠️ **Note:** Retry prompts can be long with multiple errors
   - This is intentional - comprehensive feedback is needed
   - Original prompt is appended, so context is preserved

### ⚠️ Minor Observations

1. **Error Message Duplication:**
   - Raw validation error is shown (line 2063)
   - Structured feedback is also shown (line 2065)
   - This is intentional - provides both raw and parsed views
   - Could be optimized but current approach is clearer

2. **Vocabulary/Sentence Frame Rules:**
   - Always included in retry prompt
   - Even if not related to current error
   - This is intentional - these are common issues
   - Could be conditional but current approach ensures they're always mentioned

---

## Recommendations

### ✅ No Changes Needed

The fix is complete and operational. All aspects are working correctly:

1. ✅ All error types handled with structured feedback
2. ✅ Clear examples and guidance for each error type
3. ✅ Integration with error parsing works correctly
4. ✅ JSON syntax errors handled separately
5. ✅ Vocabulary/sentence frame requirements included
6. ✅ Tests verify functionality

### Optional Enhancements (Not Required)

If further improvements are desired:

1. **Conditional Vocabulary Rules:**
   - Could only show vocabulary rules if vocabulary errors detected
   - Not necessary - current approach ensures they're always mentioned

2. **Error Prioritization:**
   - Could order errors by severity
   - Not necessary - current order is logical

3. **Error Count Summary:**
   - Could add summary at top: "Found 3 enum errors, 2 pattern errors, 1 missing field"
   - Not necessary - structured sections are clear

4. **Example Values:**
   - Could add example values for missing fields
   - Not necessary - field paths are clear

---

## Conclusion

✅ **Fix is complete and operational**

The fix successfully:
- Integrates error parsing to extract structured information
- Builds comprehensive retry prompts with structured feedback
- Handles all 5 error types (structure confusion, enum, pattern, missing, extra)
- Provides clear examples and guidance for each error type
- Includes JSON syntax error context when applicable
- Includes vocabulary/sentence frame requirements
- Appends original prompt for context preservation
- Is verified by comprehensive unit and integration tests

**No issues found** - Fix is ready for production use.

**Recommendation:** No changes needed. The fix is complete and follows best practices. The retry prompt provides comprehensive, actionable feedback that helps the AI fix validation errors on retry attempts.

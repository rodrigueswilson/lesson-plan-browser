# Error Analysis: Objectives File Generation

**Date**: 2025-12-14  
**Issue**: Objectives DOCX file created successfully, but HTML and PDF files are not generated.

## Executive Summary

The primary blocker preventing HTML and PDF generation was a **NameError** in the `objectives_pdf_generator.py` file where the `metadata` variable was undefined in the `_extract_from_slot` method.

## Error Categorization

### 🔴 Critical Errors (Blocking)

#### 1. NameError: name 'metadata' is not defined
- **Location**: `backend/services/objectives_pdf_generator.py:473`
- **Method**: `_extract_from_slot`
- **Error Type**: `NameError`
- **Impact**: Prevents HTML and PDF generation completely
- **Root Cause**: The `metadata` parameter was not included in the method signature but was being used in the method body
- **Status**: ✅ **FIXED**
  - Added `metadata: Dict[str, Any]` parameter to `_extract_from_slot` method signature
  - Updated the method call in `extract_objectives` to pass `metadata` parameter

**Error Traceback:**
```
File "D:\LP\backend\services\objectives_pdf_generator.py", line 473, in _extract_from_slot
    slot_teacher = get_teacher_name(metadata, slot=slot)
                                       ^^^^^^^^
NameError: name 'metadata' is not defined
```

**Fix Applied:**
- Modified method signature to include `metadata` parameter
- Updated method call site to pass `metadata` from `extract_objectives`

---

### 🟡 Warnings (Non-blocking, but should be addressed)

#### 2. Objective Validation Failures
- **Type**: Pydantic validation errors
- **Location**: Multiple objectives with invalid WIDA ELD code format
- **Impact**: Objectives may not be properly formatted, but generation continues
- **Example Error**:
  ```
  wida_objective must include an ELD code with domain(s) 
  (e.g., ELD-SS.6-8.Explain.Writing or ELD-SS.6-8.Explain.Listening/Speaking)
  ```
- **Invalid Format Found**: `ELD-LA.2-3.Explain/Speaking/Writing`
  - Issue: Uses forward slashes instead of dots for domain separation after function name
  - Valid format should be: `ELD-LA.2-3.Explain.Speaking/Writing` (dot before first domain, slashes between multiple domains)
- **Status**: ✅ **FIXED**
  - Added normalization step in `validate_wida_objective` to automatically fix common format mistakes
  - Transforms `ELD-XX.#-#.Function/Domain` to `ELD-XX.#-#.Function.Domain`
  - Fix applied in: `backend/models_slot.py`

**Affected Objectives:**
- Thursday, Slot 6, Science: Invalid ELD format detected
- Multiple instances throughout the lesson plan

#### 4. Student Goal Invalid Domain Tags (NEW)
- **Type**: Pydantic validation errors
- **Location**: Student goal domain tag validation
- **Error Message**:
  ```
  student_goal domain tag may only include listening, reading, speaking, or writing
  Input: "I will show how matter is arranged with pictures and words (drawing, writing)."
  ```
- **Issue**: LLM generates invalid domain names like "drawing" instead of valid WIDA domains
- **Impact**: Validation fails for objectives with invalid domain tags
- **Status**: ✅ **FIXED**
  - Added normalization to map common invalid domain names to valid ones:
    - "drawing" → "writing"
    - "illustrate" → "writing"
    - "demonstrate" → "speaking"
    - "show" → "speaking"
    - "present" → "speaking"
  - Automatically deduplicates domains after normalization
  - Updates the student_goal text with normalized domain tags
  - Fix applied in: `backend/models_slot.py` - `validate_student_goal()` method

**Affected Objectives:**
- Tuesday, Slot 6, Science: Invalid domain tag "(drawing, writing)"

#### 3. Structured Outputs Fallback Warnings
- **Type**: OpenAI API schema validation warnings
- **Event**: `structured_outputs_failed_fallback`
- **Original Error Message**: 
  ```
  Invalid schema for response_format 'bilingual_lesson_plan': 
  In context=(), 'oneOf' is not permitted.
  ```
- **New Error Message (after oneOf fix)**:
  ```
  Invalid schema for response_format 'bilingual_lesson_plan': 
  In context=(), 'required' is required to be supplied and to be an array including 
  every key in properties. Missing 'subject'.
  ```
- **Impact**: System falls back to alternative generation method, but may affect output quality
- **Frequency**: Multiple occurrences during lesson plan generation
- **Status**: ✅ **FIXED** (Updated)
  - Added schema transformation to convert `oneOf` to `anyOf` when building OpenAI structured schema
  - **NEW**: Added logic to remove optional properties (properties not in `required` array) when transforming for OpenAI
  - OpenAI structured outputs API requires all properties to be in the `required` array
  - Fix applied in: `backend/llm_service.py` - `_transform_oneof_for_openai()` method (enhanced)
  - Schema is automatically transformed before being sent to OpenAI API

---

## Fixed Issues

### ✅ Issue #1: Missing metadata parameter
- **File**: `backend/services/objectives_pdf_generator.py`
- **Lines Modified**: 
  - Line 457-467: Added `metadata` parameter to method signature
  - Line 431-440: Updated method call to pass `metadata`
- **Status**: Fixed and ready for testing

### ✅ Issue #2: WIDA ELD Code Format Validation
- **File**: `backend/models_slot.py`
- **Fix Applied**: Added normalization step in `validate_wida_objective` validator
- **What it does**: Automatically fixes common ELD code format mistakes before validation
- **Pattern Fixed**: `ELD-XX.#-#.Function/Domain` → `ELD-XX.#-#.Function.Domain`
- **Status**: Fixed and ready for testing

### ✅ Issue #3: OpenAI Structured Outputs Schema Issues
- **File**: `backend/llm_service.py`
- **Fix Applied**: Enhanced `_transform_oneof_for_openai()` method
- **What it does**: 
  1. Converts `oneOf` to `anyOf` (OpenAI doesn't support `oneOf`)
  2. Removes optional properties (properties not in `required` array) - OpenAI requires all properties to be required
- **Why**: OpenAI structured outputs API has strict requirements:
  - Doesn't support `oneOf` but accepts `anyOf`
  - All properties must be in the `required` array (no optional properties)
- **Status**: Fixed and ready for testing

### ✅ Issue #4: Student Goal Invalid Domain Tags
- **File**: `backend/models_slot.py`
- **Fix Applied**: Added domain name normalization in `validate_student_goal()` validator
- **What it does**: 
  - Maps common invalid domain names to valid WIDA domains
  - Automatically deduplicates domains
  - Updates the student_goal text with normalized domain tags
- **Status**: Fixed and ready for testing

### ✅ Issue #5: Analytics/Database Join Ambiguity Errors
- **File**: `backend/database.py`
- **Fix Applied**: Added explicit ON clauses to SQLAlchemy joins
- **What it does**: 
  - Explicitly specifies join condition: `PerformanceMetric.plan_id == WeeklyPlan.id`
  - Resolves SQLAlchemy's join ambiguity error
  - Applied to both `get_aggregate_stats()` and `get_daily_breakdown()` methods
- **Why**: SQLAlchemy couldn't infer the relationship between PerformanceMetric and WeeklyPlan without explicit ON clause
- **Status**: Fixed and ready for testing

---

## Testing Plan

### Immediate Testing
1. **Verify Fix**: Re-run objectives generation to confirm HTML and PDF files are created
2. **Check Logs**: Monitor for any remaining errors or warnings
3. **Validate Output**: Ensure generated files contain correct content

### Debug Mode Consideration
- **Current Status**: Debug mode available but not necessary for this fix
- **Recommendation**: Only enable if additional issues are discovered during testing
- **When to Use**: If HTML/PDF generation still fails after this fix, enable debug mode to get more detailed error information

---

## Next Steps

### Priority 1 (Immediate)
1. ✅ Fix NameError for metadata parameter - **COMPLETED**
2. ⏳ Test objectives generation end-to-end
3. ⏳ Verify HTML and PDF files are created successfully

### Priority 2 (Follow-up)
1. Fix WIDA ELD code format validation issues
2. Review and correct `bilingual_lesson_plan` JSON schema
3. Improve error handling and logging for better diagnostics

### Priority 3 (Future Improvements)
1. Add unit tests for `_extract_from_slot` method
2. Add validation tests for WIDA objective formats
3. Improve error messages for better debugging

---

## Files Modified

1. `backend/services/objectives_pdf_generator.py`
   - Added `metadata` parameter to `_extract_from_slot` method
   - Updated method call to pass `metadata` correctly

---

## Verification Steps

After applying the fix, verify:

1. **Backend Logs**: Check for successful PDF/HTML generation messages
2. **File System**: Verify both `.html` and `.pdf` files are created alongside `.docx`
3. **File Contents**: Ensure generated files contain all expected objectives
4. **No Errors**: Confirm no NameError or similar critical errors in logs

---

## Notes

- The DOCX generation was unaffected because it uses a different code path
- The error only affected the PDF/HTML generation code path
- All metadata helper functions (`get_teacher_name`, `get_homeroom`, `get_subject`) require the `metadata` dictionary to function properly
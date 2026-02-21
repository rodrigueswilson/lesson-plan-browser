# Live Error Monitoring Guide

**Date:** 2025-12-28  
**Purpose:** Monitor lesson plan generation for validation errors

---

## Key Log Messages to Watch For

### ✅ Success Indicators
- `llm_transform_success` - Transformation completed successfully
- `llm_instructor_dict_conversion_success` - Enum serialization worked
- `llm_validation_success` - Validation passed
- `llm_instructor_converting_to_dict` - Instructor path working (not falling back)

### ⚠️ Error Indicators

1. **Validation Failures:**
   - `llm_validation_failed_retry` - Validation failed, will retry
   - Look for: `retry_count`, `validation_error`, `parsed_errors`

2. **Retry Attempts:**
   - `llm_retry_attempt` - Retry attempt started
   - Look for: `retry_count`, `parsed_errors`

3. **Enum Serialization Issues:**
   - `llm_instructor_enum_serialization_fallback` - Enum serialization failed, using fallback
   - Should NOT occur with Fix 1

4. **Structure Confusion:**
   - Look for errors mentioning `DayPlanMultiSlot` or `slots` array
   - Should NOT occur with Fix 2

5. **Invalid Enum Values:**
   - Look for errors mentioning invalid `pattern_id` values
   - Should be reduced with Fix 3

6. **Pattern Mismatches:**
   - Look for `wida_mapping` pattern errors
   - Should be reduced with Fix 4

---

## Monitoring Commands

### Real-time Monitoring
```powershell
# Monitor backend logs in real-time
Get-Content logs\backend_20251228_183327.log -Wait -Tail 50

# Filter for validation errors only
Get-Content logs\backend_20251228_183327.log -Wait | Select-String "validation|retry|enum|error"
```

### Check Recent Errors
```powershell
# Get last 100 lines
Get-Content logs\backend_20251228_183327.log -Tail 100

# Search for specific error types
Select-String -Path logs\backend_20251228_183327.log -Pattern "llm_validation_failed|llm_retry_attempt|enum_serialization"
```

---

## What to Capture

When errors occur, capture:
1. **Error message** - Full validation error text
2. **Parsed errors** - Structured error information
3. **Retry count** - How many retries were needed
4. **Error types** - enum, pattern, missing_field, extra_field, structure_confusion
5. **Field paths** - Which fields had errors
6. **Invalid values** - What values were rejected

---

## Expected Behavior

### Before Fixes:
- Multiple `llm_validation_failed_retry` messages
- Multiple `llm_retry_attempt` messages (2-3+)
- `llm_instructor_enum_serialization_fallback` messages
- Generic error messages

### After Fixes:
- Fewer `llm_validation_failed_retry` messages (0-1)
- Fewer `llm_retry_attempt` messages (0-1)
- No `llm_instructor_enum_serialization_fallback` messages
- Structured `parsed_errors` with actionable feedback
- More `llm_transform_success` messages

---

## Error Analysis Checklist

When an error occurs, check:

- [ ] What error type? (enum, pattern, missing_field, extra_field, structure_confusion)
- [ ] Which field(s) had errors?
- [ ] What was the invalid value?
- [ ] Was error parsing working? (check `parsed_errors`)
- [ ] Did retry prompt help? (check if retry succeeded)
- [ ] Is this a new error type or edge case?

# Root Cause Analysis: Validation Errors Causing Retries

**Date:** 2025-12-28  
**Issue:** AI transformation retries (attempt 2+) with persistent validation errors  
**Impact:** Delayed processing, wasted tokens, failed transformations

---

## Executive Summary

The system is experiencing cascading validation failures that cause multiple retry attempts. The root causes are:

1. **Schema Ambiguity**: Pydantic schema allows both `DayPlanSingleSlot` and `DayPlanMultiSlot`, but prompt instructions are unclear
2. **Instructor Library Serialization Error**: Enum serialization failure causes fallback to legacy path
3. **Prompt-Schema Mismatch**: Prompt says "USE SINGLE-SLOT STRUCTURE" but schema allows both structures
4. **Invalid Enum Values**: AI generates enum values not in the allowed set
5. **WIDA Pattern Mismatch**: Generated `wida_mapping` strings don't match required regex pattern
6. **Inadequate Error Feedback**: Retry prompts don't clearly explain structural differences

---

## Detailed Root Cause Analysis

### 1. Schema Structure Ambiguity (CRITICAL)

**Problem:**
The Pydantic schema uses a union type that allows **both** structures:
```python
class DayPlan(RootModel[DayPlanSingleSlot | DayPlanMultiSlot]):
    root: DayPlanSingleSlot | DayPlanMultiSlot
```

**Two Valid Structures:**
- **DayPlanSingleSlot**: Flat structure with fields at root level
  ```json
  {
    "unit_lesson": "...",
    "objective": {...},
    "vocabulary_cognates": [...]
  }
  ```

- **DayPlanMultiSlot**: Nested structure with `slots` array
  ```json
  {
    "slots": [
      {
        "slot_number": 1,
        "unit_lesson": "...",
        "objective": {...}
      }
    ]
  }
  ```

**Why This Causes Errors:**
- The AI model doesn't know which structure to use
- Attempt 1: Generated `DayPlanMultiSlot` but put fields at wrong level (60 errors)
- Attempt 2: Generated `DayPlanSingleSlot` but incorrectly added `slots` field (15 errors)
- Attempt 3: Same structural confusion persists (12 errors)

**Evidence from Logs:**
```
Attempt 1: days.monday.DayPlanMultiSlot.unit_lesson - Extra inputs are not permitted
          days.monday.DayPlanMultiSlot.slots - Field required

Attempt 2: days.monday.DayPlanSingleSlot.unit_lesson - Field required
          days.monday.DayPlanSingleSlot.slots - Extra inputs are not permitted
          days.monday.DayPlanMultiSlot.slots.0.slot_number - Field required
```

---

### 2. Instructor Library Serialization Error (CRITICAL)

**Problem:**
The instructor library fails with:
```
"Object of type ProficiencyLevel is not JSON serializable"
```

**Root Cause:**
The `ProficiencyLevel` enum is defined as:
```python
class ProficiencyLevel(Enum):
    levels_1_2 = 'levels_1_2'
    levels_3_4 = 'levels_3_4'
    levels_5_6 = 'levels_5_6'
```

When instructor library tries to serialize the Pydantic model to JSON, it encounters the enum and fails. This causes:
1. Instructor path fails immediately
2. Falls back to legacy path (line 1020-1028 in `llm_service.py`)
3. Legacy path doesn't have same schema enforcement
4. AI generates invalid structures

**Impact:**
- Instructor library's automatic validation retries never execute
- System falls back to manual retry logic with less effective error feedback
- Wastes tokens on failed attempts

---

### 3. Prompt-Schema Mismatch

**Problem:**
The prompt explicitly states:
```
"CRITICAL: USE THE SINGLE-SLOT STRUCTURE" 
(do not use a "slots" array inside each day; put unit_lesson, objective, etc. directly inside the day object)
```

But the Pydantic schema **allows both structures** via union type. The AI sees:
- Prompt says: "Use single-slot structure"
- Schema allows: Both single-slot AND multi-slot
- Result: Confusion and incorrect structure generation

**Location:**
- Prompt instruction: `llm_service.py` lines 1299, 1307
- Schema definition: `lesson_schema_models.py` lines 587-588

**Why This Happens:**
The codebase was designed to support both structures (for flexibility), but the prompt was updated to force single-slot without updating the schema to enforce it.

---

### 4. Invalid Enum Values for `pattern_id`

**Problem:**
AI generates enum values that don't exist in the `PatternId` enum:

**Generated (Invalid):**
- `'direction_words_confusion'`
- `'sequencing_words'`
- `'preposition_use'`

**Allowed (From Schema):**
```python
class PatternId(Enum):
    subject_pronoun_omission = 'subject_pronoun_omission'
    adjective_placement = 'adjective_placement'
    past_tense_ed_dropping = 'past_tense_ed_dropping'
    preposition_depend_on = 'preposition_depend_on'
    false_cognate_actual = 'false_cognate_actual'
    false_cognate_library = 'false_cognate_library'
    default = 'default'
```

**Root Cause:**
- Prompt doesn't explicitly list allowed `pattern_id` values
- AI infers pattern names from context instead of using enum values
- No validation feedback tells AI which values are allowed

**Evidence:**
```
days.monday.DayPlanSingleSlot.misconceptions.linguistic_note.pattern_id
  Input should be 'subject_pronoun_omission', 'adjective_placement', ... or 'default'
  [type=enum, input_value='direction_words_confusion', input_type=str]
```

---

### 5. WIDA Mapping Pattern Mismatch

**Problem:**
Generated `wida_mapping` strings don't match the required regex pattern.

**Required Pattern:**
```python
pattern='.*(Explain|Narrate|Inform|Argue).*ELD.*Level'
```

**Generated (Invalid):**
```
'Inform; ELD-MA.2-3.Infor...ey Language Use: Inform'
```

**Why It Fails:**
- Pattern requires: `.*ELD.*Level` (with "Level" at the end)
- Generated format: `ELD-MA.2-3.Infor...ey Language Use: Inform` (no "Level" keyword)
- The regex expects the word "Level" to appear after "ELD"

**Root Cause:**
- Prompt instructions for `wida_mapping` don't emphasize the regex pattern requirement
- AI generates natural language descriptions instead of pattern-compliant strings
- No examples in prompt show the exact pattern format needed

---

### 6. Missing Required Fields in Nested Structures

**Problem:**
When AI generates `DayPlanMultiSlot` structure, it omits required `slot_number` field:

**Required Structure:**
```json
{
  "slots": [
    {
      "slot_number": 1,  // REQUIRED but missing
      "unit_lesson": "...",
      ...
    }
  ]
}
```

**Generated (Invalid):**
```json
{
  "slots": [
    {
      "unit_lesson": "...",  // slot_number missing
      ...
    }
  ]
}
```

**Root Cause:**
- Prompt doesn't explicitly mention `slot_number` requirement for multi-slot structure
- Schema example builder (`_build_schema_example`) only shows single-slot examples
- AI doesn't know `slot_number` is mandatory when using slots array

---

### 7. Inadequate Error Feedback in Retry Prompts

**Problem:**
When validation fails, the retry prompt (`_build_retry_prompt`) doesn't clearly explain:
1. The difference between `DayPlanSingleSlot` and `DayPlanMultiSlot`
2. Which structure should be used
3. What fields are required for each structure

**Current Retry Prompt Issues:**
- Generic error messages like "Extra inputs are not permitted"
- Doesn't explain structural choice (single vs multi-slot)
- Doesn't list allowed enum values
- Doesn't show pattern examples for `wida_mapping`

**Location:**
- `llm_service.py` method `_build_retry_prompt` (not shown in current codebase, likely missing or insufficient)

---

## Error Progression Analysis

### Attempt 1 (60 validation errors)
**Errors:**
- Structure confusion: `DayPlanMultiSlot` with fields at wrong level
- Invalid enum: `pattern_id` values not in enum
- Pattern mismatch: `wida_mapping` doesn't match regex
- Missing fields: `slots` array missing in `DayPlanMultiSlot`

**Why:**
- AI chose `DayPlanMultiSlot` structure but didn't understand nesting requirements
- Generated creative enum values instead of using allowed ones
- Generated natural language for `wida_mapping` instead of pattern-compliant format

### Attempt 2 (15 validation errors)
**Errors:**
- Structure confusion: `DayPlanSingleSlot` with incorrect `slots` field
- Missing `unit_lesson` at root level of `DayPlanSingleSlot`
- Missing `slot_number` in `slots` array items

**Why:**
- AI tried to fix by switching to `DayPlanSingleSlot` but kept `slots` field from previous attempt
- Didn't understand that `DayPlanSingleSlot` requires `unit_lesson` at root, not in slots
- Still generating `DayPlanMultiSlot` structure inside `DayPlanSingleSlot` wrapper

### Attempt 3 (12 validation errors)
**Errors:**
- Same structural issues persist
- Still missing `slot_number` in slots
- Still mixing single-slot and multi-slot structures

**Why:**
- Retry feedback doesn't clearly explain the structural difference
- AI continues to generate hybrid structures that don't match either schema variant

---

## Contributing Factors

### 1. Dual-Path Architecture Complexity
- Instructor path (with automatic validation) fails due to serialization
- Falls back to legacy path (manual validation) with less effective error handling
- Two different retry mechanisms create confusion

### 2. Schema Evolution Without Prompt Updates
- Schema was updated to support both structures for flexibility
- Prompt was updated to force single-slot structure
- No enforcement mechanism to ensure prompt-schema alignment

### 3. Missing Schema Examples
- `_build_schema_example` only shows single-slot structure
- No examples of multi-slot structure (even though schema allows it)
- AI has no reference for correct multi-slot format

### 4. Enum Documentation Gap
- `PatternId` enum values not listed in prompt
- AI must infer from context or generate creative values
- No validation feedback lists allowed values

### 5. Pattern Documentation Gap
- `wida_mapping` regex pattern not explained in prompt
- No examples showing pattern-compliant format
- AI generates natural language instead of pattern-compliant strings

---

## Impact Assessment

### Performance Impact
- **Token Waste**: Each retry consumes full token budget (16K+ tokens per attempt)
- **Time Delay**: 3 retry attempts = ~3x processing time
- **API Costs**: 3x API calls for same transformation

### Reliability Impact
- **Failure Rate**: High failure rate after 3 attempts
- **User Experience**: Long wait times, unclear error messages
- **Data Quality**: Some transformations may succeed with incorrect structures

### Maintenance Impact
- **Debugging Difficulty**: Multiple error types make root cause identification hard
- **Code Complexity**: Dual-path architecture increases maintenance burden
- **Schema Drift Risk**: Prompt and schema can drift out of sync

---

## Recommendations (For Future Implementation)

### Immediate Fixes (High Priority)
1. **Fix Instructor Library Serialization**
   - Ensure enums are properly serialized to JSON strings
   - Test instructor path with all enum types
   - Add enum serialization handling

2. **Clarify Schema Structure in Prompt**
   - Explicitly state: "ALWAYS use DayPlanSingleSlot structure"
   - OR: Update schema to only allow single-slot structure
   - Remove union type if single-slot is always required

3. **Add Enum Value Documentation**
   - List all allowed `PatternId` values in prompt
   - Provide examples of correct enum usage
   - Add validation feedback that lists allowed values

4. **Fix WIDA Pattern Documentation**
   - Show exact pattern format in prompt: `"Explain; ELD-SS.6-8.Explain.Writing; Levels 2-4"`
   - Explain regex requirements clearly
   - Provide multiple examples

### Medium-Term Improvements
5. **Improve Retry Error Feedback**
   - Explain structural differences in retry prompts
   - Show correct vs incorrect examples
   - List allowed enum values when enum errors occur

6. **Add Schema Examples for Both Structures**
   - If both structures are needed, show examples of both
   - Clearly explain when to use each structure
   - Add validation to ensure correct structure is used

7. **Unify Retry Mechanisms**
   - Fix instructor path to avoid fallback
   - OR: Remove instructor path if it's unreliable
   - Consolidate to single, reliable retry mechanism

### Long-Term Improvements
8. **Schema-Prompt Synchronization**
   - Automated checks to ensure prompt matches schema
   - Schema-driven prompt generation
   - Version control for prompt-schema pairs

9. **Enhanced Validation Feedback**
   - Structured error messages with fix suggestions
   - Examples of correct structures
   - Interactive validation with step-by-step guidance

10. **Monitoring and Alerting**
    - Track retry rates and error types
    - Alert on high retry rates
    - Dashboard for validation error patterns

---

## Conclusion

The root causes are **interconnected** and create a cascading failure pattern:

1. Instructor library fails → Falls back to legacy path
2. Legacy path has schema ambiguity → AI generates wrong structure
3. Wrong structure fails validation → Retry with unclear feedback
4. Unclear feedback → AI makes same mistakes → More retries
5. Multiple retries → High token costs and delays

**Primary Root Cause:** Schema ambiguity combined with instructor library serialization failure creates a perfect storm where the AI cannot reliably generate valid structures, and the retry mechanism cannot effectively guide corrections.

**Critical Path to Fix:**
1. Fix instructor library enum serialization (enables automatic validation)
2. Remove schema ambiguity (enforce single structure or clarify when to use each)
3. Improve error feedback (help AI understand and fix mistakes)

Without addressing these root causes, the retry mechanism will continue to fail, wasting tokens and delaying transformations.

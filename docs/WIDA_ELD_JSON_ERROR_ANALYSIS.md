# WIDA/ELD Objective JSON Format Error Analysis

## Error Explanation

### The Problem

The system frequently encounters JSON parsing errors when processing the `wida_mapping` field within the `assessment.bilingual_overlay` section of lesson plans. The error manifests as:

**Error Message:**
```
Expecting ',' delimiter: line X column Y (char Z)
```

**Root Cause:**
The LLM (gpt-5-mini) generates unescaped quotes inside the `wida_mapping` string value, creating invalid JSON syntax.

### Specific Error Pattern

**Incorrect (causes error):**
```json
"wida_mapping": "Target WIDA "levels": 1-6 with differentiated supports"
```

**Correct (expected):**
```json
"wida_mapping": "Target WIDA \"levels\": 1-6 with differentiated supports"
```

### Why This Happens

1. **Natural Language Pattern**: The phrase "Target WIDA levels" is natural English, and the LLM generates it with quotes around "levels" as if it were natural language, not JSON.

2. **Field Context**: The `wida_mapping` field often contains phrases like:
   - `"Target "levels": 1-6"`
   - `"Key Language Use: Explain. ELD domains: "levels": 2-4"`
   - `"WIDA "levels": 1-5"`

3. **JSON String Escaping**: In JSON, all quotes inside string values must be escaped with backslashes (`\"`), but the LLM generates them as literal quotes.

4. **Location**: The error consistently occurs in the `assessment.bilingual_overlay.wida_mapping` field, specifically on Monday's assessment section.

### Impact

- **Frequency**: High - affects multiple slots, particularly in the assessment section
- **Retry Behavior**: Causes multiple retry attempts (up to 4 attempts observed)
- **Failure Pattern**: Not slot-specific, but field-specific - all slots fail in the same field
- **JSON Repair**: The repair function attempts to fix this but sometimes fails to detect the pattern correctly

### Error Flow

1. LLM generates JSON with unescaped quotes in `wida_mapping`
2. JSON parser encounters unescaped quote → raises `JSONDecodeError`
3. Error analysis identifies the problematic field (`assessment`, `monday`)
4. JSON repair function attempts to escape the quote
5. If repair fails → retry with same prompt (up to 4 attempts)
6. If all retries fail → slot processing fails

---

## Related Documents and Code

### Core Schema Files

1. **`schemas/lesson_output_schema.json`**
   - **Lines 504-509**: Defines `wida_mapping` field structure
   - **Field Type**: `string`
   - **Pattern**: `".*(Explain|Narrate|Inform|Argue).*ELD.*Level"`
   - **Examples**: `["Explain + ELD-SS.6-8.Writing + Levels 2-5"]`
   - **Location**: `assessment.bilingual_overlay.wida_mapping`

2. **`tests/fixtures/valid_lesson_minimal.json`**
   - **Lines 488**: Example of correct `wida_mapping` format
   - **Value**: `"Inform + ELD-SS.6-8.Speaking/Writing + Levels 2-5"`
   - Shows proper format without problematic quotes

### Prompt and LLM Service Files

3. **`backend/llm_service.py`**
   - **Lines 1248-1250**: Explicit instruction for escaping quotes in `wida_mapping`
     ```python
     - Example: "wida_mapping": "Target \\"levels\\": 1-4" (NOT "Target "levels": 1-4")
     ```
   - **Lines 1333**: Duplicate instruction (appears twice in prompt)
   - **Lines 1706-1708**: Schema example showing `wida_mapping` structure
   - **Lines 1735-1737**: Another schema example
   - **Function**: `_build_prompt()` - Contains prompt instructions

4. **`docs/prompt_v4.md`**
   - **Lines 632**: Example showing `wida_mapping` in assessment structure
   - **Lines 628-640**: Complete assessment section example
   - Documents the expected JSON structure

### JSON Repair and Error Handling

5. **`tools/json_repair.py`**
   - **Lines 227-275**: `fix_unescaped_quotes_in_strings()` function
   - **Purpose**: Detects and escapes unescaped quotes inside string values
   - **Pattern Detection**: 
     - Lines 244-258: Multiple regex patterns to detect problematic quotes
     - Lines 243-258: Specific patterns for "Target", "WIDA", "levels" combinations
   - **Recent Improvements**: Enhanced pattern detection for `"Target "levels":` pattern
   - **Function**: `repair_json()` - Main repair entry point

6. **`backend/llm_service.py`** (Error Handling)
   - **Lines 2121-2200**: `_parse_response()` method
   - **Lines 2146-2168**: JSON parsing error handling
   - **Lines 2170-2172**: Calls `repair_json()` on parse failure
   - **Lines 2150**: `_analyze_json_error()` - Analyzes error context
   - **Lines 2073-2118**: Error analysis function

### Documentation Files

7. **`docs/training/TRAINING_SCHEMA_SIMPLIFIED.md`**
   - **Lines 202-220**: Assessment section structure
   - **Lines 210**: Example `wida_mapping` format
   - Training documentation for schema structure

8. **`docs/json_output_implementation_plan.md`**
   - **Lines 190-195**: `bilingual_overlay` structure documentation
   - **Lines 192**: Mentions `wida_mapping` field
   - Implementation planning document

9. **`docs/examples/Sample_Lesson_Transformation_WIDA.md`**
   - Example transformations showing WIDA structure
   - May contain `wida_mapping` examples

10. **`docs/archive/deprecated/documentation/Prompt_Lesson_Plan_V3_WIDA_Enhanced.md`**
    - Historical prompt version
    - May contain legacy WIDA format examples

### Test Files

11. **`tests/fixtures/valid_lesson_minimal.json`**
    - **Lines 484-496**: Complete assessment section with correct `wida_mapping`
    - Reference for valid format

12. **`tests/fixtures/invalid_string_too_short.json`**
    - May contain examples of invalid formats

13. **`tests/fixtures/invalid_wrong_enum.json`**
    - May contain validation error examples

### Template Files

14. **`templates/partials/bilingual_overlay.jinja2`**
    - Jinja2 template for rendering bilingual overlay
    - May reference `wida_mapping` field

### Log Files (Runtime)

15. **`logs/backend_*.log`**
    - Contains actual error instances
    - Search pattern: `"wida_mapping"`, `"Target "levels"`, `"ERROR HERE"`
    - Shows retry attempts and repair failures

### Related Code Sections

16. **`backend/llm_service.py`** - Structured Outputs
    - **Lines 488-500**: `_structured_response_format()` method
    - **Lines 421-463**: `_transform_oneof_for_openai()` - Schema transformation
    - **Recent Change**: `strict: False` for gpt-5-mini to improve compatibility

17. **`tools/markdown_to_docx.py`**
    - **Function**: `sanitize_xml_text()` - Removes invalid XML characters
    - Related to text sanitization (though not directly related to JSON parsing)

18. **`tools/docx_renderer.py`**
    - Renders validated JSON to DOCX
    - Uses `sanitize_xml_text()` for text insertion
    - Processes `wida_mapping` field during rendering

---

## Error Pattern Examples from Logs

### Common Patterns That Fail

1. **Pattern 1**: `"Target WIDA "levels": 1-6"`
   - Error: Unescaped quote before "levels"
   - Should be: `"Target WIDA \"levels\": 1-6"`

2. **Pattern 2**: `"Key Language Use: Explain. ELD domains: "levels": 2-4"`
   - Error: Unescaped quote before "levels"
   - Should be: `"Key Language Use: Explain. ELD domains: \"levels\": 2-4"`

3. **Pattern 3**: `"Target "levels": 1-4 with differentiated supports"`
   - Error: Unescaped quote before "levels"
   - Should be: `"Target \"levels\": 1-4 with differentiated supports"`

### Log Evidence

From `logs/backend_*.log`:
```
"wida_mapping": "Target " <-- ERROR HERE --> levels": 1-6 with differentiated
```

---

## Solutions Implemented

### 1. Prompt Instructions (Current)
- Explicit examples in `backend/llm_service.py` lines 1249, 1333
- Shows correct escaping: `"Target \\"levels\\": 1-4"`

### 2. JSON Repair Function (Current)
- Enhanced pattern detection in `tools/json_repair.py`
- Multiple regex patterns to catch various quote patterns
- Error position-aware repair

### 3. Structured Outputs (Recent)
- Using `strict: False` for gpt-5-mini
- Schema-based generation to guide LLM output

### 4. Retry Logic (Current)
- Up to 4 retry attempts per slot
- Only failed slots retry (not entire batch)

### 5. Pre-Validation Enhancement (Implemented 2025-12-28)
- **Location**: `backend/llm_service.py` lines 2006-2031
- **Implementation**: Targeted regex check for `wida_mapping` field
- **Pattern**: `r'("wida_mapping"\s*:\s*")(.+?)(")(?=\s*[,}])'` with positive lookahead
- **Functionality**: Escapes unescaped quotes in `wida_mapping` field BEFORE JSON parsing
- **Impact**: Catches errors early, prevents JSON parsing failures

### 6. JSON-Repair Library Integration (Implemented 2025-12-28)
- **Location**: `tools/json_repair.py` lines 10-14, 107-120
- **Library**: `json-repair` Python package
- **Functionality**: Robust fallback for complex JSON syntax errors
- **Usage**: Attempts library repair before custom fixes
- **Benefits**: Handles nested quotes, trailing commas, and other complex errors

### 7. Instructor Library Integration (Implemented 2025-12-28)
- **Location**: `backend/llm_service.py` lines 15, 82-88, 845-920, 1009-1036
- **Library**: `instructor` for schema-first approach
- **Models**: `backend/lesson_schema_models.py` (Pydantic models generated from JSON schema)
- **Functionality**: Guarantees schema compliance using OpenAI structured outputs with Pydantic validation
- **Features**:
  - `create_with_completion` for accurate token tracking
  - Support for both OpenAI and Anthropic models
  - Partial week optimization (optional days in Pydantic model)
- **Impact**: Ultimate solution - prevents JSON errors at generation time

---

## Recommendations

### Short-term
1. ✅ Enhanced JSON repair patterns (already implemented)
2. ✅ Improved prompt instructions (already implemented)
3. ✅ Structured outputs with `strict: False` (already implemented)
4. ✅ Pre-validation for `wida_mapping` field (implemented 2025-12-28)
5. ✅ JSON-repair library integration (implemented 2025-12-28)

### Medium-term
1. ✅ **Pre-validation**: Add specific pre-validation check for `wida_mapping` quotes (IMPLEMENTED)
2. ✅ **Robust Repair**: Integrate json-repair library for complex errors (IMPLEMENTED)
3. **Prompt Enhancement**: Add more explicit examples in the prompt for this specific field (OPTIONAL)

### Long-term
1. ✅ **Schema-First Approach**: Instructor library with Pydantic models (IMPLEMENTED 2025-12-28)
   - Guarantees schema compliance at generation time
   - Eliminates JSON parsing errors at the source
   - Uses OpenAI structured outputs with Pydantic validation
2. **LLM Fine-tuning**: If possible, fine-tune on examples with correct escaping (FUTURE)
3. **Alternative Format**: Consider using a structured format instead of free-form string (FUTURE)

---

## Related Issues

- JSON parsing errors in general (not just `wida_mapping`)
- XML compatibility issues (NULL bytes, control characters)
- Structured outputs compatibility with gpt-5-mini
- Retry logic and error recovery

---

**Last Updated**: 2025-12-28  
**Status**: ✅ **RESOLVED** - Multi-layer defense strategy implemented:
1. Pre-validation regex for `wida_mapping` field
2. JSON-repair library fallback
3. Instructor library with Pydantic models (ultimate solution)

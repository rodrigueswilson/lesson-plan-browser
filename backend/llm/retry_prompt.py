"""
Builds the retry prompt with validation error feedback for LLM.
Used by prompt_builder.build_retry_prompt.
"""

from typing import Any, Dict, List, Optional

from backend.llm.validation import parse_validation_errors


def build_retry_prompt(
    original_prompt: str,
    validation_error: Optional[str],
    retry_count: int,
    available_days: Optional[List[str]] = None,
    error_analysis: Optional[Dict[str, Any]] = None,
) -> str:
    """Build a retry prompt with feedback about validation errors."""
    days_to_generate = (
        [d.lower() for d in available_days]
        if available_days
        else ["monday", "tuesday", "wednesday", "thursday", "friday"]
    )

    if len(days_to_generate) < 5:
        days_str = ", ".join(days_to_generate)
        vocab_rule_1 = f"1. **vocabulary_cognates is MANDATORY**: For the requested days ({days_str}), each day must have exactly 6 English-Portuguese word pairs. **CRITICAL: Do not skip this field for any of the requested days.**"
        sentence_rule_2 = "2. **sentence_frames is MANDATORY**: For the requested days, each day must have exactly 8 sentence frames. This field cannot be omitted or empty."
        combined_rule_3 = f"3. **Both fields are required for ALL requested days** ({days_str}). Ensure vocabulary_cognates is included for every single requested day."
        structure_rule_4 = f"4. **Check your JSON structure**: Ensure keys exist ONLY for: {days_str}. Do not generate other days."
        regenerate_instruction = f"Please regenerate the lesson plan JSON for {days_str} with all required fields included."
    else:
        vocab_rule_1 = "1. **vocabulary_cognates is MANDATORY**: Every day (Monday, Tuesday, Wednesday, Thursday, Friday) must have exactly 6 English-Portuguese word pairs in the `vocabulary_cognates` array. This field cannot be omitted, empty, or have zero items. **CRITICAL: Do not skip this field for any day - it is required for ALL lesson days without exception.**"
        sentence_rule_2 = "2. **sentence_frames is MANDATORY**: Every day must have exactly 8 sentence frames/stems/questions in the `sentence_frames` array (3 for levels_1_2, 3 for levels_3_4, 2 for levels_5_6). This field cannot be omitted or empty."
        combined_rule_3 = "3. **Both fields are required for ALL lesson days** (Monday, Tuesday, Wednesday, Thursday, Friday), even if the lesson content is minimal. Extract vocabulary from lesson objectives or identify essential academic vocabulary that supports the lesson's core concepts. **Ensure vocabulary_cognates is included for every single day.**"
        structure_rule_4 = "4. **Check your JSON structure**: Ensure all required fields are present and properly formatted according to the schema."
        regenerate_instruction = "Please regenerate the complete lesson plan JSON with all required fields included. Do not omit vocabulary_cognates or sentence_frames for any day."

    error_context_section = ""
    if error_analysis:
        error_type = error_analysis.get("error_type", "unknown")
        error_pos = error_analysis.get("error_position")
        error_line = error_analysis.get("error_line")
        error_col = error_analysis.get("error_column")
        problematic_snippet = error_analysis.get("problematic_snippet", "")
        day_being_generated = error_analysis.get("day_being_generated")
        field_being_generated = error_analysis.get("field_being_generated")

        error_context_section = "\n## JSON SYNTAX ERROR DETECTED\n\n"
        error_context_section += "Your previous response had a JSON syntax error:\n"
        error_context_section += f"- Error Type: {error_type}\n"
        if error_line and error_col:
            error_context_section += f"- Location: Line {error_line}, Column {error_col}"
        if error_pos:
            error_context_section += f" (Character {error_pos})"
        error_context_section += "\n"
        if day_being_generated:
            error_context_section += f"- Day being generated: {day_being_generated}\n"
        if field_being_generated:
            error_context_section += f"- Field being generated: {field_being_generated}\n"
        if problematic_snippet:
            error_context_section += f"\nProblematic JSON snippet:\n```\n{problematic_snippet}\n```\n\n"
        if error_type == "unquoted_property_name":
            error_context_section += "What's wrong: You used an unquoted property name.\n\n"
            error_context_section += "How to fix: ALL property names must be in double quotes.\n\n"
            error_context_section += "Example:\n"
            error_context_section += '- WRONG: {key: "value"}\n'
            error_context_section += '- CORRECT: {"key": "value"}\n\n'
        elif error_type == "incomplete_string":
            error_context_section += "What's wrong: A string value is not properly closed with a closing quote.\n\n"
            error_context_section += "How to fix: Ensure all string values are closed with double quotes.\n\n"
        elif error_type == "trailing_comma":
            error_context_section += "What's wrong: There is a trailing comma after the last item in an object or array.\n\n"
            error_context_section += "How to fix: Remove trailing commas. JSON does not allow them.\n\n"
        error_context_section += "## CRITICAL: JSON SYNTAX RULES (MUST FOLLOW)\n\n"
        error_context_section += "1. **ALL property names MUST be in double quotes**\n"
        error_context_section += '   - CORRECT: {"key": "value"}\n'
        error_context_section += '   - INCORRECT: {key: "value"}\n\n'
        error_context_section += "2. **ALL string values MUST be in double quotes**\n"
        error_context_section += "3. **NO unquoted property names**\n"
        error_context_section += "   - The error 'Expecting property name' means you used an unquoted property name.\n"
        error_context_section += "   - ALL property names must be in double quotes.\n\n"

    parsed_errors = None
    if error_analysis and "validation_errors" in error_analysis:
        parsed_errors = error_analysis["validation_errors"]
    elif validation_error:
        parsed_errors = parse_validation_errors(validation_error)

    structured_feedback = ""
    if parsed_errors and parsed_errors.get("structure_confusion_detected"):
        structured_feedback += """

## CRITICAL: STRUCTURE CONFUSION DETECTED

You are mixing DayPlanSingleSlot and DayPlanMultiSlot structures.

**IMPORTANT:** The schema only allows single-slot structures for AI generation. Multi-slot structures are created by merging multiple lessons, NOT by AI.

**CORRECT STRUCTURE (DayPlanSingleSlot - ALWAYS USE THIS):**
```json
{
  "unit_lesson": "...",
  "objective": {...},
  "vocabulary_cognates": [...],
  "sentence_frames": [...],
  ...
}
```

**INCORRECT (DO NOT USE):**
```json
{
  "slots": [...]  // DO NOT include this field - AI should never generate multi-slot
}
```

**Rule:** Always put fields directly in the day object. Never use a "slots" array. The schema only supports the single-slot structure for AI generation.

"""

    if parsed_errors and parsed_errors.get("enum_errors"):
        structured_feedback += "\n## ENUM VALUE ERRORS\n\n"
        for enum_error in parsed_errors["enum_errors"]:
            field_path = enum_error.get("field_path", "unknown")
            allowed_values = enum_error.get("allowed_values", [])
            invalid_value = enum_error.get("invalid_value", "unknown")
            structured_feedback += f"**Field:** `{field_path}`\n"
            structured_feedback += f"**You used:** `{invalid_value}`\n"
            if allowed_values:
                allowed_values_str = ", ".join([f"'{v}'" for v in allowed_values])
                structured_feedback += f"**Allowed values:** {allowed_values_str}\n"
            structured_feedback += "**Fix:** Use one of the allowed values exactly as listed above.\n\n"

    if parsed_errors and parsed_errors.get("pattern_errors"):
        structured_feedback += "\n## PATTERN MISMATCH ERRORS\n\n"
        for pattern_error in parsed_errors["pattern_errors"]:
            field_path = pattern_error.get("field_path", "unknown")
            pattern_req = pattern_error.get("pattern_requirement", "unknown")
            invalid_value = pattern_error.get("invalid_value", "unknown")
            structured_feedback += f"**Field:** `{field_path}`\n"
            structured_feedback += f"**Required pattern:** `{pattern_req}`\n"
            if invalid_value != "unknown":
                structured_feedback += f"**Your value:** `{invalid_value}`\n"
            structured_feedback += "**Fix:** Ensure your value matches the pattern. See examples in original prompt.\n\n"

    if parsed_errors and parsed_errors.get("missing_field_errors"):
        structured_feedback += "\n## MISSING REQUIRED FIELDS\n\n"
        for missing_error in parsed_errors["missing_field_errors"]:
            field_path = missing_error.get("field_path", "unknown")
            structured_feedback += f"- `{field_path}` is required but missing. Please add this field.\n"
        structured_feedback += "\n"

    if parsed_errors and parsed_errors.get("extra_field_errors"):
        structured_feedback += "\n## EXTRA FIELDS (NOT ALLOWED)\n\n"
        for extra_error in parsed_errors["extra_field_errors"]:
            field_path = extra_error.get("field_path", "unknown")
            extra_field = extra_error.get("extra_field", "unknown")
            structured_feedback += f"- `{field_path}` contains field `{extra_field}` which is not allowed. Remove it.\n"
        structured_feedback += "\n"

    feedback_section = f"""
## CRITICAL: VALIDATION ERROR - RETRY ATTEMPT {retry_count}

Your previous response failed validation. Please fix the following issues:

{validation_error or ''}

{structured_feedback}

{error_context_section}

### SPECIFIC REQUIREMENTS TO FIX:

{vocab_rule_1}

{sentence_rule_2}

{combined_rule_3}

{structure_rule_4}

{regenerate_instruction}

---
"""
    return feedback_section + "\n\n" + original_prompt

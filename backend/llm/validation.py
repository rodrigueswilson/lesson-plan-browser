"""
Retry and validation logic for LLM responses.
Parse validation errors, pre-validate JSON, analyze JSON errors, validate structure.
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from backend.telemetry import logger
from tools.json_repair import repair_json


def parse_validation_errors(validation_error: str) -> Dict[str, Any]:
    """
    Parse Pydantic validation error messages to extract actionable feedback.

    Args:
        validation_error: Validation error message string (may contain multiple errors)

    Returns:
        Dict with:
        - error_type: 'enum', 'pattern', 'missing_field', 'extra_field', 'structure_confusion', 'unknown'
        - errors: List of parsed error dicts
        - structure_confusion_detected, enum_errors, pattern_errors, etc.
    """
    parsed_errors = []
    structure_confusion_detected = False
    enum_errors = []
    pattern_errors = []
    missing_field_errors = []
    extra_field_errors = []

    error_lines = validation_error.split("\n")

    for idx, line in enumerate(error_lines):
        line = line.strip()
        if not line:
            continue

        if "DayPlanSingleSlot" in line and "slots" in line.lower():
            structure_confusion_detected = True
        if "DayPlanMultiSlot" in line and (
            "unit_lesson" in line.lower() or "objective" in line.lower()
        ):
            structure_confusion_detected = True
        if "Extra inputs are not permitted" in line and (
            "slots" in line.lower() or "DayPlan" in line
        ):
            structure_confusion_detected = True

        field_match = re.search(
            r"\b(days\.[a-zA-Z_]+\.[a-zA-Z_]+(?:\.[a-zA-Z_]+)*)\b", line
        )
        if not field_match:
            field_match = re.search(r"\b([a-z_]+(?:\.[a-zA-Z_]+){2,})\b", line)

        next_line = ""
        next_next_line = ""
        if idx + 1 < len(error_lines):
            next_line = error_lines[idx + 1].strip()
        if idx + 2 < len(error_lines):
            next_next_line = error_lines[idx + 2].strip()

        if field_match:
            field_path = field_match.group(1)
            combined_line = line
            if next_line:
                combined_line += " " + next_line
            if next_next_line:
                combined_line += " " + next_next_line
            error_info = {
                "field_path": field_path,
                "error_type": "unknown",
                "guidance": combined_line,
            }

            enum_match = re.search(
                r"Input should be '([^']+)'(?:, '([^']+)')*.*or '([^']+)'",
                combined_line,
            )
            if (
                enum_match
                or "is not one of" in combined_line
                or "type=enum" in combined_line
            ):
                error_info["error_type"] = "enum"
                allowed_values = re.findall(r"'([^']+)'", combined_line)
                if allowed_values:
                    error_info["allowed_values"] = allowed_values
                    error_info["guidance"] = (
                        f"Field '{field_path}' must be one of: {', '.join(allowed_values)}"
                    )
                value_match = re.search(r"input_value='([^']+)'", combined_line)
                if value_match:
                    error_info["invalid_value"] = value_match.group(1)
                enum_errors.append(error_info)

            elif (
                "string should match pattern" in combined_line.lower()
                or "string_pattern_mismatch" in combined_line
                or (
                    re.search(r"pattern\s+'([^']+)'", combined_line, re.IGNORECASE)
                    and "should match" in combined_line.lower()
                )
            ):
                error_info["error_type"] = "pattern"
                pattern_match = re.search(r"pattern '([^']+)'", combined_line)
                if pattern_match:
                    error_info["pattern_requirement"] = pattern_match.group(1)
                value_match = re.search(r"input_value='([^']+)'", combined_line)
                if value_match:
                    error_info["invalid_value"] = value_match.group(1)
                error_info["guidance"] = (
                    f"Field '{field_path}' must match the required pattern. See examples in prompt."
                )
                pattern_errors.append(error_info)

            elif (
                "Field required" in combined_line or "type=missing" in combined_line
            ):
                error_info["error_type"] = "missing_field"
                error_info["guidance"] = (
                    f"Field '{field_path}' is required but missing. Please add this field."
                )
                missing_field_errors.append(error_info)

            elif (
                "Extra inputs are not permitted" in combined_line
                or "extra_forbidden" in combined_line
            ):
                error_info["error_type"] = "extra_field"
                extra_match = re.search(r"\.([a-z_]+)\s", combined_line)
                if extra_match:
                    error_info["extra_field"] = extra_match.group(1)
                error_info["guidance"] = (
                    f"Field '{field_path}' contains an extra field that is not allowed. Remove it."
                )
                extra_field_errors.append(error_info)

            parsed_errors.append(error_info)

    return {
        "errors": parsed_errors,
        "structure_confusion_detected": structure_confusion_detected,
        "enum_errors": enum_errors,
        "pattern_errors": pattern_errors,
        "missing_field_errors": missing_field_errors,
        "extra_field_errors": extra_field_errors,
        "has_errors": len(parsed_errors) > 0,
    }


def pre_validate_json(
    json_string: str,
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Pre-validate JSON string for common issues before parsing.

    Returns:
        (is_valid, error_message, fix_attempts)
    """
    issues = []
    fix_attempts = []
    fixed_string = json_string

    unquoted_pattern = re.search(r'(?<!["\w])(\w+):\s*["\d\[\{]', json_string)
    if unquoted_pattern:
        issues.append(
            f"Unquoted property name detected at position {unquoted_pattern.start()}"
        )
        key_name = unquoted_pattern.group(1)
        fixed_string = re.sub(
            r'(?<!["\w])' + re.escape(key_name) + r":",
            f'"{key_name}":',
            fixed_string,
            count=1,
        )
        fix_attempts.append(f"Quoted property name '{key_name}'")

    quote_count = json_string.count('"')
    if quote_count % 2 != 0:
        issues.append("Unmatched quotes detected")
        last_quote_idx = json_string.rfind('"')
        if last_quote_idx >= 0:
            remaining = json_string[last_quote_idx + 1 :]
            if '"' not in remaining or remaining.count('"') % 2 == 0:
                fixed_string = (
                    json_string[: last_quote_idx + 1]
                    + '"'
                    + json_string[last_quote_idx + 1 :]
                )
                fix_attempts.append("Closed unmatched quote")

    trailing_comma = re.search(r",(\s*[}\]])", json_string)
    if trailing_comma:
        issues.append(f"Trailing comma at position {trailing_comma.start()}")
        fixed_string = re.sub(r",(\s*[}\]])", r"\1", fixed_string)
        fix_attempts.append("Removed trailing comma")

    trimmed = json_string.rstrip()
    if trimmed and not trimmed.endswith(("}", "]", '"', ",", ":", "[", "{")):
        last_colon_quote = trimmed.rfind(': "')
        if last_colon_quote > 0:
            remaining_after_colon = trimmed[last_colon_quote + 3 :]
            if '"' not in remaining_after_colon:
                issues.append("Incomplete string value detected near end")
                fixed_string = trimmed + '"'
                fix_attempts.append("Closed incomplete string value")

    wida_mapping_matches = list(
        re.finditer(
            r'("wida_mapping"\s*:\s*")(.+?)(")(?=\s*[,}])',
            fixed_string,
            re.IGNORECASE | re.DOTALL,
        )
    )

    if wida_mapping_matches:
        for match in reversed(wida_mapping_matches):
            prefix, content, suffix = match.groups()
            if '"' in content and '\\"' not in content:
                issues.append(
                    f"Unescaped quotes detected in wida_mapping field at position {match.start()}"
                )
                escaped_content = re.sub(r'(?<!\\)"', r'\\"', content)
                fixed_match = prefix + escaped_content + suffix
                fixed_string = (
                    fixed_string[: match.start()]
                    + fixed_match
                    + fixed_string[match.end() :]
                )
                fix_attempts.append("Escaped quotes in wida_mapping field")

    if issues:
        return (
            False,
            "; ".join(issues),
            {"fix_attempts": fix_attempts, "fixed_string": fixed_string},
        )
    return True, None, None


def identify_day_at_position(json_string: str, position: int) -> Optional[str]:
    """Find which day is being generated at the given position."""
    text_before = json_string[:position]
    day_patterns = [
        ('"monday":', "monday"),
        ('"tuesday":', "tuesday"),
        ('"wednesday":', "wednesday"),
        ('"thursday":', "thursday"),
        ('"friday":', "friday"),
    ]
    last_day = None
    last_pos = -1
    for pattern, day_name in day_patterns:
        pos = text_before.rfind(pattern)
        if pos > last_pos:
            last_pos = pos
            last_day = day_name
    return last_day


def identify_field_at_position(json_string: str, position: int) -> Optional[str]:
    """Find which field is being generated at the given position."""
    field_patterns = [
        ('"unit_lesson":', "unit_lesson"),
        ('"objective":', "objective"),
        ('"anticipatory_set":', "anticipatory_set"),
        ('"tailored_instruction":', "tailored_instruction"),
        ('"misconceptions":', "misconceptions"),
        ('"assessment":', "assessment"),
        ('"homework":', "homework"),
        ('"content_objective":', "content_objective"),
        ('"student_goal":', "student_goal"),
        ('"wida_objective":', "wida_objective"),
        ('"bilingual_bridge":', "bilingual_bridge"),
        ('"co_teaching_model":', "co_teaching_model"),
        ('"ell_support":', "ell_support"),
        ('"vocabulary_cognates":', "vocabulary_cognates"),
        ('"sentence_frames":', "sentence_frames"),
    ]
    text_before = json_string[:position]
    last_field = None
    last_pos = -1
    for pattern, field_name in field_patterns:
        pos = text_before.rfind(pattern)
        if pos > last_pos:
            last_pos = pos
            last_field = field_name
    return last_field


def detect_error_type(
    error: json.JSONDecodeError, json_string: str, error_pos: int
) -> str:
    """Classify the type of JSON error."""
    error_msg = str(error).lower()
    if (
        "expecting property name" in error_msg
        or "property name enclosed" in error_msg
    ):
        return "unquoted_property_name"
    elif "expecting" in error_msg and "delimiter" in error_msg:
        return "syntax_error"
    elif "unterminated string" in error_msg or "unterminated" in error_msg:
        return "incomplete_string"
    elif "trailing comma" in error_msg or "trailing" in error_msg:
        return "trailing_comma"
    elif "expecting value" in error_msg:
        return "missing_value"
    return "unknown_error"


def analyze_characters_around_error(
    json_string: str, error_pos: int
) -> Dict[str, Any]:
    """Analyze character balance around error position."""
    context_start = max(0, error_pos - 200)
    context_end = min(len(json_string), error_pos + 200)
    context = json_string[context_start:context_end]

    quote_count = context.count('"')
    bracket_count = context.count("[") - context.count("]")
    brace_count = context.count("{") - context.count("}")

    text_before = json_string[:error_pos]
    quotes_before = text_before.count('"')
    in_string = quotes_before % 2 != 0

    return {
        "quote_balance": quote_count % 2,
        "bracket_balance": bracket_count,
        "brace_balance": brace_count,
        "in_string": in_string,
    }


def find_complete_days_before_error(
    json_string: str, error_pos: int
) -> List[str]:
    """Find which days were successfully parsed before the error."""
    text_before = json_string[:error_pos]
    complete_days = []

    day_patterns = [
        ('"monday":', "monday"),
        ('"tuesday":', "tuesday"),
        ('"wednesday":', "wednesday"),
        ('"thursday":', "thursday"),
        ('"friday":', "friday"),
    ]

    for pattern, day_name in day_patterns:
        day_start = text_before.find(pattern)
        if day_start >= 0:
            after_day = text_before[day_start:]
            brace_count = 0
            in_string = False
            escape_next = False
            found_closing = False

            for i, char in enumerate(after_day):
                if escape_next:
                    escape_next = False
                    continue
                if char == "\\":
                    escape_next = True
                    continue
                if char == '"':
                    in_string = not in_string
                    continue
                if not in_string:
                    if char == "{":
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1
                        if brace_count == 0 and i > len(pattern):
                            found_closing = True
                            break

            if found_closing:
                complete_days.append(day_name)

    return complete_days


def extract_problematic_snippet(
    json_string: str, error_pos: int, context_size: int = 200
) -> str:
    """Extract a snippet of code around the error position."""
    start = max(0, error_pos - context_size)
    end = min(len(json_string), error_pos + context_size)
    snippet = json_string[start:end]
    relative_pos = error_pos - start
    if relative_pos < len(snippet):
        snippet = (
            snippet[:relative_pos] + " <-- ERROR HERE --> " + snippet[relative_pos:]
        )
    return snippet


def detect_truncation(json_string: str) -> bool:
    """Detect if the JSON response appears to be truncated."""
    trimmed = json_string.rstrip()
    if not trimmed.endswith(("}", "]", '"')):
        open_braces = trimmed.count("{")
        close_braces = trimmed.count("}")
        open_brackets = trimmed.count("[")
        close_brackets = trimmed.count("]")
        if open_braces > close_braces or open_brackets > close_brackets:
            return True
    return False


def analyze_json_error(
    json_string: str, error: json.JSONDecodeError
) -> Dict[str, Any]:
    """
    Analyze JSON parsing error to extract comprehensive context.
    Returns structured error information for logging and retry prompts.
    """
    error_pos = getattr(error, "pos", len(json_string))
    error_line = getattr(error, "lineno", None)
    error_col = getattr(error, "colno", None)

    context_before = json_string[max(0, error_pos - 500) : error_pos]
    context_after = json_string[error_pos : min(len(json_string), error_pos + 500)]

    day_being_generated = identify_day_at_position(json_string, error_pos)
    field_being_generated = identify_field_at_position(json_string, error_pos)
    error_type = detect_error_type(error, json_string, error_pos)
    char_analysis = analyze_characters_around_error(json_string, error_pos)
    complete_days = find_complete_days_before_error(json_string, error_pos)

    return {
        "error_type": error_type,
        "error_position": error_pos,
        "error_position_percent": round((error_pos / len(json_string)) * 100, 2)
        if len(json_string) > 0
        else 0,
        "error_line": error_line,
        "error_column": error_col,
        "context_before": context_before,
        "context_after": context_after,
        "problematic_snippet": extract_problematic_snippet(json_string, error_pos),
        "day_being_generated": day_being_generated,
        "field_being_generated": field_being_generated,
        "response_length": len(json_string),
        "was_truncated": detect_truncation(json_string),
        "complete_days_before_error": complete_days,
        "character_analysis": char_analysis,
    }


def parse_llm_response(response_text: str) -> Dict[str, Any]:
    """
    Parse LLM response text to JSON. Strips markdown fences, pre-validates,
    and on JSONDecodeError attempts repair using error analysis.
    """
    cleaned = response_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    is_valid, pre_validation_error, pre_validation_fixes = pre_validate_json(cleaned)
    if (
        not is_valid
        and pre_validation_fixes
        and pre_validation_fixes.get("fixed_string")
    ):
        cleaned = pre_validation_fixes["fixed_string"]
        logger.info(
            "json_pre_validation_fixes_applied",
            extra={
                "pre_validation_error": pre_validation_error,
                "fixes_applied": pre_validation_fixes.get("fix_attempts", []),
            },
        )

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        original_error = str(e)
        error_analysis = analyze_json_error(cleaned, e)
        logger.warning(
            "json_parse_error_attempting_repair",
            extra={
                "error": original_error,
                "response_preview": cleaned[:500],
                "response_length": len(cleaned),
                "error_position": getattr(e, "pos", None),
                "error_type": error_analysis.get("error_type"),
                "error_position_percent": error_analysis.get("error_position_percent"),
                "day_being_generated": error_analysis.get("day_being_generated"),
                "field_being_generated": error_analysis.get("field_being_generated"),
                "complete_days_before_error": error_analysis.get(
                    "complete_days_before_error"
                ),
                "was_truncated": error_analysis.get("was_truncated"),
                "problematic_snippet": error_analysis.get("problematic_snippet"),
                "character_analysis": error_analysis.get("character_analysis"),
            },
        )
        error_pos = error_analysis.get("error_position")
        success, repaired, repair_error = repair_json(cleaned, error_pos, error_analysis)
        if success and repaired:
            logger.info(
                "json_repair_successful",
                extra={
                    "repair_message": repair_error,
                    "original_length": len(cleaned),
                    "repaired_length": len(repaired) if repaired else 0,
                },
            )
            try:
                parsed = json.loads(repaired)
                logger.info(
                    "json_repair_parse_success",
                    extra={
                        "salvaged_days": list(parsed.get("days", {}).keys())
                        if isinstance(parsed, dict)
                        else [],
                    },
                )
                return parsed
            except json.JSONDecodeError as e2:
                logger.error(
                    "json_repair_failed_to_parse",
                    extra={
                        "repair_error": str(e2),
                        "original_error": original_error,
                        "repaired_preview": repaired[:500] if repaired else None,
                    },
                )
        logger.error(
            "json_parse_error_repair_failed",
            extra={
                "original_error": original_error,
                "repair_error": repair_error,
                "response_preview": cleaned[:500],
                "response_length": len(cleaned),
                "error_analysis": error_analysis,
            },
        )
        error_with_analysis = ValueError(f"Failed to parse JSON: {original_error}")
        error_with_analysis.error_analysis = error_analysis  # type: ignore[attr-defined]
        raise error_with_analysis


def validate_structure(
    lesson_json: Dict[str, Any],
) -> Tuple[bool, Optional[str]]:
    """
    Validate JSON structure matches schema. Fills missing days with placeholders.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if "metadata" not in lesson_json or "days" not in lesson_json:
        error_msg = "Missing root keys: 'metadata' or 'days'"
        logger.error("schema_validation_failed", extra={"reason": error_msg})
        return False, error_msg

    metadata = lesson_json["metadata"]
    required_metadata = ["week_of", "grade", "subject"]
    for field in required_metadata:
        if field not in metadata:
            error_msg = f"Missing metadata.{field}"
            logger.error("schema_validation_failed", extra={"reason": error_msg})
            return False, error_msg

    days = lesson_json["days"]
    required_days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    missing_days = []
    for day in required_days:
        if day not in days:
            missing_days.append(day)
            logger.warning(
                "schema_validation_missing_day",
                extra={"day": day, "action": "Adding placeholder"},
            )

    no_school_placeholder = {
        "unit_lesson": "No School",
        "objective": {
            "content_objective": "No School",
            "student_goal": "No School",
            "wida_objective": "No School",
        },
        "anticipatory_set": {
            "original_content": "No School",
            "bilingual_bridge": "No School",
        },
        "vocabulary_cognates": [],
        "sentence_frames": [],
        "tailored_instruction": {
            "original_content": "No School",
            "co_teaching_model": {},
            "ell_support": [],
            "special_needs_support": [],
            "materials": [],
        },
        "misconceptions": {
            "original_content": "No School",
            "linguistic_note": {},
        },
        "assessment": {
            "primary_assessment": "No School",
            "bilingual_overlay": {},
        },
        "homework": {
            "original_content": "No School",
            "family_connection": "No School",
        },
    }

    if missing_days:
        for day in missing_days:
            days[day] = no_school_placeholder.copy()

        for day_name in required_days:
            if day_name not in days:
                continue
            day_data = days[day_name]
            if day_data.get("unit_lesson") == "No School":
                tailored_instruction = day_data.get("tailored_instruction", {})
                if isinstance(tailored_instruction, dict):
                    original_content = tailored_instruction.get("original_content", "")
                    if (
                        original_content
                        and original_content.strip()
                        and original_content.strip() != "No School"
                    ):
                        logger.info(
                            "preserving_tailored_instruction_content",
                            extra={"day": day_name, "has_content": True},
                        )
                    co_teaching = tailored_instruction.get("co_teaching_model", {})
                    if isinstance(co_teaching, dict) and co_teaching:
                        has_co_teaching_content = (
                            co_teaching.get("model_name")
                            or co_teaching.get("rationale")
                            or (
                                isinstance(co_teaching.get("phase_plan"), list)
                                and len(co_teaching.get("phase_plan", [])) > 0
                            )
                        )
                        if has_co_teaching_content:
                            logger.info(
                                "preserving_co_teaching_model",
                                extra={"day": day_name, "has_content": True},
                            )
                    for field in ["ell_support", "special_needs_support", "materials"]:
                        field_value = tailored_instruction.get(field, [])
                        if isinstance(field_value, list) and len(field_value) > 0:
                            logger.info(
                                "preserving_tailored_instruction_field",
                                extra={
                                    "day": day_name,
                                    "field": field,
                                    "count": len(field_value),
                                },
                            )

                objective = day_data.get("objective", {})
                if isinstance(objective, dict):
                    for obj_field in [
                        "content_objective",
                        "student_goal",
                        "wida_objective",
                    ]:
                        obj_value = objective.get(obj_field, "")
                        if (
                            obj_value
                            and obj_value.strip()
                            and obj_value.strip() != "No School"
                        ):
                            logger.info(
                                "preserving_objective_content",
                                extra={"day": day_name, "field": obj_field},
                            )

                anticipatory_set = day_data.get("anticipatory_set", {})
                if isinstance(anticipatory_set, dict):
                    for as_field in ["original_content", "bilingual_bridge"]:
                        as_value = anticipatory_set.get(as_field, "")
                        if (
                            as_value
                            and as_value.strip()
                            and as_value.strip() != "No School"
                        ):
                            logger.info(
                                "preserving_anticipatory_set_content",
                                extra={"day": day_name, "field": as_field},
                            )

        logger.info(
            "schema_validation_missing_days_filled",
            extra={"missing_days": missing_days, "filled_count": len(missing_days)},
        )

    monday = days["monday"]
    if "unit_lesson" not in monday:
        error_msg = "Missing monday.unit_lesson"
        logger.error("schema_validation_failed", extra={"reason": error_msg})
        return False, error_msg

    missing_fields = []
    for day_name in required_days:
        day_data = days.get(day_name, {})
        if not day_data or day_data.get("unit_lesson") == "No School":
            continue

        vocab = day_data.get("vocabulary_cognates")
        if vocab is None:
            missing_fields.append(f"{day_name}.vocabulary_cognates (missing)")
        elif not isinstance(vocab, list):
            missing_fields.append(f"{day_name}.vocabulary_cognates (not a list)")
        elif len(vocab) == 0:
            missing_fields.append(
                f"{day_name}.vocabulary_cognates (empty array - must have exactly 6 items)"
            )
        elif len(vocab) > 6:
            day_data["vocabulary_cognates"] = vocab[:6]
        elif len(vocab) != 6:
            missing_fields.append(
                f"{day_name}.vocabulary_cognates (has {len(vocab)} items, need exactly 6)"
            )

        frames = day_data.get("sentence_frames")
        if frames is None:
            missing_fields.append(f"{day_name}.sentence_frames (missing)")
        elif not isinstance(frames, list):
            missing_fields.append(f"{day_name}.sentence_frames (not a list)")
        elif len(frames) != 8:
            missing_fields.append(
                f"{day_name}.sentence_frames (has {len(frames)} items, need exactly 8)"
            )

    if missing_fields:
        error_msg = f"Missing or invalid required fields: {', '.join(missing_fields)}. vocabulary_cognates (exactly 6 items) and sentence_frames (exactly 8 items) are MANDATORY for all lesson days."
        logger.error(
            "schema_validation_missing_fields",
            extra={"missing_fields": missing_fields},
        )
        return False, error_msg

    logger.info("schema_validation_success")
    return True, None

"""
Parse Pydantic validation error messages into structured feedback.
Used by backend.llm.validation.parse_validation_errors (re-exported there).
"""

import re
from typing import Any, Dict, List


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
    parsed_errors: List[Dict[str, Any]] = []
    structure_confusion_detected = False
    enum_errors: List[Dict[str, Any]] = []
    pattern_errors: List[Dict[str, Any]] = []
    missing_field_errors: List[Dict[str, Any]] = []
    extra_field_errors: List[Dict[str, Any]] = []

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
            error_info: Dict[str, Any] = {
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

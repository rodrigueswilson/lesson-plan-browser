"""
JSON error analysis helpers: position/context and truncation detection.
Used by validation.analyze_json_error.
"""

import json
from typing import Any, Dict, List, Optional


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

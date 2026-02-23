"""
JSON Repair Helper
Attempts to fix common JSON syntax errors before validation.
"""

import json
import re
from typing import Any, Dict, Optional, Tuple

try:
    from json_repair import repair_json as json_repair_library_func
    JSON_REPAIR_AVAILABLE = True
except ImportError:
    JSON_REPAIR_AVAILABLE = False

from tools.json_repair_fixes import (
    apply_truncation_and_brace_fixes as _apply_truncation_and_brace_fixes,
    escape_control_chars as _escape_control_chars,
    fix_unescaped_quotes_in_strings as _fix_unescaped_quotes_in_strings,
    fix_unquoted_property_names as _fix_unquoted_property_names,
)


def repair_json(
    json_string: str, 
    error_pos: Optional[int] = None, 
    error_analysis: Optional[Dict[str, Any]] = None
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Attempt to repair common JSON syntax errors.

    Args:
        json_string: Potentially malformed JSON string
        error_pos: Optional error position to focus repair efforts
        error_analysis: Optional error analysis dictionary for context-aware repair

    Returns:
        Tuple of (success, repaired_json, error_message)
    """
    original = json_string
    original_error = ""

    # Try parsing as-is first
    try:
        json.loads(json_string)
        return True, json_string, None
    except json.JSONDecodeError as e:
        original_error = str(e)

    # NEW: Try robust json-repair library first if available
    if JSON_REPAIR_AVAILABLE:
        try:
            repaired_lib = json_repair_library_func(json_string)
            if repaired_lib and repaired_lib != json_string:
                # Validate the repaired JSON
                try:
                    json.loads(repaired_lib)
                    return True, repaired_lib, None
                except:
                    # If it's still not valid, continue to custom fixes
                    pass
        except Exception:
            # If library fails, continue to custom fixes
            pass

    # Common fixes to try
    fixes_applied = []
    repair_details = {
        "strategies_attempted": [],
        "fixes_applied": [],
        "positions_fixed": [],
    }
    
    # If error analysis is provided, prioritize repairs based on error type
    error_type = error_analysis.get("error_type") if error_analysis else None
    
    # Strategy 1: Fix unquoted property names (if error type suggests it or if detected)
    if error_type == "unquoted_property_name" or "expecting property name" in str(error_analysis.get("error", "")).lower() if error_analysis else False:
        repair_details["strategies_attempted"].append("fix_unquoted_property_names")
        try:
            fixed, fixes = _fix_unquoted_property_names(json_string, error_pos)
            if fixes:
                json_string = fixed
                fixes_applied.extend(fixes)
                repair_details["fixes_applied"].extend(fixes)
                repair_details["positions_fixed"].append(error_pos if error_pos else "unknown")
        except Exception as e:
            repair_details["strategies_attempted"].append(f"fix_unquoted_property_names (failed: {str(e)})")

    # Fix 1: Remove invalid control characters (newlines, tabs, etc. inside string values)
    json_string_escaped, control_fixes = _escape_control_chars(json_string)
    if control_fixes:
        json_string = json_string_escaped
        fixes_applied.extend(control_fixes)

    # Fix 1b: Remove markdown code blocks
    if json_string.strip().startswith("```"):
        json_string = re.sub(r"^```json\s*\n", "", json_string, flags=re.MULTILINE)
        json_string = re.sub(r"\n```\s*$", "", json_string, flags=re.MULTILINE)
        fixes_applied.append("Removed markdown code blocks")

    # Fix 2: Remove trailing commas in objects
    json_string = re.sub(r",(\s*[}\]])", r"\1", json_string)
    if "," in original and ",}" not in original and ",]" not in original:
        fixes_applied.append("Removed trailing commas")

    # Fix 3: Fix unescaped quotes inside string values
    if error_type == "syntax_error" and (
        "delimiter" in str(original_error).lower()
        or "expecting" in str(original_error).lower()
    ):
        repair_details["strategies_attempted"].append("fix_unescaped_quotes_in_strings")
        try:
            fixed, fixes = _fix_unescaped_quotes_in_strings(json_string, error_pos)
            if fixes:
                json_string = fixed
                fixes_applied.extend(fixes)
                repair_details["fixes_applied"].extend(fixes)
        except Exception as e:
            repair_details["strategies_attempted"].append(
                f"fix_unescaped_quotes_in_strings (failed: {str(e)})"
            )

    # Fix 4: Remove comments (// and /* */)
    json_string = re.sub(r"//.*?$", "", json_string, flags=re.MULTILINE)
    json_string = re.sub(r"/\*.*?\*/", "", json_string, flags=re.DOTALL)
    if "//" in original or "/*" in original:
        fixes_applied.append("Removed comments")

    # Fix 5: Replace single quotes with double quotes (risky but common)
    # Only do this if there are no double quotes already
    if "'" in json_string and '"' not in json_string:
        json_string = json_string.replace("'", '"')
        fixes_applied.append("Replaced single quotes with double quotes")

    # Fix 6-7b: Truncation and closing braces (delegated to json_repair_fixes)
    json_string, truncation_fixes = _apply_truncation_and_brace_fixes(
        json_string, original_error, error_pos, error_analysis
    )
    fixes_applied.extend(truncation_fixes)

    # Try parsing after fixes
    try:
        parsed = json.loads(json_string)
        # Verify it's actually valid by re-serializing
        json.dumps(parsed)

        message = (
            f"Repaired JSON successfully. Fixes applied: {', '.join(fixes_applied)}"
        )
        return True, json_string, message

    except json.JSONDecodeError as e:
        error_msg = f"Could not repair JSON. Original error: {original_error}. After fixes: {str(e)}"
        return False, None, error_msg


def extract_json_from_text(text: str) -> Optional[str]:
    """
    Extract JSON from text that may contain other content.

    Args:
        text: Text that may contain JSON

    Returns:
        Extracted JSON string or None
    """
    # Try to find JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)

    # Try to find JSON array
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        return match.group(0)

    return None


def validate_and_repair(json_string: str) -> Tuple[bool, Optional[dict], Optional[str]]:
    """
    Validate JSON and attempt repair if needed.

    Args:
        json_string: JSON string to validate/repair

    Returns:
        Tuple of (success, parsed_data, message)
    """
    # First try: parse as-is
    try:
        data = json.loads(json_string)
        return True, data, "Valid JSON"
    except json.JSONDecodeError:
        pass

    # Second try: extract JSON from text
    extracted = extract_json_from_text(json_string)
    if extracted and extracted != json_string:
        try:
            data = json.loads(extracted)
            return True, data, "Extracted JSON from surrounding text"
        except json.JSONDecodeError:
            json_string = extracted  # Use extracted for repair attempt

    # Third try: repair
    success, repaired, message = repair_json(json_string)

    if success and repaired:
        try:
            data = json.loads(repaired)
            return True, data, message
        except json.JSONDecodeError as e:
            return False, None, f"Repair succeeded but parsing failed: {str(e)}"

    return False, None, message or "Could not validate or repair JSON"


if __name__ == "__main__":
    # Test cases
    test_cases = [
        # Valid JSON
        '{"key": "value"}',
        # Trailing comma
        '{"key": "value",}',
        # Markdown code block
        '```json\n{"key": "value"}\n```',
        # Comments
        '{"key": "value" /* comment */}',
        # Missing closing brace
        '{"key": "value"',
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test[:50]}...")
        success, result, message = validate_and_repair(test)
        print(f"  Success: {success}")
        print(f"  Message: {message}")
        if result:
            print(f"  Result: {json.dumps(result, indent=2)[:100]}...")

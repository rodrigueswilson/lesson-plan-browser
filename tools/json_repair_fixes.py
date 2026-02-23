"""
JSON repair fix helpers: unquoted property names, control chars, unescaped quotes, truncation.
Used by json_repair.repair_json.
"""

import re
from typing import Any, Dict, List, Optional, Tuple


def escape_control_chars(text: str) -> Tuple[str, List[str]]:
    """
    Escape control characters in JSON string contexts.
    Replaces raw control chars inside strings with space.
    """
    result = []
    in_string = False
    escape_next = False
    fixes: List[str] = []

    i = 0
    while i < len(text):
        char = text[i]

        if escape_next:
            escape_next = False
            result.append(char)
            i += 1
            continue

        if char == "\\":
            escape_next = True
            result.append(char)
            i += 1
            continue

        if char == '"':
            in_string = not in_string
            result.append(char)
            i += 1
            continue

        if in_string and ord(char) < 32:
            result.append(" ")
            if not fixes:
                fixes.append("Replaced invalid control characters with spaces")
        else:
            result.append(char)

        i += 1

    return "".join(result), fixes


def fix_unescaped_quotes_in_strings(
    text: str, error_pos: Optional[int] = None
) -> Tuple[str, List[str]]:
    """Fix unescaped quotes inside string values."""
    fixes_applied: List[str] = []
    result = []
    in_string = False
    escape_next = False
    i = 0

    if error_pos is not None:
        start = max(0, error_pos - 2000)
        end = min(len(text), error_pos + 2000)
        focus_start = start
        focus_end = end
        segment = text[start:end]
        seg_start = 0
        seg_end = len(segment)
    else:
        start = 0
        end = len(text)
        focus_start = 0
        focus_end = len(text)
        segment = text
        seg_start = 0
        seg_end = len(segment)

    n = len(segment)
    while i < n:
        char = segment[i]

        if escape_next:
            escape_next = False
            result.append(char)
            i += 1
            continue

        if char == "\\":
            escape_next = True
            result.append(char)
            i += 1
            continue

        if char == '"':
            if in_string:
                lookahead = segment[i + 1 : min(i + 100, n)] if i + 1 < n else ""
                lookahead_stripped = lookahead.lstrip()
                should_escape = False

                if re.match(r"^\s*\w+\s*\":", lookahead):
                    should_escape = True
                elif re.match(r"^\s*\w+\s*\"", lookahead):
                    if '":' in lookahead[:20] or '": ' in lookahead[:20]:
                        should_escape = True
                elif re.match(r"^\s+\w+\s*\":", lookahead):
                    should_escape = True
                elif re.match(r"^\w+\s*\":", lookahead):
                    should_escape = True
                elif re.match(r"^\w+\s*:", lookahead) and '"' in lookahead[:10]:
                    should_escape = True
                elif re.search(r'(Target|WIDA)\s+"\w+":', lookahead[:50]):
                    should_escape = True
                elif re.search(r'\w+"\s*:', lookahead[:20]):
                    should_escape = True
                elif error_pos is not None and abs((start + i) - error_pos) < 200:
                    if (
                        re.search(r"\w+\s*\":", lookahead[:30])
                        or re.search(r"Target\s+\"\w+\":", lookahead[:50])
                        or re.search(r"WIDA\s+\"\w+\":", lookahead[:50])
                        or re.search(r'\w+"\s*:', lookahead[:30])
                    ):
                        should_escape = True

                if should_escape:
                    result.append('\\"')
                    fixes_applied.append("Escaped quote inside string at position")
                else:
                    result.append(char)
                    in_string = False
            else:
                result.append(char)
                in_string = True
            i += 1
            continue

        result.append(char)
        i += 1

    fixed_segment = "".join(result)
    if error_pos is not None and start < end:
        fixed_text = (
            text[:focus_start] + fixed_segment + text[focus_start + len(segment) :]
        )
    else:
        fixed_text = fixed_segment
    return fixed_text, fixes_applied


def apply_truncation_and_brace_fixes(
    json_string: str,
    original_error: str,
    error_pos: Optional[int],
    error_analysis: Optional[Dict[str, Any]],
) -> Tuple[str, List[str]]:
    """
    Handle truncated JSON: close incomplete strings, add missing braces/brackets.
    """
    fixes_applied: List[str] = []
    error_type = (
        error_analysis.get("error_type") if error_analysis else None
    )
    trimmed = json_string.rstrip()
    needs_closing = False

    if trimmed.endswith("\\"):
        json_string = trimmed.rstrip("\\") + '"'
        fixes_applied.append("Closed incomplete escaped string")
        needs_closing = True
    elif json_string.count('"') % 2 != 0:
        last_quote_idx = json_string.rfind('"')
        if last_quote_idx >= 0:
            remaining = json_string[last_quote_idx + 1 :]
            if '"' not in remaining or remaining.count('"') % 2 == 0:
                json_string += '"'
                fixes_applied.append("Closed truncated string")
                needs_closing = True

    if "Expecting property name" in str(original_error) or (
        error_analysis and error_analysis.get("error_type") == "incomplete_string"
    ):
        if error_pos is not None:
            scan_start = max(0, error_pos - 500)
            scan_area = json_string[scan_start : error_pos + 100]
            incomplete_pattern = re.search(r':\s*"([^"]*?)$', scan_area)
            if incomplete_pattern:
                relative_pos = incomplete_pattern.end()
                absolute_pos = scan_start + relative_pos
                json_string = json_string[:absolute_pos] + '"' + json_string[absolute_pos:]
                fixes_applied.append("Closed incomplete string value (position-aware)")
                needs_closing = True
        elif "Expecting property name" in str(original_error):
            incomplete_string_pattern = re.search(
                r'"([^"]+)":\s*"([^"]*?)$', json_string
            )
            if incomplete_string_pattern:
                json_string += '"'
                fixes_applied.append(
                    "Closed incomplete string value before property name error"
                )
                needs_closing = True
            else:
                last_colon_quote = json_string.rfind(': "')
                if last_colon_quote > 0:
                    remaining_after_colon = json_string[last_colon_quote + 3 :]
                    if '"' not in remaining_after_colon:
                        json_string += '"'
                        fixes_applied.append(
                            "Closed incomplete string value (no closing quote found)"
                        )
                        needs_closing = True

    if not trimmed.endswith(("}", "]", '"', ",", ":", "[", "{")):
        if re.search(r'"[^"]*"\s*$', trimmed):
            json_string = trimmed + ": null"
            fixes_applied.append("Closed truncated key-value pair")
            needs_closing = True
        elif re.search(r'"[^"]*"\s*:\s*$', trimmed):
            json_string = trimmed + " null"
            fixes_applied.append("Closed truncated key-value pair")
            needs_closing = True
        elif trimmed.endswith('"'):
            if not re.search(r':\s*"[^"]*"$', trimmed):
                fixes_applied.append("Detected possible string truncation")

    if "Expecting property name" in str(original_error) or error_type == "unquoted_property_name":
        fixes_applied.append(
            "Detected property name error - attempting aggressive repair"
        )
        needs_closing = True
        escape_scan = False
        for i in range(len(json_string) - 1, -1, -1):
            char = json_string[i]
            if escape_scan:
                escape_scan = False
                continue
            if char == "\\":
                escape_scan = True
                continue
            if char == '"' and i < len(json_string) - 1:
                next_char = json_string[i + 1]
                if next_char not in [":", ",", "}", "]", " ", "\n", "\t"]:
                    remaining_text = json_string[i + 1 :]
                    if '"' not in remaining_text:
                        json_string = json_string[: i + 1] + '"'
                        fixes_applied.append(
                            "Closed incomplete string value causing property name error"
                        )
                        break

        day_patterns = [
            '"monday":',
            '"tuesday":',
            '"wednesday":',
            '"thursday":',
            '"friday":',
        ]
        last_complete_day = -1
        for day_pattern in day_patterns:
            day_idx = json_string.rfind(day_pattern)
            if day_idx > last_complete_day:
                last_complete_day = day_idx

        if last_complete_day > 0:
            remaining = json_string[last_complete_day:]
            brace_count = 0
            in_string_count = False
            escape_count = False
            truncate_pos = -1
            for idx, ch in enumerate(remaining):
                if escape_count:
                    escape_count = False
                    continue
                if ch == "\\":
                    escape_count = True
                    continue
                if ch == '"':
                    in_string_count = not in_string_count
                    continue
                if not in_string_count:
                    if ch == "{":
                        brace_count += 1
                    elif ch == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            truncate_pos = last_complete_day + idx + 1
                            break
            if truncate_pos > 0 and truncate_pos < len(json_string):
                json_string = json_string[:truncate_pos]
                fixes_applied.append(
                    f"Truncated at last complete day structure (position {truncate_pos})"
                )

    last_valid_pos = len(json_string)
    in_string = False
    escape_next = False
    for i in range(len(json_string) - 1, -1, -1):
        char = json_string[i]
        if escape_next:
            escape_next = False
            continue
        if char == "\\":
            escape_next = True
            continue
        if char == '"':
            in_string = not in_string
            if in_string and i < len(json_string) - 100:
                remaining = json_string[i:]
                if remaining.count('"') % 2 != 0:
                    json_string = json_string[: i + 1] + '"'
                    fixes_applied.append("Closed truncated string found mid-value")
                    last_valid_pos = i + 2
                    break

    open_braces = 0
    open_brackets = 0
    in_string = False
    escape_next = False
    for i, char in enumerate(json_string):
        if i >= last_valid_pos:
            break
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
                open_braces += 1
            elif char == "}":
                open_braces -= 1
            elif char == "[":
                open_brackets += 1
            elif char == "]":
                open_brackets -= 1

    if open_brackets > 0:
        json_string += "]" * open_brackets
        fixes_applied.append(f"Added {open_brackets} closing bracket(s)")
    if open_braces > 0:
        json_string += "}" * open_braces
        fixes_applied.append(f"Added {open_braces} closing brace(s)")

    return json_string, fixes_applied


def fix_unquoted_property_names(
    json_string: str, error_pos: Optional[int] = None
) -> Tuple[str, List[str]]:
    """
    Detect and fix unquoted property names.

    Pattern: key: value (where key is not quoted)
    Fix: "key": value
    """
    fixes_applied = []

    # Focus on area around error if position provided
    if error_pos:
        start = max(0, error_pos - 1000)
        end = min(len(json_string), error_pos + 1000)
        focus_area = json_string[start:end]
        focus_start = start
    else:
        focus_area = json_string
        focus_start = 0

    # Pattern: word followed by colon (not inside string, not already quoted)
    def is_inside_string(text: str, pos: int) -> bool:
        """Check if position is inside a string"""
        before = text[:pos]
        quote_count = 0
        escape_next = False
        for char in before:
            if escape_next:
                escape_next = False
                continue
            if char == "\\":
                escape_next = True
                continue
            if char == '"':
                quote_count += 1
        return quote_count % 2 != 0

    # Find unquoted property names
    pattern = r'(?<!["\w])(\w+):\s*(["\d\[\{])'
    matches = list(re.finditer(pattern, focus_area))
    valid_matches = [m for m in matches if not is_inside_string(focus_area, m.start())]

    if valid_matches:
        fixed_area = focus_area
        for match in reversed(valid_matches):
            key = match.group(1)
            value_start = match.group(2)
            replacement = f'"{key}": {value_start}'
            fixed_area = (
                fixed_area[: match.start()] + replacement + fixed_area[match.end() :]
            )
            fixes_applied.append(f"Quoted property name '{key}'")

        if fixes_applied:
            json_string = (
                json_string[:focus_start]
                + fixed_area
                + json_string[focus_start + len(focus_area) :]
            )

    return json_string, fixes_applied

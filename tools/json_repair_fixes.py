"""
JSON repair fix helpers: unquoted property names, etc.
Used by json_repair.repair_json.
"""

import re
from typing import List, Optional, Tuple


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

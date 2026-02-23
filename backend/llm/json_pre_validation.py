"""
Pre-validate JSON string for common issues before parsing (unquoted keys, trailing commas, etc.).
"""

import re
from typing import Any, Dict, Optional, Tuple


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

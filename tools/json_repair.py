"""
JSON Repair Helper
Attempts to fix common JSON syntax errors before validation.
"""

import json
import re
from typing import Optional, Tuple, Dict, Any, List

try:
    from json_repair import repair_json as json_repair_library_func
    JSON_REPAIR_AVAILABLE = True
except ImportError:
    JSON_REPAIR_AVAILABLE = False


def _fix_unquoted_property_names(json_string: str, error_pos: Optional[int] = None) -> Tuple[str, List[str]]:
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
    # Match: \w+: (but not "key":)
    # We need to be careful not to match inside strings
    def is_inside_string(text: str, pos: int) -> bool:
        """Check if position is inside a string"""
        before = text[:pos]
        # Count unescaped quotes
        quote_count = 0
        escape_next = False
        for char in before:
            if escape_next:
                escape_next = False
                continue
            if char == '\\':
                escape_next = True
                continue
            if char == '"':
                quote_count += 1
        return quote_count % 2 != 0
    
    # Find unquoted property names
    # Pattern: word boundary, word characters, colon, whitespace, then quote or bracket or digit or brace
    pattern = r'(?<!["\w])(\w+):\s*(["\d\[\{])'
    
    matches = list(re.finditer(pattern, focus_area))
    # Filter out matches inside strings
    valid_matches = [m for m in matches if not is_inside_string(focus_area, m.start())]
    
    if valid_matches:
        # Replace from end to start to preserve positions
        fixed_area = focus_area
        for match in reversed(valid_matches):
            key = match.group(1)
            value_start = match.group(2)
            replacement = f'"{key}": {value_start}'
            fixed_area = fixed_area[:match.start()] + replacement + fixed_area[match.end():]
            fixes_applied.append(f"Quoted property name '{key}'")
        
        if fixes_applied:
            json_string = json_string[:focus_start] + fixed_area + json_string[focus_start + len(focus_area):]
    
    return json_string, fixes_applied


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
    # JSON doesn't allow raw control characters (except in escaped form: \n, \r, \t)
    # Replace invalid control chars with their Unicode escape sequences or spaces
    def escape_control_chars(text):
        """Escape control characters in JSON string contexts."""
        result = []
        in_string = False
        escape_next = False

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

            # Inside string: replace invalid control chars
            if in_string and ord(char) < 32:
                # Replace control chars with space (safer than trying to escape)
                # JSON doesn't allow raw control chars except escaped \n, \r, \t
                # If they're already part of the string, replace with space
                result.append(" ")  # Replace with space for simplicity
                if "Escaped control characters" not in fixes_applied:
                    fixes_applied.append(
                        "Replaced invalid control characters with spaces"
                    )
            else:
                result.append(char)

            i += 1

        return "".join(result)

    # Apply control character escaping
    json_string_escaped = escape_control_chars(json_string)
    if json_string_escaped != json_string:
        json_string = json_string_escaped

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
    # This handles cases like: "key": "value with "unquoted" text"
    # Pattern: quote inside a string (not at string boundaries, not already escaped)
    def fix_unescaped_quotes_in_strings(text: str, error_pos: Optional[int] = None) -> Tuple[str, List[str]]:
        """Fix unescaped quotes inside string values"""
        fixes_applied = []
        result = []
        in_string = False
        escape_next = False
        i = 0
        
        # Focus on area around error if position provided
        if error_pos:
            start = max(0, error_pos - 2000)
            end = min(len(text), error_pos + 2000)
            focus_start = start
            focus_end = end
        else:
            start = 0
            end = len(text)
            focus_start = 0
            focus_end = len(text)
        
        # Process character by character
        while i < len(text):
            char = text[i]
            
            if escape_next:
                escape_next = False
                result.append(char)
                i += 1
                continue
            
            if char == '\\':
                escape_next = True
                result.append(char)
                i += 1
                continue
            
            if char == '"':
                if in_string:
                    # We're inside a string and found a quote
                    # Check if this looks like an unescaped quote (not closing the string)
                    # Look ahead to see if this is followed by word chars and then colon/comma/brace
                    lookahead = text[i+1:min(i+100, len(text))] if i+1 < len(text) else ""
                    lookahead_stripped = lookahead.lstrip()
                    
                    # Pattern detection: quote inside string followed by word then colon/quote
                    # Common patterns:
                    # 1. " levels":  (space, word, quote, colon)
                    # 2. "levels":   (word, quote, colon)
                    # 3. " levels"   (space, word, quote)
                    # 4. "levels"    (word, quote)
                    should_escape = False
                    
                    # Check for pattern: quote followed by optional space, word, then quote and colon
                    # Pattern 1: " levels": or "levels": (most common)
                    if re.match(r'^\s*\w+\s*":', lookahead):
                        should_escape = True
                    # Pattern 2: " levels" or "levels" followed by quote and colon nearby
                    elif re.match(r'^\s*\w+\s*"', lookahead):
                        # Check if there's a colon nearby (within next 20 chars)
                        if '":' in lookahead[:20] or '": ' in lookahead[:20]:
                            should_escape = True
                    # Pattern 3: " levels": (with space before word)
                    elif re.match(r'^\s+\w+\s*":', lookahead):
                        should_escape = True
                    # Pattern 4: Direct word followed by quote and colon (no space) - "levels":
                    elif re.match(r'^\w+\s*":', lookahead):
                        should_escape = True
                    # Pattern 5: Word, quote, colon (like "levels":)
                    elif re.match(r'^\w+\s*:', lookahead) and '"' in lookahead[:10]:
                        should_escape = True
                    # Pattern 6: Specific common patterns that cause issues
                    # "Target "levels": or "WIDA "levels": or "Target WIDA "levels":
                    elif re.search(r'(Target|WIDA)\s+"\w+":', lookahead[:50]):
                        should_escape = True
                    # Pattern 7: Any word followed immediately by quote and colon (no space)
                    elif re.search(r'\w+"\s*:', lookahead[:20]):
                        should_escape = True
                    # If near error position, be more aggressive
                    elif error_pos and abs(i - error_pos) < 200:
                        # Near error, check for any word followed by quote and colon
                        # Also check for common patterns like "Target "levels":"
                        if (re.search(r'\w+\s*":', lookahead[:30]) or 
                            re.search(r'Target\s+"\w+":', lookahead[:50]) or
                            re.search(r'WIDA\s+"\w+":', lookahead[:50]) or
                            re.search(r'\w+"\s*:', lookahead[:30])):
                            should_escape = True
                    
                    if should_escape:
                        # This is likely an unescaped quote inside the string - escape it
                        result.append('\\"')
                        fixes_applied.append(f"Escaped quote inside string at position {i}")
                        # Don't toggle in_string - we're still inside the original string
                    else:
                        # This might be closing the string
                        result.append(char)
                        in_string = False
                else:
                    # Opening a new string
                    result.append(char)
                    in_string = True
                i += 1
                continue
            
            result.append(char)
            i += 1
        
        fixed_text = ''.join(result)
        return fixed_text, fixes_applied
    
    # Apply unescaped quote fix if error suggests it
    if error_type == "syntax_error" and ("delimiter" in str(original_error).lower() or "expecting" in str(original_error).lower()):
        repair_details["strategies_attempted"].append("fix_unescaped_quotes_in_strings")
        try:
            fixed, fixes = fix_unescaped_quotes_in_strings(json_string, error_pos)
            if fixes:
                json_string = fixed
                fixes_applied.extend(fixes)
                repair_details["fixes_applied"].extend(fixes)
        except Exception as e:
            repair_details["strategies_attempted"].append(f"fix_unescaped_quotes_in_strings (failed: {str(e)})")

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

    # Fix 6: Handle truncated JSON by trying to close incomplete structures
    # Check if JSON appears to be cut off mid-value
    trimmed = json_string.rstrip()

    # Check for truncation patterns - be more aggressive in detecting and fixing
    needs_closing = False
    truncation_pattern = None

    # Pattern 1: Ends with incomplete string (escape sequence)
    if trimmed.endswith("\\"):
        json_string = trimmed.rstrip("\\") + '"'
        fixes_applied.append("Closed incomplete escaped string")
        needs_closing = True

    # Pattern 2: Odd number of quotes - likely truncated string
    elif json_string.count('"') % 2 != 0:
        # Find the last unclosed quote and close it
        last_quote_idx = json_string.rfind('"')
        if last_quote_idx >= 0:
            # Check if it's actually unclosed (no matching quote after)
            remaining = json_string[last_quote_idx + 1 :]
            if '"' not in remaining or remaining.count('"') % 2 == 0:
                json_string += '"'
                fixes_applied.append("Closed truncated string")
                needs_closing = True

    # Pattern 3: Detect truncation mid-string value (common pattern: "key": "incomplete text)
    # Look for patterns like: "student_goal": "I will read and wri (cut off)
    # This pattern appears before "Expecting property name" errors
    # Use position-aware detection if error_pos is provided
    if "Expecting property name" in str(original_error) or (error_analysis and error_analysis.get("error_type") == "incomplete_string"):
        # If error position is provided, focus scanning around that area
        if error_pos:
            # Scan backwards from error position to find incomplete strings
            scan_start = max(0, error_pos - 500)
            scan_area = json_string[scan_start:error_pos + 100]
            
            # Look for incomplete string patterns near error position
            incomplete_pattern = re.search(r':\s*"([^"]*?)$', scan_area)
            if incomplete_pattern:
                # Found incomplete string - close it
                relative_pos = incomplete_pattern.end()
                absolute_pos = scan_start + relative_pos
                json_string = json_string[:absolute_pos] + '"' + json_string[absolute_pos:]
                fixes_applied.append("Closed incomplete string value (position-aware)")
                needs_closing = True
        elif "Expecting property name" in str(original_error):
            # Try to find incomplete string values and close them
            # Look for: "key": "incomplete_text (no closing quote)
            incomplete_string_pattern = re.search(r'"([^"]+)":\s*"([^"]*?)$', json_string)
            if incomplete_string_pattern:
                # Found an incomplete string value - close it
                json_string += '"'
                fixes_applied.append(
                    "Closed incomplete string value before property name error"
                )
                needs_closing = True
            else:
                # Try to find any incomplete string near the end
                # Look for last occurrence of : " followed by text without closing quote
                last_colon_quote = json_string.rfind(': "')
                if last_colon_quote > 0:
                    remaining_after_colon = json_string[last_colon_quote + 3 :]
                    if '"' not in remaining_after_colon:
                        # No closing quote found - this is an incomplete string
                        json_string += '"'
                        fixes_applied.append(
                            "Closed incomplete string value (no closing quote found)"
                        )
                        needs_closing = True

    # Pattern 4: Ends with key name but no value (e.g., "key": or just "key")
    # This handles "Expecting ':' delimiter" and "Expecting ',' delimiter" errors
    elif not trimmed.endswith(("}", "]", '"', ",", ":", "[", "{")):
        # Check if ends with incomplete value (common truncation patterns)
        if re.search(r'"[^"]*"\s*$', trimmed):
            # Ends with a quoted string (likely a key), add ": null"
            json_string = trimmed + ": null"
            fixes_applied.append("Closed truncated key-value pair")
            needs_closing = True
        elif re.search(r'"[^"]*"\s*:\s*$', trimmed):
            # Ends with key and colon, add null value
            json_string = trimmed + " null"
            fixes_applied.append("Closed truncated key-value pair")
            needs_closing = True
        elif trimmed.endswith('"'):
            # Ends mid-string, try to find if it's a value or key
            # If preceded by colon, it's a value - close it
            if re.search(r':\s*"[^"]*"$', trimmed):
                # Actually looks complete, might be different issue
                pass
            else:
                # Might be truncated mid-string
                fixes_applied.append("Detected possible string truncation")

    # Pattern 4: Handle "Expecting property name" errors - usually means truncation mid-object
    # This happens when JSON is cut off in the middle of an object definition or mid-string
    # Use position-aware repair if error_pos is provided
    if "Expecting property name" in str(original_error) or error_type == "unquoted_property_name":
        fixes_applied.append(
            "Detected property name error - attempting aggressive repair"
        )
        needs_closing = True

        # First, try to close any incomplete string values
        # Look for patterns like: "key": "incomplete_text (no closing quote)
        # Scan backwards from end to find incomplete strings
        in_string_scan = False
        escape_scan = False
        last_open_quote = -1

        for i in range(len(json_string) - 1, -1, -1):
            char = json_string[i]
            if escape_scan:
                escape_scan = False
                continue
            if char == "\\":
                escape_scan = True
                continue
            if char == '"':
                # Check if this quote starts a string or ends one
                # If followed by : or , or } or ], it's likely a key or end of value
                # If followed by text, it's the start of a value (and we're mid-string)
                if i < len(json_string) - 1:
                    next_char = json_string[i + 1]
                    if next_char not in [":", ",", "}", "]", " ", "\n", "\t"]:
                        # This looks like the start of an incomplete string value
                        last_open_quote = i
                        # Check if there's a closing quote after this
                        remaining_text = json_string[i + 1 :]
                        if '"' not in remaining_text:
                            # No closing quote - this is an incomplete string
                            # Close it and break
                            json_string = json_string[: i + 1] + '"'
                            fixes_applied.append(
                                "Closed incomplete string value causing property name error"
                            )
                            break

        # If we still have the error, try finding last complete day structure
        # Try to find a safe truncation point - look for last complete day object
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

        # If we found a day pattern, try to truncate after that day's complete structure
        if last_complete_day > 0:
            # Find the closing brace for that day's object
            remaining = json_string[last_complete_day:]
            brace_count = 0
            in_string_count = False
            escape_count = False
            truncate_pos = -1

            for i, char in enumerate(remaining):
                if escape_count:
                    escape_count = False
                    continue
                if char == "\\":
                    escape_count = True
                    continue
                if char == '"':
                    in_string_count = not in_string_count
                    continue
                if not in_string_count:
                    if char == "{":
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            truncate_pos = last_complete_day + i + 1
                            break

            # If we found a complete day structure, truncate there and close remaining structures
            if truncate_pos > 0 and truncate_pos < len(json_string):
                json_string = json_string[:truncate_pos]
                fixes_applied.append(
                    f"Truncated at last complete day structure (position {truncate_pos})"
                )

    # Fix 7: Handle truncated JSON mid-string or mid-value
    # This is a more aggressive repair for cases where JSON is cut off
    # Try to find the last valid position and close structures from there

    # First, try to close any incomplete strings
    in_string = False
    escape_next = False
    last_valid_pos = len(json_string)

    # Scan backwards to find where we might have been cut off
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
            # If we're in a string and find an opening quote, we might be mid-string
            if in_string and i < len(json_string) - 100:  # Not near the end
                # Check if this might be a truncation point
                remaining = json_string[i:]
                # If remaining has unbalanced quotes, we were cut off mid-string
                if remaining.count('"') % 2 != 0:
                    # Close the string and any open structures
                    json_string = json_string[: i + 1] + '"'
                    fixes_applied.append("Closed truncated string found mid-value")
                    last_valid_pos = i + 2
                    break

    # Fix 7b: Add missing closing braces/brackets (accounting for strings)
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

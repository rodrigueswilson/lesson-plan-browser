"""
JSON Repair Helper
Attempts to fix common JSON syntax errors before validation.
"""

import json
import re
from typing import Tuple, Optional


def repair_json(json_string: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Attempt to repair common JSON syntax errors.
    
    Args:
        json_string: Potentially malformed JSON string
        
    Returns:
        Tuple of (success, repaired_json, error_message)
    """
    original = json_string
    
    # Try parsing as-is first
    try:
        json.loads(json_string)
        return True, json_string, None
    except json.JSONDecodeError as e:
        original_error = str(e)
    
    # Common fixes to try
    fixes_applied = []
    
    # Fix 1: Remove markdown code blocks
    if json_string.strip().startswith('```'):
        json_string = re.sub(r'^```json\s*\n', '', json_string, flags=re.MULTILINE)
        json_string = re.sub(r'\n```\s*$', '', json_string, flags=re.MULTILINE)
        fixes_applied.append("Removed markdown code blocks")
    
    # Fix 2: Remove trailing commas in objects
    json_string = re.sub(r',(\s*[}\]])', r'\1', json_string)
    if ',' in original and ',}' not in original and ',]' not in original:
        fixes_applied.append("Removed trailing commas")
    
    # Fix 3: Fix unescaped quotes in strings (basic attempt)
    # This is tricky and may not work in all cases
    # json_string = re.sub(r'(?<!\\)"(?=\w)', r'\\"', json_string)
    
    # Fix 4: Remove comments (// and /* */)
    json_string = re.sub(r'//.*?$', '', json_string, flags=re.MULTILINE)
    json_string = re.sub(r'/\*.*?\*/', '', json_string, flags=re.DOTALL)
    if '//' in original or '/*' in original:
        fixes_applied.append("Removed comments")
    
    # Fix 5: Replace single quotes with double quotes (risky but common)
    # Only do this if there are no double quotes already
    if "'" in json_string and '"' not in json_string:
        json_string = json_string.replace("'", '"')
        fixes_applied.append("Replaced single quotes with double quotes")
    
    # Fix 6: Add missing closing braces/brackets (very basic)
    open_braces = json_string.count('{') - json_string.count('}')
    open_brackets = json_string.count('[') - json_string.count(']')
    
    if open_braces > 0:
        json_string += '}' * open_braces
        fixes_applied.append(f"Added {open_braces} closing brace(s)")
    
    if open_brackets > 0:
        json_string += ']' * open_brackets
        fixes_applied.append(f"Added {open_brackets} closing bracket(s)")
    
    # Try parsing after fixes
    try:
        parsed = json.loads(json_string)
        # Verify it's actually valid by re-serializing
        json.dumps(parsed)
        
        message = f"Repaired JSON successfully. Fixes applied: {', '.join(fixes_applied)}"
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
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)
    
    # Try to find JSON array
    match = re.search(r'\[.*\]', text, re.DOTALL)
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


if __name__ == '__main__':
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

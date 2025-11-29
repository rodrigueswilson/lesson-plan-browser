"""
Shared utilities for strategy conversion operations.
Handles normalization, formatting, and common transformations.
"""

import re
from typing import Any, Dict, List, Union
from decimal import Decimal, ROUND_HALF_UP


def normalize_array(value: Union[str, List[str]], delimiter: str = ',') -> List[str]:
    """
    Normalize input to a list of strings.
    
    Args:
        value: String (comma/delimiter-separated) or list
        delimiter: Character to split on if value is string
        
    Returns:
        List of trimmed, non-empty strings
    """
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    
    if isinstance(value, str):
        return [item.strip() for item in value.split(delimiter) if item.strip()]
    
    return []


def format_skill_weights(weights: Dict[str, float], precision: int = 4) -> str:
    """
    Format skill weights dictionary as readable string.
    
    Args:
        weights: Dict with speaking, listening, reading, writing keys
        precision: Decimal places to display (default 4 to preserve values like 0.1667)
        
    Returns:
        Formatted string like "speaking: 0.0000; listening: 0.0000; reading: 0.5000; writing: 0.5000"
    """
    skills = ['speaking', 'listening', 'reading', 'writing']
    # Strip trailing zeros for cleaner output
    parts = []
    for skill in skills:
        value = weights.get(skill, 0.0)
        formatted = f"{value:.{precision}f}".rstrip('0').rstrip('.')
        parts.append(f"{skill}: {formatted}")
    return '; '.join(parts)


def parse_skill_weights(text: str) -> Dict[str, float]:
    """
    Parse skill weights string back to dictionary.
    
    Args:
        text: String like "speaking: 0.0; listening: 0.0; reading: 0.5; writing: 0.5"
        
    Returns:
        Dict with float values for each skill
    """
    weights = {'speaking': 0.0, 'listening': 0.0, 'reading': 0.0, 'writing': 0.0}
    
    # Match pattern: skill_name: number
    pattern = r'(\w+):\s*([\d.]+)'
    matches = re.findall(pattern, text)
    
    for skill, value in matches:
        if skill in weights:
            weights[skill] = float(value)
    
    return weights


def normalize_decimal(value: float, precision: int = 1) -> float:
    """
    Normalize decimal to specified precision using banker's rounding.
    
    Args:
        value: Float value to normalize
        precision: Decimal places
        
    Returns:
        Normalized float
    """
    decimal_value = Decimal(str(value))
    quantizer = Decimal(10) ** -precision
    return float(decimal_value.quantize(quantizer, rounding=ROUND_HALF_UP))


def validate_skill_weights(weights: Dict[str, float], tolerance: float = 0.01) -> bool:
    """
    Validate that skill weights sum to approximately 1.0 (or 0.0 for none).
    
    Args:
        weights: Dict with skill weights
        tolerance: Acceptable deviation from 1.0
        
    Returns:
        True if valid, False otherwise
    """
    total = sum(weights.values())
    return abs(total - 1.0) <= tolerance or abs(total) <= tolerance


def format_list_as_bullets(items: List[str], indent: int = 0) -> str:
    """
    Format list items as Markdown bullet points.
    
    Args:
        items: List of strings
        indent: Number of spaces to indent
        
    Returns:
        Markdown bullet list
    """
    prefix = ' ' * indent
    return '\n'.join(f"{prefix}- {item}" for item in items)


def parse_bullet_list(text: str) -> List[str]:
    """
    Parse Markdown bullet list back to array.
    
    Args:
        text: Markdown text with bullet points
        
    Returns:
        List of bullet point contents
    """
    lines = text.strip().split('\n')
    items = []
    
    for line in lines:
        # Match various bullet formats: -, *, •, 1., etc.
        match = re.match(r'^[\s]*[-*•][\s]+(.+)$', line)
        if match:
            items.append(match.group(1).strip())
        else:
            # Also handle numbered lists
            match = re.match(r'^[\s]*\d+\.[\s]+(.+)$', line)
            if match:
                items.append(match.group(1).strip())
    
    return items


def sanitize_id(text: str) -> str:
    """
    Convert text to valid snake_case ID.
    
    Args:
        text: Input text
        
    Returns:
        snake_case identifier
    """
    # Convert to lowercase
    text = text.lower()
    # Replace spaces and hyphens with underscores
    text = re.sub(r'[\s-]+', '_', text)
    # Remove non-alphanumeric characters except underscores
    text = re.sub(r'[^a-z0-9_]', '', text)
    # Remove leading/trailing underscores
    text = text.strip('_')
    # Collapse multiple underscores
    text = re.sub(r'_+', '_', text)
    
    return text


def extract_sentinel_section(text: str, sentinel: str, next_sentinel: str = None) -> str:
    """
    Extract content between sentinel markers.
    
    Args:
        text: Full text to search
        sentinel: Starting marker (e.g., "**Core Principle:**")
        next_sentinel: Optional ending marker (if None, goes to next heading or end)
        
    Returns:
        Extracted content, stripped of markers
    """
    # Escape special regex characters in sentinel
    sentinel_pattern = re.escape(sentinel)
    
    if next_sentinel:
        next_pattern = re.escape(next_sentinel)
        pattern = f"{sentinel_pattern}\\s*(.+?)\\s*{next_pattern}"
    else:
        # Match until next heading (###, **Field:**) or end of string
        pattern = f"{sentinel_pattern}\\s*(.+?)(?=\\n\\n###|\\n\\n\\*\\*|\\Z)"
    
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    
    return ""


def format_field_value(value: Any, field_type: str = 'string') -> str:
    """
    Format field value for Markdown display.
    
    Args:
        value: Field value
        field_type: Type hint (string, array, object, etc.)
        
    Returns:
        Formatted string
    """
    if value is None:
        return ""
    
    if field_type == 'array':
        if isinstance(value, list):
            return ', '.join(str(item) for item in value)
        return str(value)
    
    if field_type == 'object':
        if isinstance(value, dict):
            return '; '.join(f"{k}: {v}" for k, v in value.items())
        return str(value)
    
    return str(value)


def deep_merge_dicts(base: Dict, updates: Dict) -> Dict:
    """
    Deep merge two dictionaries, with updates taking precedence.
    
    Args:
        base: Base dictionary
        updates: Dictionary with updates
        
    Returns:
        Merged dictionary
    """
    result = base.copy()
    
    for key, value in updates.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result

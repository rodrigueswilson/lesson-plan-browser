"""
Date formatting utilities for lesson plan processing.

Standardizes week date formats to MM/DD-MM/DD for consistency.
"""

import re
from typing import Optional


def format_week_dates(week_of: str) -> str:
    """
    Standardize week date format to MM/DD-MM/DD.
    
    Handles various input formats:
    - "10-27-10-31" → "10/27-10/31"
    - "10/27-10/31" → "10/27-10/31" (already correct)
    - "10-27 to 10-31" → "10/27-10/31"
    - "Week of 10/27" → "10/27-10/31" (assumes 5-day week)
    - "10/27/2025-10/31/2025" → "10/27-10/31" (strips year)
    - "10-27-2025 to 10-31-2025" → "10/27-10/31"
    
    Args:
        week_of: Week date string in various formats
        
    Returns:
        Standardized format MM/DD-MM/DD, or original string if unparseable
        
    Examples:
        >>> format_week_dates("10-27-10-31")
        '10/27-10/31'
        >>> format_week_dates("Week of 10/27-10/31")
        '10/27-10/31'
        >>> format_week_dates("10-27 to 10-31")
        '10/27-10/31'
    """
    if not week_of:
        return ""
    
    # Remove common prefixes and extra whitespace
    cleaned = week_of.replace("Week of", "").replace("week of", "").strip()
    cleaned = re.sub(r'\s+', '', cleaned)  # Remove all whitespace
    cleaned = cleaned.replace("to", "-").replace("TO", "-")
    
    # Pattern to match dates: MM/DD or MM-DD, optionally with /YYYY or -YYYY
    # Captures month and day, ignoring year if present
    date_pattern = r'(\d{1,2})[/-](\d{1,2})(?:[/-]\d{4})?'
    matches = re.findall(date_pattern, cleaned)
    
    if len(matches) >= 2:
        # Found start and end dates
        start_month, start_day = matches[0]
        end_month, end_day = matches[1]
        return f"{start_month}/{start_day}-{end_month}/{end_day}"
    
    elif len(matches) == 1:
        # Only start date found - assume 5-day week (Monday-Friday)
        start_month, start_day = matches[0]
        start_day_int = int(start_day)
        
        # Simple calculation: add 4 days
        # Note: This doesn't handle month boundaries correctly
        # For production, consider using datetime for proper date arithmetic
        end_day_int = start_day_int + 4
        
        # If end day goes past reasonable day count, keep same month
        # (This is a simplification - real implementation should handle month boundaries)
        if end_day_int <= 31:
            return f"{start_month}/{start_day}-{start_month}/{end_day_int}"
        else:
            # Month boundary - just use start date
            return f"{start_month}/{start_day}-{start_month}/{start_day}"
    
    # Fallback: try to parse "10-27-10-31" format (all hyphens, no year)
    parts = cleaned.split("-")
    if len(parts) == 4 and all(p.isdigit() for p in parts):
        return f"{parts[0]}/{parts[1]}-{parts[2]}/{parts[3]}"
    
    # Can't parse - return original
    return week_of


def validate_week_format(week_of: str) -> bool:
    """
    Validate that week_of is in MM/DD-MM/DD format.
    
    Args:
        week_of: Week date string
        
    Returns:
        True if valid format, False otherwise
        
    Examples:
        >>> validate_week_format("10/27-10/31")
        True
        >>> validate_week_format("10-27-10-31")
        False
        >>> validate_week_format("invalid")
        False
    """
    if not week_of:
        return False
    
    # Pattern: MM/DD-MM/DD (1 or 2 digits for month/day)
    pattern = r'^\d{1,2}/\d{1,2}-\d{1,2}/\d{1,2}$'
    return bool(re.match(pattern, week_of))


def parse_week_dates(week_of: str) -> Optional[tuple[str, str, str, str]]:
    """
    Parse week date string into components.
    
    Args:
        week_of: Week date string in MM/DD-MM/DD format
        
    Returns:
        Tuple of (start_month, start_day, end_month, end_day) or None if invalid
        
    Examples:
        >>> parse_week_dates("10/27-10/31")
        ('10', '27', '10', '31')
        >>> parse_week_dates("invalid")
        None
    """
    if not validate_week_format(week_of):
        return None
    
    # Split on hyphen to get start and end
    parts = week_of.split("-")
    if len(parts) != 2:
        return None
    
    # Split each part on slash
    start_parts = parts[0].split("/")
    end_parts = parts[1].split("/")
    
    if len(start_parts) != 2 or len(end_parts) != 2:
        return None
    
    return (start_parts[0], start_parts[1], end_parts[0], end_parts[1])

"""
Date formatting utilities for lesson plan processing.

Standardizes week date formats to MM/DD-MM/DD for consistency.
"""

import re
from datetime import datetime, timedelta
from typing import Optional


def _parse_week_of_to_ints(week_of: str) -> Optional[tuple[int, int, int, int]]:
    """
    Parse week_of to (m1, d1, m2, d2) for start and end month/day.
    Handles both MM-DD-MM-DD and MM/DD-MM/DD formats.
    Returns None if parsing fails.
    """
    if not week_of or not isinstance(week_of, str):
        return None
    cleaned = week_of.replace("Week of", "").replace("week of", "").strip()
    parts = cleaned.split("-")
    if len(parts) == 4 and all(p.isdigit() for p in parts):
        try:
            return (int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]))
        except ValueError:
            pass
    if len(parts) == 2:
        try:
            start = parts[0].strip().split("/")
            end = parts[1].strip().split("/")
            if len(start) == 2 and len(end) == 2 and all(x.isdigit() for x in start + end):
                return (int(start[0]), int(start[1]), int(end[0]), int(end[1]))
        except ValueError:
            pass
    matches = re.findall(r"(\d{1,2})[/-](\d{1,2})", cleaned.replace("to", "-"))
    if len(matches) >= 2:
        try:
            m1, d1 = int(matches[0][0]), int(matches[0][1])
            m2, d2 = int(matches[1][0]), int(matches[1][1])
            return (m1, d1, m2, d2)
        except ValueError:
            pass
    return None


def normalize_week_of_canonical(week_of: str) -> str:
    """
    Normalize week_of to zero-padded canonical form MM/DD-MM/DD.
    Accepts MM-DD-MM-DD and MM/DD-MM/DD. Raises ValueError if unparseable or invalid.

    Args:
        week_of: Week date string in various formats.

    Returns:
        Zero-padded canonical form, e.g. "03/16-03/20".

    Raises:
        ValueError: If week_of is empty, unparseable, or has invalid month/day.
    """
    if not week_of or not isinstance(week_of, str):
        raise ValueError("week_of must be a non-empty string")
    parsed = _parse_week_of_to_ints(week_of.strip())
    if parsed is None:
        raise ValueError(f"Invalid week_of format: {week_of!r}")
    m1, d1, m2, d2 = parsed
    if not (1 <= m1 <= 12 and 1 <= m2 <= 12 and 1 <= d1 <= 31 and 1 <= d2 <= 31):
        raise ValueError(f"Invalid month/day in week_of: {week_of!r}")
    return f"{m1:02d}/{d1:02d}-{m2:02d}/{d2:02d}"


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
        # Found start and end dates; zero-pad month and day to two digits
        start_month, start_day = int(matches[0][0]), int(matches[0][1])
        end_month, end_day = int(matches[1][0]), int(matches[1][1])
        return f"{start_month:02d}/{start_day:02d}-{end_month:02d}/{end_day:02d}"

    elif len(matches) == 1:
        # Only start date found - assume 5-day week (Monday-Friday)
        start_month, start_day = int(matches[0][0]), int(matches[0][1])
        end_day_int = start_day + 4
        if end_day_int <= 31:
            return f"{start_month:02d}/{start_day:02d}-{start_month:02d}/{end_day_int:02d}"
        return f"{start_month:02d}/{start_day:02d}-{start_month:02d}/{start_day:02d}"

    # Fallback: try to parse "10-27-10-31" format (all hyphens, no year)
    parts = cleaned.split("-")
    if len(parts) == 4 and all(p.isdigit() for p in parts):
        m1, d1, m2, d2 = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
        return f"{m1:02d}/{d1:02d}-{m2:02d}/{d2:02d}"
    
    # Can't parse - return original
    return week_of


def parse_iso_year_week_string_to_hyphen_range(text: str) -> Optional[str]:
    """
    Parse a leading YY W## label (ISO-style week folders) into MM-DD-MM-DD (Monday-Friday).

    Examples: \"26 W13\", \"25W43\". Returns None if the pattern does not match or week is invalid.
    """
    if not text or not isinstance(text, str):
        return None
    iso_pattern = r"^(\d{2})\s*W\s*(\d{1,2})\b"
    match = re.search(iso_pattern, text.strip(), re.IGNORECASE)
    if not match:
        return None
    year_short, week_num = match.groups()
    year = 2000 + int(year_short)
    week = int(week_num)
    if week < 1 or week > 53:
        return None
    try:
        jan_4 = datetime(year, 1, 4)
        _, _, iso_weekday = jan_4.isocalendar()
        days_back_to_monday = iso_weekday - 1
        monday_week1 = jan_4 - timedelta(days=days_back_to_monday)
        monday = monday_week1 + timedelta(weeks=week - 1)
        friday = monday + timedelta(days=4)
        return (
            f"{monday.month:02d}-{monday.day:02d}-"
            f"{friday.month:02d}-{friday.day:02d}"
        )
    except (ValueError, OSError):
        return None


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


def normalize_week_of_for_match(week_of: str) -> str:
    """
    Return a canonical week_of string for matching (e.g. 03-02-03-06 and 03/02-03/06 match).
    Accepts YY W## folder labels via parse_iso_year_week_string_to_hyphen_range.
    Uses normalize_week_of_canonical when possible; falls back to format_week_dates for
    legacy inputs that canonical rejects. Returns "" if unparseable.
    """
    if not week_of or not isinstance(week_of, str):
        return ""
    stripped = week_of.strip()
    iso_range = parse_iso_year_week_string_to_hyphen_range(stripped)
    if iso_range:
        try:
            return normalize_week_of_canonical(iso_range)
        except ValueError:
            pass
    try:
        return normalize_week_of_canonical(stripped)
    except ValueError:
        fw = format_week_dates(stripped) or ""
        if not fw:
            return ""
        try:
            return normalize_week_of_canonical(fw)
        except ValueError:
            return fw


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

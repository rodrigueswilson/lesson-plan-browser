"""Font size calculation for objectives DOCX layout."""

import re
from datetime import datetime, timedelta
from typing import Optional

from .extraction import DAY_NAMES


def calculate_font_size(
    text: str,
    available_width: float,
    available_height: float,
    base_font_size: int,
    min_font_size: int,
    max_font_size: int,
) -> int:
    """
    Calculate optimal font size to maximize text fill in available space.

    Uses iterative approach to find font size that fills target height (85%)
    while allowing text to wrap naturally within available width.

    Font metrics (Verdana Bold):
    - Average character width: ~0.6 * font_size (in points)
    - Line height with spacing: ~1.3 * font_size (in points)
    - Conversion: 72 points = 1 inch
    """
    if not text or not text.strip():
        return base_font_size

    lines = text.split("\n")
    max_line_length = max(len(line) for line in lines) if lines else 0

    if max_line_length == 0:
        return base_font_size

    CHAR_WIDTH_RATIO = 0.6
    LINE_HEIGHT_RATIO = 1.3

    height_target = available_height * 0.85

    text_without_newlines = text.replace("\n", " ")
    total_chars = len(text_without_newlines)
    existing_lines = len(lines)

    if total_chars == 0 or available_width <= 0 or available_height <= 0:
        return base_font_size

    if existing_lines > 1:
        font_size = (height_target * 72) / (existing_lines * LINE_HEIGHT_RATIO)
    else:
        numerator = height_target * available_width * 72 * 72
        denominator = total_chars * CHAR_WIDTH_RATIO * LINE_HEIGHT_RATIO

        if denominator > 0:
            font_size_squared = numerator / denominator
            font_size = font_size_squared**0.5
        else:
            font_size = base_font_size

        for _ in range(3):
            chars_per_line = (
                (available_width * 72) / (font_size * CHAR_WIDTH_RATIO)
                if font_size > 0
                else 1
            )
            estimated_wrapped_lines = max(1, (total_chars / chars_per_line) * 1.1)
            new_font_size = (height_target * 72) / (
                estimated_wrapped_lines * LINE_HEIGHT_RATIO
            )
            font_size = font_size * 0.6 + new_font_size * 0.4

    font_size = max(min_font_size, min(int(font_size), max_font_size))

    return font_size


def calculate_font_size_to_fill_height(
    text: str,
    available_width: float,
    target_height: float,
    min_font_size: int,
    max_font_size: int,
    char_width_ratio: float = 0.6,
    line_height_ratio: float = 1.3,
) -> int:
    """
    Calculate maximum font size that fits within target height.
    Uses conservative approach to ensure content definitely fits.
    """
    if not text or not text.strip() or target_height <= 0:
        return min_font_size

    text_without_newlines = text.replace("\n", " ")
    total_chars = len(text_without_newlines)
    words = text.split()

    if total_chars == 0 or available_width <= 0:
        return min_font_size

    safe_height = target_height * 0.70

    numerator = safe_height * available_width * 72 * 72
    denominator = total_chars * char_width_ratio * line_height_ratio

    if denominator > 0:
        font_size_squared = numerator / denominator
        font_size = font_size_squared**0.5

        for _ in range(5):
            chars_per_line = (
                (available_width * 72) / (font_size * char_width_ratio)
                if font_size > 0
                else 1
            )
            words_per_line = max(1, chars_per_line / 6)
            estimated_wrapped_lines = max(
                1, (len(words) / words_per_line) * 1.15
            )
            new_font_size = (safe_height * 72) / (
                estimated_wrapped_lines * line_height_ratio
            )
            font_size = font_size * 0.5 + new_font_size * 0.5
    else:
        font_size = min_font_size

    font_size = max(min_font_size, min(int(font_size), max_font_size))

    chars_per_line = (
        (available_width * 72) / (font_size * char_width_ratio)
        if font_size > 0
        else 1
    )
    words_per_line = max(1, chars_per_line / 6)
    final_estimated_lines = max(1, (len(words) / words_per_line) * 1.15)
    final_estimated_height = (
        font_size * line_height_ratio * final_estimated_lines
    ) / 72

    if final_estimated_height > target_height:
        reduction_factor = target_height / final_estimated_height * 0.85
        font_size = int(font_size * reduction_factor)
        font_size = max(min_font_size, min(font_size, max_font_size))

    return font_size


def parse_week_of_date(week_of: str) -> Optional[datetime]:
    """
    Parse week_of string to get Monday's date.

    Handles formats like:
    - "11/18/2024"
    - "Week of 11/18/2024"
    - "2024-11-18"
    - "10/06-10/10" (date range, use first date)
    - "11-17-11-21" (date range, use first date)
    """
    date_str = week_of.replace("Week of", "").strip()

    match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", date_str)
    if match:
        month, day, year = match.groups()
        try:
            return datetime(int(year), int(month), int(day))
        except ValueError:
            pass

    match = re.search(r"(\d{1,2})/(\d{1,2})-", date_str)
    if match:
        month, day = match.groups()
        current_year = datetime.now().year
        try:
            parsed_date = datetime(current_year, int(month), int(day))
            if parsed_date > datetime.now():
                parsed_date = datetime(current_year - 1, int(month), int(day))
            return parsed_date
        except ValueError:
            pass

    match = re.search(r"(\d{1,2})-(\d{1,2})-", date_str)
    if match:
        month, day = match.groups()
        current_year = datetime.now().year
        try:
            parsed_date = datetime(current_year, int(month), int(day))
            if parsed_date > datetime.now():
                parsed_date = datetime(current_year - 1, int(month), int(day))
            return parsed_date
        except ValueError:
            pass

    match = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", date_str)
    if match:
        year, month, day = match.groups()
        try:
            return datetime(int(year), int(month), int(day))
        except ValueError:
            pass

    return None


def get_day_date(week_of: str, day_name: str) -> str:
    """
    Get the date for a specific day of the week.

    Args:
        week_of: Week identifier (e.g., "Week of 11/18/2024")
        day_name: Day name (e.g., "monday", "Tuesday")

    Returns:
        Formatted date string (MM/DD/YYYY) or week_of if parsing fails
    """
    monday_date = parse_week_of_date(week_of)
    if not monday_date:
        return week_of

    day_index = (
        DAY_NAMES.index(day_name.lower())
        if day_name.lower() in DAY_NAMES
        else 0
    )
    target_date = monday_date + timedelta(days=day_index)

    return target_date.strftime("%m/%d/%Y")

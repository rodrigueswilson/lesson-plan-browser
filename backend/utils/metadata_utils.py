"""
Metadata utility functions for consistent extraction across document generators.

This module provides standardized functions for extracting metadata fields
like teacher names, ensuring consistent behavior across all document generators.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from backend.config import settings


def get_teacher_name(
    metadata: Dict[str, Any],
    slot: Optional[Dict[str, Any]] = None,
    user_name: Optional[str] = None,
) -> str:
    """
    Get teacher name with consistent priority across all document generators.

    Priority order:
    1. user_name (if provided - highest priority, from API/user context)
    2. slot.primary_teacher_name (slot-specific full name)
    3. slot.teacher_name (slot-specific name, alternative field)
    4. metadata.primary_teacher_name (lesson-level full name)
    5. metadata.teacher_name (lesson-level name)
    6. Constructed from slot.primary_teacher_first_name + slot.primary_teacher_last_name
    7. Constructed from metadata.primary_teacher_first_name + metadata.primary_teacher_last_name
    8. "Unknown" (fallback)

    Args:
        metadata: Lesson-level metadata dictionary
        slot: Optional slot dictionary (for multi-slot lessons)
        user_name: Optional user name from API/user context (highest priority)

    Returns:
        Teacher name string, or "Unknown" if not found
    """
    # Priority 1: user_name (from API/user context)
    if user_name and user_name.strip():
        return user_name.strip()

    # Priority 2-3: Slot-specific teacher name
    if slot:
        # Try primary_teacher_name first (slot metadata model field)
        slot_primary = slot.get("primary_teacher_name")
        if slot_primary and slot_primary.strip():
            return slot_primary.strip()

        # Try teacher_name (alternative field name)
        slot_teacher = slot.get("teacher_name")
        if slot_teacher and slot_teacher.strip():
            return slot_teacher.strip()

        # Try constructing from first + last name
        slot_first = slot.get("primary_teacher_first_name", "").strip()
        slot_last = slot.get("primary_teacher_last_name", "").strip()
        if slot_first or slot_last:
            constructed = f"{slot_first} {slot_last}".strip()
            if constructed:
                return constructed

    # Priority 4-5: Lesson-level teacher name
    # CRITICAL: Check teacher_name (combined format "Primary / Bilingual") BEFORE primary_teacher_name
    # This ensures we show "Kelsey Lang / Wilson Rodrigues" instead of just "Kelsey Lang"
    lesson_teacher = metadata.get("teacher_name")
    if lesson_teacher and lesson_teacher.strip():
        return lesson_teacher.strip()
    
    lesson_primary = metadata.get("primary_teacher_name")
    if lesson_primary and lesson_primary.strip():
        return lesson_primary.strip()

    # Priority 6-7: Constructed from lesson-level first + last name
    lesson_first = metadata.get("primary_teacher_first_name", "").strip()
    lesson_last = metadata.get("primary_teacher_last_name", "").strip()
    if lesson_first or lesson_last:
        constructed = f"{lesson_first} {lesson_last}".strip()
        if constructed:
            return constructed

    # Priority 8: Fallback
    return "Unknown"


def get_subject(
    metadata: Dict[str, Any],
    slot: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Get subject with consistent priority across all document generators.

    Priority order:
    1. slot.subject (slot-specific subject, if provided)
    2. metadata.subject (lesson-level subject)
    3. "Unknown" (fallback)

    Note: This function does NOT use text detection from unit_lesson as it is unreliable.
    Subject should always come from metadata.

    Args:
        metadata: Lesson-level metadata dictionary
        slot: Optional slot dictionary (for multi-slot lessons)

    Returns:
        Subject string, or "Unknown" if not found
    """
    # Priority 1: Slot-specific subject
    if slot:
        slot_subject = slot.get("subject")
        if slot_subject and slot_subject.strip() and slot_subject != "Unknown":
            return slot_subject.strip()

    # Priority 2: Lesson-level subject
    lesson_subject = metadata.get("subject")
    if lesson_subject and lesson_subject.strip() and lesson_subject != "Unknown":
        return lesson_subject.strip()

    # Priority 3: Fallback
    return "Unknown"


def get_homeroom(
    metadata: Dict[str, Any],
    slot: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Get homeroom with consistent priority and leakage prevention.

    This function prevents homeroom from leaking between slots in multi-slot lessons.

    Priority order:
    1. slot.homeroom (if key exists in slot, even if empty/None/"N/A")
    2. metadata.homeroom (lesson-level homeroom, only if slot doesn't have homeroom key)
    3. "Unknown" (fallback)

    Key principle: If a slot explicitly has a homeroom field (even if empty),
    use that value. Only use lesson-level homeroom if the slot doesn't have
    the homeroom key at all. This prevents Math slot's homeroom from being
    used for Science slot.

    Args:
        metadata: Lesson-level metadata dictionary
        slot: Optional slot dictionary (for multi-slot lessons)

    Returns:
        Homeroom string, or "Unknown" if not found
    """
    # Priority 1: Slot-specific homeroom (if key exists)
    if slot is not None:
        # Check if slot has homeroom key (even if value is None/empty)
        if "homeroom" in slot:
            slot_homeroom = slot.get("homeroom")
            # If slot explicitly has homeroom (even if empty/None/"N/A"), use it
            # This prevents using another slot's homeroom
            if slot_homeroom is None:
                return "Unknown"
            slot_homeroom_str = str(slot_homeroom).strip()
            if slot_homeroom_str and slot_homeroom_str != "N/A":
                return slot_homeroom_str
            # If slot has homeroom but it's empty/"N/A", return "Unknown"
            # Don't fall back to lesson-level (might be from another slot)
            return "Unknown"

    # Priority 2: Lesson-level homeroom (only if slot doesn't have homeroom key)
    lesson_homeroom = metadata.get("homeroom")
    if lesson_homeroom:
        lesson_homeroom_str = str(lesson_homeroom).strip()
        if lesson_homeroom_str and lesson_homeroom_str != "N/A":
            return lesson_homeroom_str

    # Priority 3: Fallback
    return "Unknown"


def build_document_header(
    metadata: Dict[str, Any],
    slot: Optional[Dict[str, Any]] = None,
    day_date: Optional[str] = None,
    day_name: Optional[str] = None,
    include_time: bool = False,
    include_day_name: bool = True,
) -> str:
    """
    Build a standardized document header string for lesson plan documents.

    Standard header format:
    Date | Day | Subject | Grade | Homeroom | Room

    Optional fields:
    - Time: Only included if include_time=True and slot has time
    - Day name: Only included if include_day_name=True

    This function ensures consistent header formatting across all document generators
    (Objectives PDF, Sentence Frames PDF, DOCX).

    Args:
        metadata: Lesson-level metadata dictionary
        slot: Optional slot dictionary (for multi-slot lessons)
        day_date: Optional formatted date string (MM/DD/YYYY or MM/DD/YY).
                  If not provided, will attempt to calculate from week_of and day_name.
        day_name: Optional day name (e.g., "Monday", "Wednesday").
                  Used for date calculation if day_date not provided.
        include_time: If True, include time field from slot (default: False)
        include_day_name: If True, include day name in header (default: True)

    Returns:
        Formatted header string with fields separated by " | "
    """
    parts: List[str] = []

    # 1. Date (required)
    if day_date:
        parts.append(day_date)
    elif day_name and metadata.get("week_of"):
        # Calculate date if not provided
        config_school_year = None
        if settings.SCHOOL_YEAR_START_YEAR and settings.SCHOOL_YEAR_END_YEAR:
            config_school_year = (
                settings.SCHOOL_YEAR_START_YEAR,
                settings.SCHOOL_YEAR_END_YEAR,
            )
        calculated_date = get_day_date(
            metadata["week_of"], day_name, config_school_year=config_school_year
        )
        if calculated_date and calculated_date != metadata.get("week_of"):
            parts.append(calculated_date)
        else:
            parts.append(metadata.get("week_of", "Unknown"))
    else:
        parts.append(metadata.get("week_of", "Unknown"))

    # 2. Day name (optional, default: True)
    if include_day_name and day_name:
        day_display = (
            day_name.capitalize() if isinstance(day_name, str) else str(day_name)
        )
        parts.append(day_display)

    # 3. Time (optional, only if include_time=True and slot has time)
    if include_time and slot:
        time = slot.get("time", "")
        if time and time.strip() and time != "N/A":
            parts.append(time)

    # 4. Subject (required)
    subject = get_subject(metadata, slot=slot)
    if subject and subject != "Unknown":
        # Handle multiple subjects separated by " / " - take first
        if " / " in subject:
            subject = subject.split(" / ")[0].strip()
        parts.append(subject)
    else:
        parts.append("Unknown")

    # 5. Grade (if not Unknown)
    grade = None
    if slot:
        grade = slot.get("grade")
    if not grade or grade == "N/A":
        grade = metadata.get("grade")
    if grade and grade != "Unknown" and grade != "N/A":
        parts.append(f"Grade {grade}")

    # 6. Homeroom (if not Unknown)
    homeroom = get_homeroom(metadata, slot=slot)
    if homeroom and homeroom != "Unknown":
        parts.append(homeroom)

    # 7. Room (if present)
    room = None
    if slot:
        room = slot.get("room")
    if not room or room == "N/A" or (isinstance(room, str) and not room.strip()):
        room = metadata.get("room", "")
    if room and room.strip() and room != "N/A" and room != "Unknown":
        parts.append(f"Room {room}")

    return " | ".join(parts)


def infer_school_year_from_date(
    month: int, day: int, year: Optional[int] = None
) -> tuple[int, int]:
    """
    Infer school year (start_year, end_year) from a date.

    School year typically runs August-June:
    - August-December: Start of school year (e.g., Aug 2025 = SY 2025-2026)
    - January-June: End of school year (e.g., Jan 2026 = SY 2025-2026)

    Args:
        month: Month (1-12)
        day: Day (1-31)
        year: Optional year. If not provided, uses current year.

    Returns:
        Tuple of (start_year, end_year) for the school year
        Example: (2025, 2026) for SY 2025-2026
    """
    if year is None:
        year = datetime.now().year

    # If month is August-December (8-12), it's the start of the school year
    if month >= 8:
        return (year, year + 1)
    # If month is January-June (1-6), it's the end of the school year
    elif month <= 6:
        return (year - 1, year)
    # July (7) is ambiguous - assume it's end of previous school year
    else:
        return (year - 1, year)


def parse_week_of_date(week_of: str) -> Optional[tuple[int, int, Optional[int]]]:
    """
    Parse week_of string to extract month, day, and optionally year.

    Handles formats:
    - "11/17-11/21" -> (11, 17, None)
    - "11-17-11-21" -> (11, 17, None)
    - "11/17/2025-11/21/2025" -> (11, 17, 2025)
    - "11-17-2025 to 11-21-2025" -> (11, 17, 2025)

    Args:
        week_of: Week date string

    Returns:
        Tuple of (month, day, year) where year is None if not found, or None if unparseable
    """
    if not week_of:
        return None

    # Try to extract year first (4-digit year)
    year_match = re.search(r"(\d{4})", week_of)
    year = int(year_match.group(1)) if year_match else None

    # Parse first date (Monday's date)
    # Try slash format: "11/17" or "11/17/2025"
    match = re.search(r"(\d{1,2})/(\d{1,2})(?:/(\d{4}))?", week_of)
    if match:
        month, day, year_in_date = match.groups()
        if year_in_date:
            year = int(year_in_date)
        return (int(month), int(day), year)

    # Try dash format: "11-17" or "11-17-2025"
    match = re.search(r"(\d{1,2})-(\d{1,2})(?:-(\d{4}))?", week_of)
    if match:
        month, day, year_in_date = match.groups()
        if year_in_date:
            year = int(year_in_date)
        return (int(month), int(day), year)

    return None


def get_day_date(
    week_of: str,
    day_name: str,
    school_year: Optional[tuple[int, int]] = None,
    config_school_year: Optional[tuple[int, int]] = None,
) -> str:
    """
    Calculate the specific date for a given day in the week.

    This function provides consistent date calculation across all document generators.
    It infers the school year from the week_of date if not provided.

    Priority for school year:
    1. school_year parameter (explicitly provided)
    2. config_school_year parameter (from user configuration)
    3. Inferred from date in week_of

    Args:
        week_of: Week range string like "11/17-11/21" or "11/17/2025-11/21/2025"
        day_name: Day name like "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"
        school_year: Optional tuple of (start_year, end_year) for school year.
                     If not provided, will use config or infer from date.
                     Example: (2025, 2026) for SY 2025-2026
        config_school_year: Optional tuple from user configuration.
                            Example: (2025, 2026) for SY 2025-2026

    Returns:
        Formatted date string "MM/DD/YYYY" (e.g., "11/17/2025")
        Returns week_of if parsing fails
    """
    # Parse week_of to get Monday's date
    parsed = parse_week_of_date(week_of)
    if not parsed:
        return week_of

    month, day, year = parsed

    # Day name to offset mapping
    day_offsets = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
    }

    # Normalize day name
    normalized_day = day_name.lower().strip()
    offset = day_offsets.get(normalized_day, 0)

    try:
        # Determine school year to use (priority: parameter > config > inferred)
        if school_year:
            start_year, end_year = school_year
        elif config_school_year:
            start_year, end_year = config_school_year
        else:
            # Infer school year from date
            start_year, end_year = infer_school_year_from_date(month, day, year)

        # If year is explicitly in week_of, use it
        if year:
            monday_date = datetime(year, month, day)
        else:
            # Determine which year based on month
            # August-December: use start_year
            # January-June: use end_year
            if month >= 8:
                inferred_year = start_year
            elif month <= 6:
                inferred_year = end_year
            else:  # July - use start_year
                inferred_year = start_year

            monday_date = datetime(inferred_year, month, day)

            # Sanity check: if date is more than 1 year in the future, adjust
            # This handles cases where we're in late 2024 but processing 2025-2026 school year
            current_date = datetime.now()
            if monday_date > current_date + timedelta(days=365):
                # Too far in future, probably wrong year - adjust
                monday_date = datetime(inferred_year - 1, month, day)
            elif monday_date < current_date - timedelta(days=365):
                # Too far in past, probably wrong year - adjust
                monday_date = datetime(inferred_year + 1, month, day)

        # Calculate target date (Monday + offset)
        target_date = monday_date + timedelta(days=offset)

        # Format as MM/DD/YYYY
        return target_date.strftime("%m/%d/%Y")

    except (ValueError, OverflowError):
        # Invalid date (e.g., Feb 30)
        return week_of

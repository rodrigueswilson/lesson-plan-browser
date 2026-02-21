"""
Pure helper functions for batch processor (teacher name, week number, no-school stub).
"""

from datetime import datetime
from typing import Any, Dict

from backend.telemetry import logger


def build_teacher_name(user: Dict[str, Any], slot: Dict[str, Any]) -> str:
    """
    Build teacher name as "Primary First Last / Bilingual First Last".

    Fallback strategy:
    1. Try structured first/last names
    2. Fall back to legacy 'name' and 'primary_teacher_name' fields
    3. Return "Unknown" if all fail

    Args:
        user: User dictionary from database
        slot: Slot dictionary from database

    Returns:
        Formatted teacher name string
    """
    # Primary teacher name - normalize None to empty string before strip
    primary_first = (slot.get("primary_teacher_first_name") or "").strip()
    primary_last = (slot.get("primary_teacher_last_name") or "").strip()

    if primary_first and primary_last:
        primary_name = f"{primary_first} {primary_last}"
    elif primary_first or primary_last:
        primary_name = primary_first or primary_last
    else:
        primary_name = (slot.get("primary_teacher_name") or "").strip()

    # Bilingual teacher name - normalize None to empty string before strip
    bilingual_first = (user.get("first_name") or "").strip()
    bilingual_last = (user.get("last_name") or "").strip()

    if bilingual_first and bilingual_last:
        bilingual_name = f"{bilingual_first} {bilingual_last}"
    elif bilingual_first or bilingual_last:
        bilingual_name = bilingual_first or bilingual_last
    else:
        bilingual_name = (user.get("name") or "").strip()

    if primary_name and bilingual_name:
        return f"{primary_name} / {bilingual_name}"
    elif primary_name:
        return primary_name
    elif bilingual_name:
        return bilingual_name
    else:
        return "Unknown"


def no_school_day_stub() -> Dict[str, Any]:
    """Return the minimal day structure for a No School day (shared by sequential and parallel paths)."""
    return {
        "unit_lesson": "No School",
        "objective": {
            "content_objective": "No School",
            "student_goal": "No School",
            "wida_objective": "No School",
        },
        "anticipatory_set": {
            "original_content": "",
            "bilingual_bridge": "",
        },
        "tailored_instruction": {
            "original_content": "",
            "co_teaching_model": {},
            "ell_support": [],
            "special_needs_support": [],
            "materials": [],
        },
        "misconceptions": {
            "original_content": "",
            "linguistic_note": {},
        },
        "assessment": {
            "primary_assessment": "",
            "bilingual_overlay": {},
        },
        "homework": {
            "original_content": "",
            "family_connection": "",
        },
    }


def get_week_num(week_of: str) -> int:
    """Extract week number from week_of string.

    Supports formats:
    - MM/DD-MM/DD (e.g., 10/13-10/17)
    - MM-DD-MM-DD (e.g., 10-13-10-17)
    """
    try:
        if "/" in week_of:
            first_date = week_of.split("-")[0].strip()
            month, day = map(int, first_date.split("/"))
        else:
            parts = week_of.split("-")
            if len(parts) >= 2:
                month, day = int(parts[0]), int(parts[1])
            else:
                raise ValueError(f"Invalid week_of format: {week_of}")

        year = datetime.now().year
        date_obj = datetime(year, month, day)
        week_num = date_obj.isocalendar()[1]
        logger.debug(
            "week_number_calculated",
            extra={
                "week_of": week_of,
                "month": month,
                "day": day,
                "year": year,
                "week_number": week_num,
            },
        )
        return week_num
    except Exception as e:
        logger.warning(
            "week_number_calculation_failed",
            extra={"week_of": week_of, "error": str(e)},
        )
        return 1


def calculate_week_number(week_of: str) -> int:
    """Calculate week number from date range.

    Args:
        week_of: Week date range (MM/DD-MM/DD)

    Returns:
        Week number (1-52)
    """
    try:
        first_date = week_of.split("-")[0].strip()
        month, day = map(int, first_date.split("/"))
        if month >= 9:
            week_num = (month - 9) * 4 + (day // 7) + 1
        else:
            week_num = (month + 3) * 4 + (day // 7) + 1
        return min(week_num, 52)
    except Exception:
        return 1

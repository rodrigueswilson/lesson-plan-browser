"""
No-school day/week JSON builders for slot flow.
"""

from copy import deepcopy
from typing import Any, Dict, List

from tools.batch_processor_pkg.helpers import no_school_day_stub


def build_no_school_day_json(
    week_of: str, slot: dict, hyperlinks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Build minimal lesson JSON for no-school day (entire document)."""
    stub = no_school_day_stub()
    no_school_json = {
        "metadata": {
            "week_of": week_of,
            "grade": slot["grade"],
            "subject": slot["subject"],
            "homeroom": slot.get("homeroom"),
            "no_school": True,
        },
        "days": {
            day: deepcopy(stub)
            for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]
        },
    }
    if hyperlinks:
        no_school_json["_hyperlinks"] = hyperlinks
        no_school_json["_media_schema_version"] = "2.0"
    return no_school_json


def build_no_school_week_json(processor: Any, slot: dict, week_of: str) -> Dict[str, Any]:
    """Build minimal lesson JSON for no-school week (entire document)."""
    user_dict = {
        "first_name": processor._user_first_name,
        "last_name": processor._user_last_name,
        "name": processor._user_name,
    }
    return {
        "metadata": {
            "teacher_name": processor._build_teacher_name(user_dict, slot),
            "grade": slot.get("grade", ""),
            "subject": slot["subject"],
            "week_of": week_of,
            "homeroom": slot.get("homeroom", ""),
            "slot_number": slot["slot_number"],
        },
        "days": {
            day: {"unit_lesson": "No School"}
            for day in [
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
            ]
        },
        "_images": [],
        "_hyperlinks": [],
    }

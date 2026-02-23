"""
No-school day/week JSON builders for slot flow.
"""

from typing import Any, Dict, List


def build_no_school_day_json(
    week_of: str, slot: dict, hyperlinks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Build minimal lesson JSON for no-school day (entire document)."""
    no_school_json = {
        "metadata": {
            "week_of": week_of,
            "grade": slot["grade"],
            "subject": slot["subject"],
            "homeroom": slot.get("homeroom"),
            "no_school": True,
        },
        "days": {
            day: {
                "unit_lesson": "No School",
                "objective": {
                    "content_objective": "No School",
                    "student_goal": "No School",
                    "wida_objective": "No School",
                },
                "anticipatory_set": {
                    "original_content": "No School",
                    "bilingual_bridge": "",
                },
                "tailored_instruction": {
                    "original_content": "No School",
                    "co_teaching_model": {},
                    "ell_support": [],
                    "special_needs_support": [],
                    "materials": [],
                },
                "misconceptions": {
                    "original_content": "No School",
                    "linguistic_note": {},
                },
                "assessment": {
                    "primary_assessment": "No School",
                    "bilingual_overlay": {},
                },
                "homework": {
                    "original_content": "No School",
                    "family_connection": "",
                },
            }
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

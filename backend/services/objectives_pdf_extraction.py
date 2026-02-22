"""
Extract objective records from lesson JSON (day and slot structures).

Extracted from objectives_pdf_generator to keep the generator slim.
"""

from __future__ import annotations

from typing import Any, Dict, List

from backend.services.objectives_utils import normalize_objective_payload
from backend.telemetry import logger
from backend.utils.metadata_utils import get_homeroom, get_subject, get_teacher_name


def extract_from_slot(
    slot: Dict[str, Any],
    day_name: str,
    week_of: str,
    grade: str,
    homeroom: str,
    room: str,
    teacher_name: str,
    objectives: List[Dict[str, Any]],
    metadata: Dict[str, Any],
) -> None:
    """Extract objectives from a slot (multi-slot structure).

    Prioritizes slot-specific metadata over merged metadata.
    """
    unit_lesson = slot.get("unit_lesson", "")
    slot_teacher = get_teacher_name(metadata, slot=slot)

    slot_grade = slot.get("grade", grade)
    slot_homeroom = get_homeroom(metadata, slot=slot)
    slot_room = slot.get("room", room)
    slot_time = slot.get("time", "")

    detected_subject = get_subject(metadata, slot=slot)

    slot_num = slot.get("slot_number", 0)
    objective_data = normalize_objective_payload(
        slot.get("objective", {}),
        {
            "day": day_name,
            "slot_number": slot_num,
            "subject": detected_subject,
        },
    )
    if not objective_data:
        logger.debug(
            f"Slot {slot_num} ({day_name}) has no objective data - including with empty objectives"
        )
        objective_data = {
            "content_objective": "",
            "student_goal": "",
            "wida_objective": "",
        }

    if unit_lesson and unit_lesson.strip().lower() == "no school":
        return

    content_obj = objective_data.get("content_objective", "").strip().lower()
    student_goal = objective_data.get("student_goal", "").strip().lower()
    wida_obj = objective_data.get("wida_objective", "").strip().lower()

    if (
        content_obj == "no school"
        and student_goal == "no school"
        and wida_obj == "no school"
    ):
        return

    objectives.append(
        {
            "week_of": week_of,
            "day": day_name.capitalize(),
            "subject": detected_subject,
            "grade": slot_grade if slot_grade and slot_grade != "N/A" else grade,
            "homeroom": slot_homeroom,
            "room": slot_room if slot_room and slot_room != "N/A" else room,
            "time": slot_time if slot_time and slot_time != "N/A" else "",
            "teacher_name": slot_teacher,
            "slot_number": slot.get("slot_number", 0),
            "unit_lesson": unit_lesson,
            "content_objective": objective_data.get("content_objective", ""),
            "student_goal": objective_data.get("student_goal", ""),
            "wida_objective": objective_data.get("wida_objective", ""),
        }
    )


def extract_from_day(
    day_data: Dict[str, Any],
    day_name: str,
    week_of: str,
    grade: str,
    homeroom: str,
    room: str,
    metadata: Dict[str, Any],
    subject: str,
    objectives: List[Dict[str, Any]],
) -> None:
    """Extract objectives from a day (single-slot structure)."""
    objective_data = normalize_objective_payload(
        day_data.get("objective", {}),
        {
            "day": day_name,
            "subject": subject,
        },
    )
    if not objective_data:
        return

    unit_lesson = day_data.get("unit_lesson", "")

    if unit_lesson and unit_lesson.strip().lower() == "no school":
        return

    content_obj = objective_data.get("content_objective", "").strip().lower()
    student_goal = objective_data.get("student_goal", "").strip().lower()
    wida_obj = objective_data.get("wida_objective", "").strip().lower()

    if (
        content_obj == "no school"
        and student_goal == "no school"
        and wida_obj == "no school"
    ):
        return

    detected_subject = get_subject(metadata)

    objectives.append(
        {
            "week_of": week_of,
            "day": day_name.capitalize(),
            "subject": detected_subject,
            "grade": grade,
            "homeroom": get_homeroom(metadata),
            "room": room if room and room != "N/A" else "",
            "teacher_name": get_teacher_name(metadata),
            "unit_lesson": unit_lesson,
            "content_objective": objective_data.get("content_objective", ""),
            "student_goal": objective_data.get("student_goal", ""),
            "wida_objective": objective_data.get("wida_objective", ""),
        }
    )

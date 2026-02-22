"""Extract objectives from lesson plan JSON."""

from typing import Any, Dict, List

from backend.services.objectives_utils import normalize_objective_payload
from backend.services.sorting_utils import sort_slots
from backend.telemetry import logger

from .subject_parsing import extract_subject_from_unit_lesson


DAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday"]


def extract_objectives(lesson_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract all objectives from lesson plan.

    Returns:
        List of objective dictionaries with day, slot, and objective data
    """
    objectives = []

    if "days" not in lesson_json:
        logger.warning("No 'days' key found in lesson_json")
        return objectives

    metadata = lesson_json.get("metadata", {})
    week_of = metadata.get("week_of", "Unknown")
    grade = metadata.get("grade", "Unknown")
    subject = metadata.get("subject", "Unknown")

    days = lesson_json["days"]

    for day_name in DAY_NAMES:
        if day_name not in days:
            continue

        day_data = days[day_name]
        slots = day_data.get("slots", [])

        sorted_slots = sort_slots(slots)

        for slot in sorted_slots:
            slot_number = slot.get("slot_number", 0)
            slot_subject = slot.get("subject", subject)
            unit_lesson = slot.get("unit_lesson", "")
            teacher_name = slot.get("teacher_name", "")

            if unit_lesson and unit_lesson.strip().lower() == "no school":
                continue

            objective_data = normalize_objective_payload(
                slot.get("objective", {}),
                {
                    "day": day_name,
                    "slot_number": slot_number,
                    "subject": slot_subject,
                },
            )

            if not objective_data:
                continue

            content_obj = (
                objective_data.get("content_objective", "").strip().lower()
            )
            student_goal = objective_data.get("student_goal", "").strip().lower()
            wida_obj = objective_data.get("wida_objective", "").strip().lower()

            if (
                content_obj == "no school"
                and student_goal == "no school"
                and wida_obj == "no school"
            ):
                continue

            final_subject = slot_subject

            if final_subject in ["Unknown", ""]:
                detected_subject = extract_subject_from_unit_lesson(unit_lesson)
                if detected_subject != "Unknown":
                    final_subject = detected_subject
                elif unit_lesson and unit_lesson.strip():
                    final_subject = subject
                else:
                    final_subject = "Unknown"

            objectives.append(
                {
                    "week_of": week_of,
                    "day": day_name.capitalize(),
                    "slot_number": slot_number,
                    "subject": final_subject,
                    "unit_lesson": unit_lesson,
                    "teacher_name": teacher_name,
                    "content_objective": objective_data.get(
                        "content_objective", ""
                    ),
                    "student_goal": objective_data.get("student_goal", ""),
                    "wida_objective": objective_data.get("wida_objective", ""),
                }
            )

    return objectives

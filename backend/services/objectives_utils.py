"""
Utility helpers for validating and normalizing objective data structures.
"""

from typing import Any, Dict, Optional

from pydantic import ValidationError

from backend.models_slot import ObjectiveData
from backend.telemetry import logger


def normalize_objective_payload(
    objective_payload: Dict[str, Any],
    log_context: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, str]]:
    """
    Validate and normalize the tri-objective payload.

    Args:
        objective_payload: Raw objective dictionary from lesson JSON.
        log_context: Optional metadata for telemetry (day, slot, subject, etc.).

    Returns:
        Dict with normalized objective fields, or None if payload is empty.
    """
    if not objective_payload:
        return None

    try:
        model = ObjectiveData.model_validate(objective_payload)
        return model.model_dump()
    except ValidationError as exc:
        context = {"objective_source": "lesson_json"}
        if log_context:
            context.update(log_context)
        context["validation_errors"] = exc.errors()
        logger.warning("objective_validation_failed", extra=context)

        fallback = {
            "content_objective": str(objective_payload.get("content_objective", "")).strip(),
            "student_goal": str(objective_payload.get("student_goal", "")).strip(),
            "wida_objective": str(objective_payload.get("wida_objective", "")).strip(),
        }

        if not any(fallback.values()):
            return None

        return fallback


def normalize_objectives_in_lesson(lesson_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize every objective structure inside a lesson JSON.

    Args:
        lesson_json: Lesson JSON payload to sanitize in-place.

    Returns:
        The same lesson_json dict for convenience.
    """
    days = lesson_json.get("days")
    if not isinstance(days, dict):
        return lesson_json

    for day_name, day_data in days.items():
        if not isinstance(day_data, dict):
            continue

        slots = day_data.get("slots")
        if isinstance(slots, list):
            for slot in slots:
                if not isinstance(slot, dict):
                    continue
                normalized = normalize_objective_payload(
                    slot.get("objective", {}),
                    {
                        "day": day_name,
                        "slot_number": slot.get("slot_number"),
                        "subject": slot.get("subject"),
                    },
                )
                if normalized is not None:
                    slot["objective"] = normalized
                elif "objective" in slot:
                    slot["objective"] = {}
        else:
            normalized = normalize_objective_payload(
                day_data.get("objective", {}),
                {"day": day_name, "subject": day_data.get("subject")},
            )
            if normalized is not None:
                day_data["objective"] = normalized
            elif "objective" in day_data:
                day_data["objective"] = {}

    return lesson_json


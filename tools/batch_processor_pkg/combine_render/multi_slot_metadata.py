"""
Apply slot_data (teacher names) to lesson_json metadata for multi-slot render.
"""

from typing import Any, Dict


def apply_slot_metadata_to_lesson(
    lesson_json: Dict[str, Any],
    slot_data: Any,
    processor: Any,
) -> None:
    """Set primary_teacher_* and teacher_name on lesson_json metadata from slot_data."""
    if not slot_data:
        return
    if isinstance(slot_data, dict):
        primary_teacher_name = slot_data.get("primary_teacher_name")
        primary_teacher_first_name = slot_data.get("primary_teacher_first_name")
        primary_teacher_last_name = slot_data.get("primary_teacher_last_name")
        lesson_json["metadata"]["primary_teacher_name"] = primary_teacher_name
        lesson_json["metadata"]["primary_teacher_first_name"] = primary_teacher_first_name
        lesson_json["metadata"]["primary_teacher_last_name"] = primary_teacher_last_name
    else:
        primary_teacher_name = getattr(slot_data, "primary_teacher_name", None)
        primary_teacher_first_name = getattr(
            slot_data, "primary_teacher_first_name", None
        )
        primary_teacher_last_name = getattr(
            slot_data, "primary_teacher_last_name", None
        )
        lesson_json["metadata"]["primary_teacher_name"] = primary_teacher_name
        lesson_json["metadata"]["primary_teacher_first_name"] = primary_teacher_first_name
        lesson_json["metadata"]["primary_teacher_last_name"] = primary_teacher_last_name

    try:
        combined_teacher_name = processor._build_teacher_name(
            {
                "first_name": getattr(processor, "_user_first_name", ""),
                "last_name": getattr(processor, "_user_last_name", ""),
                "name": getattr(processor, "_user_name", ""),
            },
            slot_data
            if isinstance(slot_data, dict)
            else {
                "primary_teacher_name": primary_teacher_name,
                "primary_teacher_first_name": primary_teacher_first_name,
                "primary_teacher_last_name": primary_teacher_last_name,
            },
        )
        lesson_json["metadata"]["teacher_name"] = combined_teacher_name
    except Exception:
        primary_teacher_name = (
            slot_data.get("primary_teacher_name")
            if isinstance(slot_data, dict)
            else getattr(slot_data, "primary_teacher_name", None)
        )
        lesson_json["metadata"]["teacher_name"] = (
            primary_teacher_name or "Unknown"
        )

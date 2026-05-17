"""
Merge lessons with existing (if partial/missing_only) and render combined DOCX.
"""
import asyncio
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.progress import progress_tracker
from backend.telemetry import logger
from tools.batch_processor_pkg.combine_render.multi_slot_metadata import (
    apply_slot_metadata_to_lesson,
)


async def merge_and_render(
    processor: Any,
    user: Dict[str, Any],
    lessons: List[Dict],
    existing_lesson_json: Optional[Dict],
    partial: bool,
    missing_only: bool,
    week_of: str,
    start_time: datetime,
    plan_id: Optional[str],
    processing_weight: float,
    rendering_weight: float,
    errors: List[str],
) -> Optional[str]:
    """
    Merge lessons with existing slots if partial/missing_only; render combined DOCX.
    Appends to errors on combine failure. Returns output_file path or None.
    """
    all_lessons_for_rendering = lessons.copy()
    if (partial or missing_only) and existing_lesson_json:
        existing_slots_by_number = processor._reconstruct_slots_from_json(
            existing_lesson_json
        )
        combined_lessons_by_number = existing_slots_by_number
        for lesson in lessons:
            combined_lessons_by_number[lesson["slot_number"]] = lesson
        all_lessons_for_rendering = list(combined_lessons_by_number.values())
        all_lessons_for_rendering.sort(key=lambda x: x.get("slot_number", 0))

    await _refresh_lesson_metadata_from_current_slots(
        processor,
        user,
        all_lessons_for_rendering,
    )

    output_file = None
    rendering_progress = int(
        processing_weight * 100 + rendering_weight * 50
    )
    if all_lessons_for_rendering:
        try:
            progress_tracker.update(
                plan_id,
                "rendering",
                rendering_progress,
                f"Rendering {len(all_lessons_for_rendering)} lessons to DOCX...",
                metadata={
                    "completed_slots": len(lessons),
                    "total_slots": len(all_lessons_for_rendering),
                },
            )
            output_file = await asyncio.to_thread(
                processor._combine_lessons,
                user,
                all_lessons_for_rendering,
                week_of,
                start_time,
                plan_id,
            )
            progress_tracker.update(
                plan_id,
                "completed",
                100,
                f"Successfully created lesson plan with {len(all_lessons_for_rendering)} slots",
                metadata={
                    "completed_slots": len(all_lessons_for_rendering),
                    "total_slots": len(all_lessons_for_rendering),
                },
            )
            progress_tracker.complete(plan_id)
        except Exception as e:
            error_msg = f"Failed to combine lessons: {str(e)}"
            traceback.print_exc()
            errors.append(error_msg)
            progress_tracker.update(
                plan_id,
                "failed",
                rendering_progress,
                f"Failed to render: {str(e)}",
                metadata={
                    "completed_slots": len(lessons),
                    "total_slots": len(all_lessons_for_rendering),
                },
            )
    return output_file


async def _refresh_lesson_metadata_from_current_slots(
    processor: Any,
    user: Dict[str, Any],
    lessons: List[Dict],
) -> None:
    """Use current slot config as source of truth before rendering cached plans."""
    user_id = user.get("id") or user.get("user_id")
    if not user_id or not lessons:
        return

    try:
        db = processor.get_db(user_id=user_id)
        current_slots = await asyncio.to_thread(db.get_user_slots, user_id)
    except Exception:
        logger.warning(
            "refresh_lesson_metadata_slots_load_failed",
            extra={"user_id": user_id},
            exc_info=True,
        )
        return

    slots_by_number = {}
    for slot in current_slots or []:
        slot_dict = _slot_to_dict(slot)
        slot_number = slot_dict.get("slot_number")
        if slot_number is not None:
            slots_by_number[slot_number] = slot_dict

    for lesson in lessons:
        slot_number = lesson.get("slot_number")
        slot_data = slots_by_number.get(slot_number)
        lesson_json = lesson.get("lesson_json")
        if not slot_data or not isinstance(lesson_json, dict):
            continue

        lesson["slot_data"] = slot_data
        lesson["subject"] = slot_data.get("subject") or lesson.get("subject")
        apply_slot_metadata_to_lesson(lesson_json, slot_data, processor)


def _slot_to_dict(slot: Any) -> Dict[str, Any]:
    if isinstance(slot, dict):
        return dict(slot)
    if hasattr(slot, "model_dump"):
        return slot.model_dump(mode="python")
    if hasattr(slot, "dict"):
        return slot.dict()
    return {
        "slot_number": getattr(slot, "slot_number", None),
        "subject": getattr(slot, "subject", None),
        "primary_teacher_name": getattr(slot, "primary_teacher_name", None),
        "primary_teacher_first_name": getattr(
            slot,
            "primary_teacher_first_name",
            None,
        ),
        "primary_teacher_last_name": getattr(
            slot,
            "primary_teacher_last_name",
            None,
        ),
    }

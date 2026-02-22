"""
Sequential path for week-level batch processing: loop over slots, _process_slot, collect lessons and errors.
"""
import traceback
from typing import Any, Dict, List, Optional

from backend.progress import progress_tracker
from backend.telemetry import logger


async def run_sequential_path(
    processor: Any,
    slots: List[Dict[str, Any]],
    week_of: str,
    provider: str,
    week_folder_path: Optional[str],
    plan_id: Optional[str],
    existing_lesson_json: Optional[Dict],
    force_slots: Optional[List[int]],
    processing_weight: float,
) -> tuple:
    """
    Run sequential loop over slots: sanitize, _process_slot, collect lessons and errors.
    Mutates slots list in place (replaces with sanitized dicts).
    Returns (lessons, errors).
    """
    lessons = []
    errors = []

    for i, slot in enumerate(slots, 1):
        slot_num = (
            slot.get("slot_number") if isinstance(slot, dict) else getattr(slot, "slot_number", i)
        )
        slot_subject = (
            slot.get("subject") if isinstance(slot, dict) else getattr(slot, "subject", "Unknown")
        )
        try:
            try:
                slot = processor._sanitize_slot(slot)
            except Exception as sanitize_err:
                if hasattr(slot, "model_dump"):
                    slot = slot.model_dump()
                elif hasattr(slot, "dict"):
                    slot = slot.dict()
                else:
                    slot = dict(slot)

            if not isinstance(slot, dict):
                if hasattr(slot, "model_dump"):
                    slot = slot.model_dump()
                elif hasattr(slot, "dict"):
                    slot = slot.dict()
                else:
                    slot = {
                        "id": getattr(slot, "id", None),
                        "slot_number": getattr(slot, "slot_number", i),
                        "subject": getattr(slot, "subject", "Unknown"),
                        "grade": getattr(slot, "grade", None),
                        "homeroom": getattr(slot, "homeroom", None),
                        "primary_teacher_name": getattr(slot, "primary_teacher_name", None),
                        "primary_teacher_first_name": getattr(slot, "primary_teacher_first_name", None),
                        "primary_teacher_last_name": getattr(slot, "primary_teacher_last_name", None),
                        "primary_teacher_file": getattr(slot, "primary_teacher_file", None),
                        "primary_teacher_file_pattern": getattr(slot, "primary_teacher_file_pattern", None),
                    }
            slot = processor._sanitize_slot(slot)
            slots[i - 1] = slot

            progress_pct = int((i - 1) / len(slots) * processing_weight * 100)
            progress_tracker.update(
                plan_id,
                "processing",
                progress_pct,
                f"Processing slot {i}/{len(slots)}: {slot.get('subject', 'Unknown')} ({slot.get('primary_teacher_name', 'No teacher')})",
            )

            logger.info(
                "batch_slot_processing",
                extra={
                    "plan_id": plan_id,
                    "slot_index": i,
                    "total_slots": len(slots),
                    "subject": slot.get("subject", "Unknown"),
                    "teacher": slot.get("primary_teacher_name"),
                },
            )

            lesson_json = await processor._process_slot(
                slot,
                week_of,
                provider,
                week_folder_path,
                processor._user_base_path,
                plan_id,
                i,
                len(slots),
                processing_weight,
                existing_lesson_json=existing_lesson_json,
                force_ai=slot.get("slot_number") in (force_slots or []),
            )

            hyperlinks_in_json = lesson_json.get("_hyperlinks", [])
            logger.info(
                "sequential_result_collection",
                extra={
                    "slot": slot.get("slot_number"),
                    "subject": slot.get("subject"),
                    "hyperlinks_count": len(hyperlinks_in_json),
                    "has_hyperlinks_key": "_hyperlinks" in lesson_json,
                },
            )
            slot_data = (
                slot.copy()
                if isinstance(slot, dict)
                else {
                    "slot_number": getattr(slot, "slot_number", i),
                    "subject": getattr(slot, "subject", "Unknown"),
                    "primary_teacher_name": getattr(slot, "primary_teacher_name", None),
                    "primary_teacher_first_name": getattr(slot, "primary_teacher_first_name", None),
                    "primary_teacher_last_name": getattr(slot, "primary_teacher_last_name", None),
                }
            )
            lessons.append(
                {
                    "slot_number": (
                        slot_data.get("slot_number")
                        if isinstance(slot_data, dict)
                        else getattr(slot, "slot_number", i)
                    ),
                    "subject": (
                        slot_data.get("subject")
                        if isinstance(slot_data, dict)
                        else getattr(slot, "subject", "Unknown")
                    ),
                    "lesson_json": lesson_json,
                    "slot_data": slot_data,
                }
            )
            logger.info(
                "batch_slot_completed",
                extra={
                    "plan_id": plan_id,
                    "slot_index": i,
                    "total_slots": len(slots),
                    "subject": slot.get("subject", "Unknown"),
                },
            )

            progress_pct = int(i / len(slots) * processing_weight * 100)
            progress_tracker.update(
                plan_id,
                "processing",
                progress_pct,
                f"Completed slot {i}/{len(slots)}: {slot.get('subject', 'Unknown')}",
            )
        except Exception as e:
            traceback.print_exc()
            slot_num = (
                slot.get("slot_number") if isinstance(slot, dict) else getattr(slot, "slot_number", i)
            )
            slot_subject = (
                slot.get("subject") if isinstance(slot, dict) else getattr(slot, "subject", "Unknown")
            )
            try:
                error_str = str(e)
            except UnicodeEncodeError:
                error_str = repr(e).encode("ascii", "replace").decode("ascii")
            error_msg = f"Slot {slot_num} ({slot_subject}): {error_str}"
            errors.append(error_msg)
            logger.error(
                "batch_slot_error",
                extra={
                    "plan_id": plan_id,
                    "slot_index": i,
                    "total_slots": len(slots),
                    "subject": slot.get("subject", "Unknown") if isinstance(slot, dict) else "Unknown",
                    "error": error_msg,
                },
            )
            progress_tracker.update(
                plan_id,
                "error",
                int(i / len(slots) * processing_weight * 100),
                f"Failed slot {i}/{len(slots)}: {error_msg}",
            )

    return (lessons, errors)

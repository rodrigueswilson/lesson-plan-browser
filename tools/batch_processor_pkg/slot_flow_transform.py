"""
LLM transform and post-process finalization for single-slot flow.
Used by slot_flow.process_one_slot.
"""

import traceback
from typing import Any, Callable, Dict, List, Optional, Tuple

from backend.services.objectives_utils import normalize_objectives_in_lesson
from backend.telemetry import logger
from backend.utils.date_formatter import format_week_dates


async def run_llm_transform(
    processor: Any,
    scrubbed_primary_content: str,
    slot: dict,
    week_of: str,
    available_days: Optional[List[str]],
    plan_id: Optional[str],
    update_slot_progress: Callable[[str, int, str], None],
) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Call LLM transform_lesson and return (success, lesson_json, error)."""
    def llm_progress_callback(stage: str, llm_progress: int, message: str):
        slot_progress_min = 8
        slot_progress_max = 70
        slot_progress = slot_progress_min + int(
            (llm_progress - 10) / 80 * (slot_progress_max - slot_progress_min)
        )
        update_slot_progress(stage, slot_progress, message)

    success, lesson_json, error = await __import__("asyncio").to_thread(
        processor.llm_service.transform_lesson,
        primary_content=scrubbed_primary_content,
        grade=slot["grade"],
        subject=slot["subject"],
        week_of=week_of,
        teacher_name=None,
        homeroom=slot.get("homeroom"),
        plan_id=plan_id,
        available_days=available_days,
        progress_callback=llm_progress_callback,
    )
    return success, lesson_json, error


def finalize_lesson_json(
    processor: Any,
    lesson_json: Dict[str, Any],
    original_unit_lessons: Dict[str, str],
    original_objectives: Dict[str, str],
    no_school_days: List[str],
    hyperlinks: List[Dict[str, Any]],
    images: List[Any],
    slot: dict,
    week_of: str,
) -> Dict[str, Any]:
    """Restore unit/lesson and objectives, apply no_school stubs, attach media, set metadata, normalize objectives."""
    if not isinstance(lesson_json, dict):
        if hasattr(lesson_json, "model_dump"):
            lesson_json = lesson_json.model_dump(mode="python")
        elif hasattr(lesson_json, "dict"):
            lesson_json = lesson_json.dict()
        else:
            lesson_json = dict(lesson_json) if lesson_json else {}

    for day_lower, day_data in lesson_json.get("days", {}).items():
        if day_lower in original_unit_lessons:
            day_data["unit_lesson"] = original_unit_lessons[day_lower]
        if day_lower in original_objectives and "objective" in day_data:
            day_data["objective"]["content_objective"] = original_objectives[day_lower]

    if no_school_days:
        for day in no_school_days:
            day_lower = day.lower()
            if day_lower in lesson_json.get("days", {}):
                lesson_json["days"][day_lower] = processor._no_school_day_stub()

    slot_number = slot.get("slot_number")
    subject = slot.get("subject")
    if hyperlinks:
        for hyperlink in hyperlinks:
            if "_source_slot" not in hyperlink:
                hyperlink["_source_slot"] = slot_number
            if "_source_subject" not in hyperlink:
                hyperlink["_source_subject"] = subject

    if images:
        lesson_json["_images"] = images
    if hyperlinks:
        lesson_json["_hyperlinks"] = hyperlinks
        logger.info(
            "sequential_hyperlinks_attached",
            extra={
                "slot": slot.get("slot_number"),
                "subject": slot.get("subject"),
                "hyperlinks_count": len(hyperlinks),
            },
        )
        try:
            from tools.diagnostic_logger import get_diagnostic_logger
            diag = get_diagnostic_logger()
            diag.log_lesson_json_created(slot["slot_number"], slot["subject"], lesson_json)
        except ImportError:
            pass
    else:
        logger.warning(
            "sequential_no_hyperlinks",
            extra={
                "slot": slot.get("slot_number"),
                "subject": slot.get("subject"),
            },
        )

    if images or hyperlinks:
        lesson_json["_media_schema_version"] = "2.0"

    if "metadata" not in lesson_json:
        lesson_json["metadata"] = {}

    try:
        teacher_name_meta = processor._build_teacher_name(
            {
                "first_name": getattr(processor, "_user_first_name", ""),
                "last_name": getattr(processor, "_user_last_name", ""),
                "name": getattr(processor, "_user_name", ""),
            },
            slot,
        )
        lesson_json["metadata"]["teacher_name"] = teacher_name_meta
    except Exception as e:
        print(f"DEBUG: Error in _build_teacher_name: {e}")
        traceback.print_exc()
        lesson_json["metadata"]["teacher_name"] = "Unknown"

    lesson_json["metadata"]["week_of"] = format_week_dates(week_of)
    try:
        lesson_json["metadata"]["slot_number"] = slot.get("slot_number")
        lesson_json["metadata"]["homeroom"] = slot.get("homeroom")
        lesson_json["metadata"]["grade"] = slot.get("grade")
        lesson_json["metadata"]["subject"] = slot.get("subject")
        lesson_json["metadata"]["start_time"] = slot.get("start_time")
        lesson_json["metadata"]["end_time"] = slot.get("end_time")
        lesson_json["metadata"]["day_times"] = slot.get("day_times")
        lesson_json["metadata"]["primary_teacher_name"] = slot.get("primary_teacher_name")
        lesson_json["metadata"]["primary_teacher_first_name"] = slot.get("primary_teacher_first_name")
        lesson_json["metadata"]["primary_teacher_last_name"] = slot.get("primary_teacher_last_name")
    except Exception as e:
        print(f"DEBUG: Error copying slot metadata: {e}")
        traceback.print_exc()

    try:
        normalize_objectives_in_lesson(lesson_json)
    except Exception as e:
        print(f"DEBUG: Error in normalize_objectives_in_lesson: {e}")
        traceback.print_exc()

    return lesson_json

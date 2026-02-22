"""
Merge lessons with existing (if partial/missing_only) and render combined DOCX.
"""
import asyncio
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.progress import progress_tracker
from backend.telemetry import logger


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
                "complete",
                100,
                f"Successfully created lesson plan with {len(all_lessons_for_rendering)} slots",
            )
            progress_tracker.complete(plan_id)
        except Exception as e:
            error_msg = f"Failed to combine lessons: {str(e)}"
            traceback.print_exc()
            errors.append(error_msg)
            progress_tracker.update(
                plan_id, "error", rendering_progress, f"Failed to render: {str(e)}"
            )
    return output_file

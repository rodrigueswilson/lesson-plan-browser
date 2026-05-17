"""
Parallel path for week-level batch processing: extract, originals docx, skip-LLM optimization, transform, collect.
"""
import copy
from typing import Any, Dict, List, Optional

from backend.progress import progress_tracker
from backend.telemetry import logger
from tools.batch_processor_pkg.combine_render.multi_slot_metadata import (
    apply_slot_metadata_to_lesson,
)


async def run_parallel_path(
    processor: Any,
    slots: List[Dict[str, Any]],
    week_of: str,
    provider: str,
    week_folder_path: Optional[str],
    plan_id: Optional[str],
    existing_lesson_json: Optional[Dict],
    force_slots: Optional[List[int]],
    user_id: str,
    refresh_source_documents: bool = False,
) -> tuple:
    """
    Run parallel extract -> originals docx -> skip-LLM optimization -> transform -> collect.
    Returns (lessons, errors, originals_docx).
    """
    lessons = []
    errors = []
    error_slots = set()
    originals_docx = None

    contexts = await processor._extract_slots_parallel_db(
        slots,
        week_of,
        week_folder_path,
        processor._user_base_path,
        plan_id,
        progress_tracker,
        refresh_source_documents=refresh_source_documents,
    )

    try:
        logger.info("batch_auto_generating_originals_docx_parallel")
        originals_docx = await processor._generate_combined_original_docx(
            user_id, week_of, plan_id, week_folder_path
        )
    except Exception as e:
        logger.error(
            "batch_auto_originals_generation_failed_parallel",
            extra={"error": str(e)},
        )

    for ctx in contexts:
        if ctx.error:
            slot_key = ctx.slot.get("slot_number") if isinstance(ctx.slot, dict) else ctx.slot_index
            if slot_key not in error_slots:
                error_slots.add(slot_key)
                errors.append(
                    f"Failed slot {ctx.slot_index}/{ctx.total_slots}: {ctx.error}"
                )

    if existing_lesson_json:
        existing_slot_plans = processor._reconstruct_slots_from_json(
            existing_lesson_json
        )
        for ctx in contexts:
            if ctx.cache_hit and not ctx.error:
                slot_num = ctx.slot.get("slot_number")
                if slot_num in existing_slot_plans and slot_num not in (
                    force_slots or []
                ):
                    ctx.lesson_json = copy.deepcopy(
                        existing_slot_plans[slot_num]["lesson_json"]
                    )
                    apply_slot_metadata_to_lesson(
                        ctx.lesson_json,
                        ctx.slot,
                        processor,
                    )

    transform_count = len(
        [c for c in contexts if not c.error and not c.lesson_json]
    )
    progress_tracker.update(
        plan_id,
        "transforming",
        20,
        f"Transforming {transform_count} slots with AI in parallel...",
        metadata={
            "completed_slots": len([c for c in contexts if c.lesson_json]),
            "total_slots": len(slots),
        },
    )

    contexts = await processor._process_slots_parallel_llm(
        contexts, week_of, provider, plan_id
    )

    for context in contexts:
        if context.error:
            slot_key = context.slot.get("slot_number") if isinstance(context.slot, dict) else context.slot_index
            if slot_key not in error_slots:
                error_slots.add(slot_key)
                errors.append(
                    f"Failed slot {context.slot_index}/{context.total_slots}: {context.error}"
                )
        elif context.lesson_json:
            hyperlinks_in_json = context.lesson_json.get("_hyperlinks", [])
            logger.info(
                "parallel_result_collection",
                extra={
                    "slot": context.slot.get("slot_number"),
                    "subject": context.slot.get("subject"),
                    "has_lesson_json": context.lesson_json is not None,
                    "hyperlinks_count": len(hyperlinks_in_json),
                    "has_hyperlinks_key": "_hyperlinks" in context.lesson_json,
                },
            )
            slot_data = (
                context.slot.copy()
                if isinstance(context.slot, dict)
                else {
                    "slot_number": getattr(
                        context.slot, "slot_number", context.slot_index
                    ),
                    "subject": getattr(context.slot, "subject", "Unknown"),
                    "primary_teacher_name": getattr(
                        context.slot, "primary_teacher_name", None
                    ),
                    "primary_teacher_first_name": getattr(
                        context.slot, "primary_teacher_first_name", None
                    ),
                    "primary_teacher_last_name": getattr(
                        context.slot, "primary_teacher_last_name", None
                    ),
                }
            )
            lessons.append(
                {
                    "slot_number": (
                        slot_data.get("slot_number")
                        if isinstance(slot_data, dict)
                        else getattr(
                            context.slot, "slot_number", context.slot_index
                        )
                    ),
                    "subject": (
                        slot_data.get("subject")
                        if isinstance(slot_data, dict)
                        else getattr(context.slot, "subject", "Unknown")
                    ),
                    "lesson_json": context.lesson_json,
                    "slot_data": slot_data,
                }
            )

    progress_tracker.update(
        plan_id,
        "finalizing",
        80,
        f"Finished slot transformations: {len(lessons)}/{len(slots)} ready for rendering.",
        metadata={"completed_slots": len(lessons), "total_slots": len(slots)},
    )

    return (lessons, errors, originals_docx)

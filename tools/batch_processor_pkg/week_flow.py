"""
Week-level batch processing flow: load user/slots, enrich, parallel or sequential process, combine.
Extracted from orchestrator.process_user_week for Session 13.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.config import settings
from backend.progress import progress_tracker
from backend.telemetry import logger

from tools.batch_processor_pkg import (
    week_flow_existing,
    week_flow_load,
    week_flow_merge_render,
    week_flow_parallel,
    week_flow_sequential,
)


async def run_process_user_week(
    processor: Any,
    user_id: str,
    week_of: str,
    provider: str = "openai",
    week_folder_path: Optional[str] = None,
    slot_ids: Optional[list] = None,
    plan_id: Optional[str] = None,
    partial: bool = False,
    missing_only: bool = False,
    force_slots: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """Process all class slots for a user's week. Delegates to processor for DB, tracker, and slot/combine methods."""
    originals_docx = None
    try:
        logger.info(
            "process_user_week_START",
            extra={"user_id": user_id, "week_of": week_of},
        )
        print(
            f"\n{'=' * 60}\nPROCESS_USER_WEEK STARTED\nUser: {user_id}\nWeek: {week_of}\n{'=' * 60}\n"
        )
        start_time = datetime.now()
    except Exception as e:
        print(f"\n{'=' * 60}\nERROR IN PROCESS_USER_WEEK INIT: {e}\n{'=' * 60}\n")
        raise

    load_result = await week_flow_load.load_user_slots(processor, user_id, slot_ids)
    if isinstance(load_result, dict):
        return load_result
    user, slots, db = load_result

    (
        existing_lesson_json,
        plan_id,
        slots,
        partial,
    ) = await week_flow_existing.load_existing_plan(
        db, user_id, week_of, plan_id, slots, missing_only, partial
    )

    # Store user's metadata for file resolution and rendering
    processor._current_user_id = user_id
    # Prefer base_path_override, but fall back to base_path if available in the user object
    processor._user_base_path = user.get("base_path_override") or user.get("base_path")
    processor._user_first_name = user.get("first_name", "")
    processor._user_last_name = user.get("last_name", "")
    processor._user_name = user.get("name", "")
    logger.info(
        "batch_user_base_path",
        extra={
            "user_id": user_id,
            "user_name": user["name"],
            "base_path": processor._user_base_path or "default",
        },
    )

    # Determine if this is a consolidated plan
    is_consolidated = len(slots) > 1

    # Create or use existing weekly plan record
    if not plan_id:
        plan_id = await asyncio.to_thread(
            db.create_weekly_plan,
            user_id,
            week_of,
            output_file="",  # Will be updated after generation
            week_folder_path=week_folder_path,
            consolidated=is_consolidated,
            total_slots=len(slots),
        )
        await asyncio.to_thread(db.update_weekly_plan, plan_id, status="processing")

    # Store plan_id for tracking
    processor._current_plan_id = plan_id

    # Start tracking total batch duration
    batch_op_id = ""
    try:
        batch_op_id = processor.tracker.start_operation(
            plan_id,
            "batch_process",
            metadata={"total_slots": len(slots), "consolidated": is_consolidated},
        )
    except Exception as e:
        print(f"WARNING: Failed to start batch tracking: {e}")

    processing_weight = settings.PROGRESS_PROCESSING_WEIGHT
    rendering_weight = settings.PROGRESS_RENDERING_WEIGHT

    # Ensure weights sum to 1 for progress tracking
    if abs((processing_weight + rendering_weight) - 1.0) > 1e-6:
        total = processing_weight + rendering_weight
        processing_weight = processing_weight / total
        rendering_weight = rendering_weight / total

    # Process each slot
    lessons = []
    errors = []

    print(f"DEBUG: About to start processing {len(slots)} slots")
    # Update progress: starting
    progress_tracker.update(
        plan_id, "processing", 0, f"Starting to process {len(slots)} slots..."
    )
    print("DEBUG: Progress tracker updated - starting")

    # Check if parallel processing is enabled
    use_parallel = settings.PARALLEL_LLM_PROCESSING and len(slots) > 1

    if use_parallel:
        lessons, errors, originals_docx = await week_flow_parallel.run_parallel_path(
            processor,
            slots,
            week_of,
            provider,
            week_folder_path,
            plan_id,
            existing_lesson_json,
            force_slots,
            user_id,
        )
    else:
        lessons, errors = await week_flow_sequential.run_sequential_path(
            processor,
            slots,
            week_of,
            provider,
            week_folder_path,
            plan_id,
            existing_lesson_json,
            force_slots,
            processing_weight,
        )

    # AUTO-GENERATE ORIGINALS AUDIT DOCX (Sequential/Fallback Path)
    # ONLY if not already generated in parallel path
    if not originals_docx:
        try:
            logger.info("batch_auto_generating_originals_docx_sequential")
            originals_docx = await processor._generate_combined_original_docx(
                user_id, week_of, plan_id, week_folder_path
            )
        except Exception as e:
            logger.error(
                "batch_auto_originals_generation_failed_sequential",
                extra={"error": str(e)},
            )

    output_file = await week_flow_merge_render.merge_and_render(
        processor,
        user,
        lessons,
        existing_lesson_json,
        partial,
        missing_only,
        week_of,
        start_time,
        plan_id,
        processing_weight,
        rendering_weight,
        errors,
    )

    # Update plan status
    total_time = (datetime.now() - start_time).total_seconds() * 1000

    # End tracking total batch duration
    try:
        if batch_op_id:
            processor.tracker.end_operation(
                batch_op_id,
                result={
                    "success": bool(output_file),
                    "processed_slots": len(lessons),
                    "failed_slots": len(errors),
                    "error": "; ".join(errors) if errors else None,
                },
            )
    except Exception as e:
        print(f"WARNING: Failed to end batch tracking: {e}")

    return {
        "success": bool(output_file),
        "plan_id": plan_id,
        "output_file": output_file or "",
        "originals_docx": originals_docx,
        "processed_slots": len(lessons),
        "failed_slots": len(errors),
        "total_time_ms": total_time,
        "consolidated": is_consolidated,
        "total_slots": len(slots),
        "errors": errors if errors else None,
    }

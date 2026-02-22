"""
Single-slot processing flow: resolve file, extract, transform, persist.
Extracted from orchestrator._process_slot for Session 13.
Refactored: resolve/extract/transform in slot_flow_resolve, slot_flow_extract, slot_flow_transform.
"""

import asyncio
import copy
import gc
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.progress import progress_tracker
from backend.telemetry import logger

from tools.batch_processor_pkg.context import SlotProcessingContext
from tools.batch_processor_pkg import slot_flow_resolve
from tools.batch_processor_pkg import slot_flow_extract
from tools.batch_processor_pkg import slot_flow_transform


async def process_one_slot(
    processor: Any,
    slot: Dict[str, Any],
    week_of: str,
    provider: str,
    week_folder_path: Optional[str] = None,
    user_base_path: Optional[str] = None,
    plan_id: Optional[str] = None,
    slot_index: int = 1,
    total_slots: int = 1,
    processing_weight: float = 0.8,
    existing_lesson_json: Optional[Dict[str, Any]] = None,
    force_ai: bool = False,
) -> Dict[str, Any]:
    """Process a single class slot. Resolve file, extract, transform, persist.

    Args:
        processor: BatchProcessor instance (for db, tracker, and delegate methods)
        slot: Class slot data (already sanitized by caller)
        week_of: Week date range
        provider: LLM provider
        week_folder_path: Optional week folder override
        user_base_path: User's base path override
        plan_id: Plan ID for progress tracking
        slot_index: Current slot index (1-based)
        total_slots: Total number of slots being processed
        processing_weight: Weight for processing phase (0-1)
        existing_lesson_json: Existing multi-slot JSON for cache reuse
        force_ai: If True, force LLM transformation even when cache is valid

    Returns:
        Lesson plan JSON for this slot
    """
    slot = processor._sanitize_slot(slot)

    def update_slot_progress(stage: str, slot_progress: int, message: str):
        if plan_id:
            base_progress = int(
                (slot_index - 1) / total_slots * processing_weight * 100
            )
            current_slot_progress = int(
                slot_progress / 100 * (1 / total_slots) * processing_weight * 100
            )
            overall_progress = base_progress + current_slot_progress
            progress_tracker.update(plan_id, stage, overall_progress, message)

    print(
        f"DEBUG: _process_slot - Resolving primary file for slot {slot['slot_number']}"
    )
    update_slot_progress(
        "processing", 10, f"Finding lesson plan file for {slot['subject']}..."
    )
    print("DEBUG: _process_slot - calling _resolve_primary_file")
    primary_file = await slot_flow_resolve.resolve_primary_file(
        processor, slot, week_of, week_folder_path, user_base_path, plan_id
    )
    print(f"DEBUG: _process_slot - Primary file resolved: {primary_file}")

    if not primary_file:
        slot_flow_resolve.raise_no_primary_file_error(
            processor, slot, week_of, week_folder_path, user_base_path
        )

    print("DEBUG: _process_slot - Creating DOCXParser")
    update_slot_progress("processing", 15, "Reading lesson plan document...")
    try:
        parser = await slot_flow_resolve.open_parser_for_slot(
            processor,
            primary_file,
            plan_id,
            slot.get("slot_number"),
            slot.get("subject"),
        )
        print("DEBUG: _process_slot - DOCXParser created successfully")
    except Exception as e:
        logger.error(
            "docx_parser_init_failed",
            extra={
                "slot": slot["slot_number"],
                "subject": slot["subject"],
                "file": primary_file,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise

    user_id = getattr(processor, "_current_user_id", "unknown")
    db_record = await asyncio.to_thread(
        processor.db.get_original_lesson_plan,
        user_id,
        week_of,
        slot["slot_number"],
    )
    cache_hit = False
    if db_record and db_record.source_file_path == primary_file:
        path_obj = Path(primary_file)
        if path_obj.exists():
            current_mtime = path_obj.stat().st_mtime
            if db_record.extracted_at.timestamp() > (current_mtime + 2):
                print(
                    f"[DEBUG] DB Cache hit for slot {slot['slot_number']} ({slot['subject']})"
                )
                cache_hit = True

    if cache_hit and existing_lesson_json and not force_ai:
        existing_slot_plans = processor._reconstruct_slots_from_json(
            existing_lesson_json
        )
        slot_num = slot.get("slot_number")
        if slot_num in existing_slot_plans:
            print(
                f"[DEBUG] REUSING TRANSFORMED PLAN for slot {slot_num} ({slot['subject']}) - Source file unchanged."
            )
            update_slot_progress(
                "processing",
                100,
                f"Reusing existing plan for {slot['subject']}",
            )
            del parser
            gc.collect()
            cached_json = copy.deepcopy(existing_slot_plans[slot_num]["lesson_json"])
            if "metadata" not in cached_json:
                cached_json["metadata"] = {}
            cached_json["metadata"]["primary_teacher_name"] = slot.get("primary_teacher_name")
            cached_json["metadata"]["primary_teacher_first_name"] = slot.get("primary_teacher_first_name")
            cached_json["metadata"]["primary_teacher_last_name"] = slot.get("primary_teacher_last_name")
            try:
                user_dict = {
                    "first_name": getattr(processor, "_user_first_name", ""),
                    "last_name": getattr(processor, "_user_last_name", ""),
                    "name": getattr(processor, "_user_name", ""),
                }
                combined_teacher_name = processor._build_teacher_name(user_dict, slot)
                cached_json["metadata"]["teacher_name"] = combined_teacher_name
            except Exception as e:
                print(f"[DEBUG] Error building combined teacher name in cache reuse: {e}")
                cached_json["metadata"]["teacher_name"] = slot.get("primary_teacher_name") or "Unknown"
            cached_json["metadata"]["grade"] = slot.get("grade")
            cached_json["metadata"]["homeroom"] = slot.get("homeroom")
            cached_json["metadata"]["subject"] = slot.get("subject")
            if slot.get("slot_number") == 2:
                print(f"DEBUG: Cache Inject Slot 2 -> Grade: '{cached_json['metadata']['grade']}', Homeroom: '{cached_json['metadata']['homeroom']}', Teacher: '{cached_json['metadata'].get('teacher_name')}'")
            return cached_json
    elif cache_hit and existing_lesson_json and force_ai:
        print(
            f"[DEBUG] FORCING AI transformation for slot {slot.get('slot_number')} ({slot['subject']}) as requested."
        )

    if parser.is_no_school_day():
        logger.info(
            "no_school_week_detected",
            extra={
                "slot": slot["slot_number"],
                "subject": slot["subject"],
                "file": primary_file,
            },
        )
        return slot_flow_extract.build_no_school_week_json(processor, slot, week_of)

    slot_num = await slot_flow_extract.find_slot_number(
        processor, parser, slot, primary_file, plan_id
    )
    update_slot_progress("processing", 20, "Extracting content from lesson plan...")
    images, hyperlinks = await slot_flow_extract.extract_media_for_slot(
        processor, parser, slot_num, slot, primary_file, plan_id
    )

    print("DEBUG: _process_slot - Checking for No School day")
    if parser.is_no_school_day():
        print("DEBUG: _process_slot - No School day detected, returning minimal JSON")
        logger.info(
            "no_school_day_skipped",
            extra={
                "slot": slot["slot_number"],
                "subject": slot["subject"],
                "file": primary_file,
            },
        )
        if hyperlinks:
            filtered_count = len(hyperlinks)
            hyperlinks = []
            print(
                f"DEBUG: _process_slot - Filtered {filtered_count} hyperlinks (entire document is No School)"
            )
            logger.info(
                "hyperlinks_filtered_no_school",
                extra={
                    "slot": slot["slot_number"],
                    "subject": slot["subject"],
                    "reason": "entire_document_no_school",
                    "filtered_count": filtered_count,
                },
            )
        no_school_json = slot_flow_extract.build_no_school_day_json(
            week_of, slot, hyperlinks
        )
        del parser
        gc.collect()
        return no_school_json

    teacher_name = slot_flow_extract.get_teacher_name(slot)
    update_slot_progress("processing", 25, "Parsing lesson content...")
    content = await slot_flow_extract.extract_content_for_slot(
        processor, parser, slot_num, slot, teacher_name, plan_id
    )
    available_days = slot_flow_extract.get_available_days_from_content(content)
    if not available_days:
        print("DEBUG: _process_slot - No specific days detected, will generate all 5 days")
    else:
        print(f"DEBUG: _process_slot - Generating content for days: {available_days}")

    await processor._persist_original_lesson_plan(
        slot,
        week_of,
        primary_file,
        teacher_name,
        content,
        hyperlinks,
        available_days,
        plan_id,
    )

    original_unit_lessons, original_objectives = (
        slot_flow_extract.get_original_unit_lessons_and_objectives(content)
    )
    primary_content = content.get("full_text", "")
    no_school_days = content.get("no_school_days", [])
    if no_school_days:
        print(f"DEBUG: _process_slot - No School days detected: {no_school_days}")
        no_school_days_normalized = {day.lower().strip() for day in no_school_days}
        initial_count = len(hyperlinks)
        hyperlinks = [
            h
            for h in hyperlinks
            if not h.get("day_hint")
            or h.get("day_hint", "").lower().strip()
            not in no_school_days_normalized
        ]
        filtered_count = initial_count - len(hyperlinks)
        if filtered_count > 0:
            logger.info(
                "hyperlinks_filtered_no_school",
                extra={
                    "slot": slot["slot_number"],
                    "subject": slot["subject"],
                    "no_school_days": no_school_days,
                    "filtered_count": filtered_count,
                    "remaining_count": len(hyperlinks),
                },
            )

    temp_context = SlotProcessingContext(
        slot=slot,
        slot_index=slot_index,
        total_slots=total_slots,
        extracted_content=primary_content,
    )
    processor._scrub_hyperlinks(temp_context)
    scrubbed_primary_content = temp_context.extracted_content
    if temp_context.link_map:
        preserve_msg = (
            f"\n\nIMPORTANT: Your input contains placeholders like {', '.join(list(temp_context.link_map.keys())[:5])}. "
            f"These represent hyperlinks. You MUST preserve these exact tokens in your output."
        )
        scrubbed_primary_content += preserve_msg

    print("DEBUG: _process_slot - Starting LLM transformation")
    update_slot_progress("processing", 30, "Preparing for transformation...")
    try:
        print("DEBUG: _process_slot - Calling LLM service transform_lesson")
        update_slot_progress(
            "processing", 40, f"Transforming {slot['subject']} with AI..."
        )
        success, lesson_json, error = await slot_flow_transform.run_llm_transform(
            processor,
            scrubbed_primary_content,
            slot,
            week_of,
            available_days,
            plan_id,
            update_slot_progress,
        )
        print(f"DEBUG: _process_slot - LLM transform_lesson returned, success: {success}")
        update_slot_progress("processing", 70, "Processing transformation results...")
        if not success:
            print(f"DEBUG: _process_slot - LLM transformation failed: {error}")
            raise ValueError(f"LLM transformation failed: {error}")

        if not isinstance(lesson_json, dict):
            if hasattr(lesson_json, "model_dump"):
                lesson_json = lesson_json.model_dump(mode="python")
            elif hasattr(lesson_json, "dict"):
                lesson_json = lesson_json.dict()
            else:
                lesson_json = dict(lesson_json) if lesson_json else {}

        if temp_context.link_map:
            print(
                f"DEBUG: _process_slot - Restoring {len(temp_context.link_map)} links from placeholders"
            )
            lesson_json, restored_originals = processor._restore_hyperlinks(
                lesson_json, temp_context.link_map
            )
            if restored_originals:
                initial_count = len(hyperlinks)
                hyperlinks = [
                    h
                    for h in hyperlinks
                    if f"[{h['text']}]({h['url']})" not in restored_originals
                    and h["url"] not in restored_originals
                ]
                removed_count = initial_count - len(hyperlinks)
                if removed_count > 0:
                    print(
                        f"DEBUG: _process_slot - Filtered {removed_count} redundant hyperlinks"
                    )

        lesson_json.pop("_usage", None)
        lesson_json.pop("_model", None)
        lesson_json.pop("_provider", None)
        print(
            "DEBUG: _process_slot - Restoring original unit/lesson and objective content"
        )
        update_slot_progress("processing", 85, "Finalizing lesson plan...")
        if no_school_days:
            print(
                f"DEBUG: _process_slot - Replacing {len(no_school_days)} No School days in output"
            )
        lesson_json = slot_flow_transform.finalize_lesson_json(
            processor,
            lesson_json,
            original_unit_lessons,
            original_objectives,
            no_school_days,
            hyperlinks,
            images,
            slot,
            week_of,
        )
        del parser
        gc.collect()
        return lesson_json
    except Exception:
        raise

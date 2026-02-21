"""
Transform subdomain: LLM-based transformation of extracted slot content.
Used by the orchestrator for Phase 2 (parallel or sequential) transformation.
"""
import asyncio
import time
import traceback
from typing import Optional

from backend.config import settings
from backend.progress import progress_tracker
from backend.telemetry import logger
from backend.utils.date_formatter import format_week_dates

from tools.batch_processor_pkg.context import SlotProcessingContext


async def transform_slot_with_llm(
    processor: "BatchProcessor",
    context: SlotProcessingContext,
    week_of: str,
    provider: str,
    plan_id: Optional[str] = None,
) -> SlotProcessingContext:
    """Phase 2: Transform content with LLM (can run in parallel).

    This function calls the LLM service to transform extracted content.
    Multiple instances can run in parallel.

    Args:
        processor: BatchProcessor instance (for llm_service, scrub/restore, build_teacher_name, no_school_day_stub)
        context: SlotProcessingContext with extracted_content
        week_of: Week date range
        provider: LLM provider name
        plan_id: Plan ID for progress tracking

    Returns:
        Updated SlotProcessingContext with lesson_json

    Raises:
        ValueError: If LLM transformation fails
    """
    if context.lesson_json:
        print(
            f"[DEBUG] _transform_slot_with_llm: Reusing existing lesson_json for slot {context.slot.get('slot_number')}"
        )
        slot = context.slot
        if "metadata" not in context.lesson_json:
            context.lesson_json["metadata"] = {}
        context.lesson_json["metadata"]["slot_number"] = slot.get("slot_number")
        context.lesson_json["metadata"]["grade"] = slot.get("grade")
        context.lesson_json["metadata"]["homeroom"] = slot.get("homeroom")
        context.lesson_json["metadata"]["subject"] = slot.get("subject")
        if slot.get("start_time"):
            context.lesson_json["metadata"]["start_time"] = slot.get("start_time")
        if slot.get("end_time"):
            context.lesson_json["metadata"]["end_time"] = slot.get("end_time")
        context.lesson_json["metadata"]["primary_teacher_name"] = slot.get("primary_teacher_name")
        context.lesson_json["metadata"]["primary_teacher_first_name"] = slot.get("primary_teacher_first_name")
        context.lesson_json["metadata"]["primary_teacher_last_name"] = slot.get("primary_teacher_last_name")
        try:
            combined_teacher_name = processor._build_teacher_name(
                {
                    "first_name": getattr(processor, "_user_first_name", ""),
                    "last_name": getattr(processor, "_user_last_name", ""),
                    "name": getattr(processor, "_user_name", ""),
                },
                slot,
            )
            context.lesson_json["metadata"]["teacher_name"] = combined_teacher_name
        except Exception as e:
            print(f"[DEBUG] Error building combined teacher name in _transform_slot_with_llm: {e}")
            context.lesson_json["metadata"]["teacher_name"] = slot.get("primary_teacher_name") or "Unknown"
        print(f"[DEBUG] Updated metadata for slot {slot.get('slot_number')}: grade={slot.get('grade')}, homeroom={slot.get('homeroom')}, teacher={context.lesson_json['metadata'].get('teacher_name')}")
        return context

    slot = context.slot
    total_slots = context.total_slots

    if context.error:
        return context

    if context.extracted_content == "__NO_SCHOOL_WEEK__":
        user_dict = {
            "first_name": getattr(processor, "_user_first_name", ""),
            "last_name": getattr(processor, "_user_last_name", ""),
            "name": getattr(processor, "_user_name", ""),
        }
        context.lesson_json = {
            "metadata": {
                "teacher_name": processor._build_teacher_name(user_dict, slot),
                "grade": slot.get("grade", ""),
                "subject": slot["subject"],
                "week_of": week_of,
                "homeroom": slot.get("homeroom", ""),
                "slot_number": slot["slot_number"],
            },
            "days": {
                day: {"unit_lesson": "No School"}
                for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]
            },
            "_images": [],
            "_hyperlinks": [],
        }
        return context

    start_time = time.time()
    is_parallel = settings.PARALLEL_LLM_PROCESSING and total_slots > 1

    processor._scrub_hyperlinks(context)

    if context.link_map:
        preserve_msg = (
            f"\n\nIMPORTANT: Your input contains placeholders like {', '.join(list(context.link_map.keys())[:5])}. "
            f"These represent hyperlinks. You MUST preserve these tokens exactly in your output."
        )
        llm_primary_content = context.extracted_content + preserve_msg
    else:
        llm_primary_content = context.extracted_content

    def llm_progress_callback(stage: str, llm_progress: int, message: str):
        if plan_id:
            phase2_min = 20
            phase2_max = 80
            phase2_progress = phase2_min + int(
                (llm_progress - 10) / 80 * (phase2_max - phase2_min)
            )
            progress_tracker.update(plan_id, stage, phase2_progress, message)

    try:
        success, lesson_json, error = await asyncio.to_thread(
            processor.llm_service.transform_lesson,
            primary_content=llm_primary_content,
            grade=slot["grade"],
            subject=slot["subject"],
            week_of=week_of,
            teacher_name=None,
            homeroom=slot.get("homeroom"),
            plan_id=plan_id,
            available_days=context.available_days,
            progress_callback=llm_progress_callback,
        )

        if not success:
            context.error = f"LLM transformation failed: {error}"
            raise ValueError(context.error)

        if not isinstance(lesson_json, dict):
            if hasattr(lesson_json, "model_dump"):
                lesson_json = lesson_json.model_dump(mode="python")
            elif hasattr(lesson_json, "dict"):
                lesson_json = lesson_json.dict()
            else:
                lesson_json = dict(lesson_json) if lesson_json else {}

        images = context.slot.get("_extracted_images", [])
        hyperlinks = context.slot.get("_extracted_hyperlinks", [])

        if context.link_map:
            logger.info(
                "restoring_links_from_placeholders",
                extra={"slot": slot.get("slot_number"), "link_count": len(context.link_map)},
            )
            lesson_json, restored_originals = processor._restore_hyperlinks(
                lesson_json, context.link_map
            )
            if restored_originals:
                hyperlinks = [
                    h
                    for h in hyperlinks
                    if f"[{h['text']}]({h['url']})" not in restored_originals
                    and h["url"] not in restored_originals
                ]
                removed_count = len(context.slot.get("_extracted_hyperlinks", [])) - len(hyperlinks)
                if removed_count > 0:
                    logger.info(
                        "filtering_redundant_hyperlinks",
                        extra={
                            "slot": slot.get("slot_number"),
                            "removed": removed_count,
                            "remaining": len(hyperlinks),
                        },
                    )

        lesson_json.pop("_usage", None)
        lesson_json.pop("_model", None)
        lesson_json.pop("_provider", None)

        print(
            f"[DEBUG] _transform_slot_with_llm (PARALLEL): Slot {slot.get('slot_number')}, "
            f"Retrieved {len(hyperlinks)} hyperlinks from context.slot['_extracted_hyperlinks']"
        )
        logger.info(
            "parallel_hyperlink_retrieval",
            extra={
                "slot": slot.get("slot_number"),
                "subject": slot.get("subject"),
                "hyperlinks_count": len(hyperlinks),
                "has_hyperlinks_in_context": "_extracted_hyperlinks" in context.slot,
            },
        )

        slot_number = slot.get("slot_number")
        subject = slot.get("subject")
        if hyperlinks:
            print(
                f"[DEBUG] _transform_slot_with_llm (PARALLEL): Processing {len(hyperlinks)} hyperlinks "
                f"for slot {slot_number}, subject {subject}"
            )
            for hyperlink in hyperlinks:
                if "_source_slot" not in hyperlink:
                    hyperlink["_source_slot"] = slot_number
                if "_source_subject" not in hyperlink:
                    hyperlink["_source_subject"] = subject

        if images:
            lesson_json["_images"] = images
            print(
                f"[DEBUG] _transform_slot_with_llm (PARALLEL): Added {len(images)} images to lesson_json"
            )
        if hyperlinks:
            print(
                f"[DEBUG] _transform_slot_with_llm (PARALLEL): Adding {len(hyperlinks)} hyperlinks to lesson_json"
            )
            lesson_json["_hyperlinks"] = hyperlinks
            logger.info(
                "parallel_hyperlinks_attached",
                extra={"slot": slot_number, "subject": subject, "hyperlinks_count": len(hyperlinks)},
            )
        else:
            print(
                f"[WARN] _transform_slot_with_llm (PARALLEL): No hyperlinks to attach for slot {slot_number}, subject {subject}"
            )
            logger.warning(
                "parallel_no_hyperlinks",
                extra={
                    "slot": slot_number,
                    "subject": subject,
                    "context_slot_keys": list(context.slot.keys()),
                },
            )

        if images or hyperlinks:
            lesson_json["_media_schema_version"] = "2.0"

        if "metadata" not in lesson_json:
            lesson_json["metadata"] = {}
        try:
            teacher_name = processor._build_teacher_name(
                {
                    "first_name": getattr(processor, "_user_first_name", ""),
                    "last_name": getattr(processor, "_user_last_name", ""),
                    "name": getattr(processor, "_user_name", ""),
                },
                slot,
            )
            lesson_json["metadata"]["teacher_name"] = teacher_name
        except Exception as e:
            print(f"DEBUG: Error in _build_teacher_name (parallel path): {e}")
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
            if slot.get("slot_number") == 2:
                print(f"DEBUG: Preserving Slot 2 Metadata -> Grade: '{lesson_json['metadata']['grade']}', Homeroom: '{lesson_json['metadata']['homeroom']}'")
        except Exception as e:
            print(f"DEBUG: Error copying slot metadata (parallel path): {e}")
            traceback.print_exc()

        if context.no_school_days:
            for day in context.no_school_days:
                day_lower = day.lower().strip()
                if day_lower in lesson_json.get("days", {}):
                    lesson_json["days"][day_lower] = processor._no_school_day_stub()

        elapsed_time = (time.time() - start_time) * 1000
        context.lesson_json = lesson_json
        context.is_parallel = is_parallel
        context.parallel_slot_count = total_slots if is_parallel else None
        if is_parallel:
            context.sequential_time_ms = elapsed_time * total_slots

        usage = lesson_json.get("_usage", {})
        if usage:
            context.tpm_usage = usage.get("tpm_usage")
            context.rpm_usage = usage.get("rpm_usage")

    except Exception as e:
        context.error = str(e)
        logger.error(
            "llm_transformation_failed",
            extra={
                "slot": slot["slot_number"],
                "subject": slot["subject"],
                "error": str(e),
            },
        )
        raise

    return context

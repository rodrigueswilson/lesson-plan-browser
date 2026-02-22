"""
Combined original DOCX generation and file-group processing for batch processor.
Fetches original plans from DB, renders per-slot DOCX, merges; processes slot groups by file.
Extracted from orchestrator.
"""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from backend.telemetry import logger
from tools.batch_processor_pkg.combined_original_render import (
    render_combined_originals_sync,
)
from tools.batch_processor_pkg.context import SlotProcessingContext


async def process_file_group(
    processor: Any,
    file_path: Optional[str],
    group: List[Tuple[int, Dict[str, Any]]],
    week_of: str,
    week_folder_path: Optional[str],
    user_base_path: Optional[str],
    plan_id: Optional[str],
    semaphore: asyncio.Semaphore,
) -> List[SlotProcessingContext]:
    """Process a group of slots that share the same source file."""
    contexts = []
    user_id = getattr(processor, "_current_user_id", "unknown")

    if not file_path:
        for i, slot in group:
            ctx = SlotProcessingContext(
                slot=slot, slot_index=i, total_slots=len(group)
            )
            ctx.error = "No primary teacher file found."
            contexts.append(ctx)
        return contexts

    if file_path not in processor._file_locks:
        processor._file_locks[file_path] = asyncio.Lock()

    async with processor._file_locks[file_path]:
        remaining_group = []

        path_obj = Path(file_path)
        current_mtime = 0
        if path_obj.exists():
            stat = path_obj.stat()
            current_mtime = stat.st_mtime

        for i, slot in group:
            context = SlotProcessingContext(
                slot=slot,
                slot_index=i,
                total_slots=len(group),
                primary_file=file_path,
            )

            db_record = await asyncio.to_thread(
                processor.db.get_original_lesson_plan,
                user_id,
                week_of,
                slot["slot_number"],
            )

            if db_record and db_record.source_file_path == file_path:
                if path_obj.exists():
                    if db_record.extracted_at.timestamp() > (current_mtime + 2):
                        logger.info(
                            f"DB Cache hit for slot {slot['slot_number']} ({slot['subject']})"
                        )
                        context.extracted_content = db_record.full_text
                        context.available_days = db_record.available_days
                        context.cache_hit = True

                        cached_hyperlinks = []
                        if db_record.content_json:
                            context.slot["_extracted_images"] = (
                                db_record.content_json.get(
                                    "_extracted_images", []
                                )
                            )
                            cached_hyperlinks = db_record.content_json.get(
                                "_extracted_hyperlinks", []
                            )
                            context.slot["_extracted_hyperlinks"] = (
                                cached_hyperlinks
                            )
                            context.no_school_days = (
                                db_record.content_json.get(
                                    "no_school_days", []
                                )
                            )

                        if not cached_hyperlinks:
                            remaining_group.append((i, slot, context))
                        else:
                            contexts.append(context)
                        continue

            remaining_group.append((i, slot, context))

        if not remaining_group:
            return contexts

        try:
            async with semaphore:
                logger.info(f"Opening DOCX for parsing group: {file_path}")
                parser = await processor._open_docx_with_retry(
                    file_path, plan_id=plan_id
                )

                for i, slot, context in remaining_group:
                    try:
                        primary_first = slot.get(
                            "primary_teacher_first_name", ""
                        ).strip()
                        primary_last = slot.get(
                            "primary_teacher_last_name", ""
                        ).strip()
                        teacher_name = (
                            f"{primary_first} {primary_last}".strip()
                            or slot.get("primary_teacher_name", "").strip()
                        )

                        actual_slot_num = await asyncio.to_thread(
                            parser.find_slot_by_subject,
                            slot["subject"],
                            teacher_name,
                            slot.get("homeroom"),
                            slot.get("grade"),
                        )

                        content_data = await asyncio.to_thread(
                            parser.extract_subject_content_for_slot,
                            actual_slot_num,
                            slot["subject"],
                            None,
                            False,
                        )

                        if (
                            "_extracted_hyperlinks" in context.slot
                            and context.slot["_extracted_hyperlinks"]
                        ):
                            hyperlinks = context.slot["_extracted_hyperlinks"]
                        else:
                            hyperlinks = await asyncio.to_thread(
                                parser.extract_hyperlinks_for_slot,
                                actual_slot_num,
                            )

                        images = await asyncio.to_thread(
                            parser.extract_images_for_slot, actual_slot_num
                        )

                        logger.info(
                            "parallel_file_group_media_extracted",
                            extra={
                                "slot": slot["slot_number"],
                                "subject": slot["subject"],
                                "images_count": len(images),
                                "hyperlinks_count": len(hyperlinks),
                            },
                        )

                        initial_hyperlink_count = len(hyperlinks)
                        if parser.is_no_school_day():
                            hyperlinks = []
                        elif "no_school_days" in content_data:
                            no_school_days_normalized = {
                                day.lower().strip()
                                for day in content_data["no_school_days"]
                            }
                            hyperlinks = [
                                h
                                for h in hyperlinks
                                if not h.get("day_hint")
                                or h.get("day_hint", "").lower().strip()
                                not in no_school_days_normalized
                            ]
                            filtered_count = (
                                initial_hyperlink_count - len(hyperlinks)
                            )
                            if filtered_count > 0:
                                logger.info(
                                    "parallel_hyperlinks_filtered_no_school",
                                    extra={
                                        "slot": slot["slot_number"],
                                        "subject": slot["subject"],
                                        "filtered_count": filtered_count,
                                        "remaining_count": len(hyperlinks),
                                    },
                                )

                        context.extracted_content = content_data.get(
                            "full_text", ""
                        )
                        context.available_days = content_data.get(
                            "available_days", []
                        )
                        context.no_school_days = content_data.get(
                            "no_school_days", []
                        )

                        context.slot["_extracted_images"] = images
                        context.slot["_extracted_hyperlinks"] = hyperlinks

                        content_data["_extracted_images"] = images
                        content_data["_extracted_hyperlinks"] = hyperlinks
                        hyperlink_texts = [
                            h["text"] for h in hyperlinks if h.get("text")
                        ]
                        if hyperlink_texts:
                            preserve_instruction = (
                                "\n\nIMPORTANT: Preserve these exact phrases in your output "
                                f"(they are hyperlinks): {', '.join(hyperlink_texts[:20])}"
                            )
                            context.extracted_content += preserve_instruction

                        metadata = content_data.get("metadata", {})
                        primary_teacher_name = (
                            metadata.get("primary_teacher_name")
                            or slot.get("primary_teacher_name")
                            or slot.get("teacher_name")
                        )

                        structured_days = {}
                        if "table_content" in content_data:
                            for day, day_data in content_data[
                                "table_content"
                            ].items():
                                day_lower = day.lower().strip()
                                if day_lower in [
                                    "monday",
                                    "tuesday",
                                    "wednesday",
                                    "thursday",
                                    "friday",
                                ]:
                                    day_links = [
                                        h
                                        for h in hyperlinks
                                        if h.get("day", "").lower().strip()
                                        == day_lower
                                    ]
                                    structured_days[f"{day_lower}_content"] = (
                                        processor._map_day_content_to_schema(
                                            day_data,
                                            slot,
                                            day_hyperlinks=day_links,
                                        )
                                    )

                        plan_data = {
                            "id": f"orig_{uuid.uuid4()}",
                            "user_id": user_id,
                            "week_of": week_of,
                            "slot_number": slot["slot_number"],
                            "subject": slot["subject"],
                            "grade": metadata.get("grade")
                            or slot.get("grade", "Unknown"),
                            "homeroom": metadata.get("homeroom")
                            or slot.get("homeroom"),
                            "source_file_path": file_path,
                            "source_file_name": path_obj.name,
                            "primary_teacher_name": primary_teacher_name,
                            "extracted_at": datetime.utcnow(),
                            "content_json": content_data,
                            "full_text": context.extracted_content,
                            "available_days": context.available_days,
                            "has_no_school": parser.is_no_school_day(),
                            "status": "extracted",
                            **structured_days,
                        }
                        await asyncio.to_thread(
                            processor.db.create_original_lesson_plan,
                            plan_data,
                        )
                        contexts.append(context)

                    except Exception as e:
                        logger.error(
                            f"Error extracting slot {slot['slot_number']}: {e}"
                        )
                        context.error = str(e)
                        contexts.append(context)

        except Exception as e:
            logger.error(f"Failed to parse group file {file_path}: {e}")
            for i, slot, context in remaining_group:
                context.error = f"Failed to parse DOCX: {str(e)}"
                contexts.append(context)

    return contexts


async def generate_combined_original_docx(
    processor: Any,
    user_id: str,
    week_of: str,
    plan_id: str,
    week_folder_path: Optional[str] = None,
    get_file_manager_fn: Optional[Callable[..., Any]] = None,
) -> Optional[str]:
    """
    Generates a combined DOCX of all original plans for the week using
    structured schema data. Reuses the standard DOCXRenderer for visual consistency.
    """
    logger.info(
        f"Generating combined original DOCX for {user_id}, week {week_of}"
    )

    plans = await asyncio.to_thread(
        processor.db.get_original_lesson_plans_for_week, user_id, week_of
    )
    if not plans:
        logger.warning(
            "combined_originals_skipped_no_plans",
            extra={"user_id": user_id, "week": week_of},
        )
        return None

    plans.sort(key=lambda x: x.slot_number)

    logger.info(
        "combined_originals_plans_fetched",
        extra={
            "total_plans": len(plans),
            "plans": [
                {
                    "slot_number": p.slot_number,
                    "subject": p.subject,
                    "grade": p.grade,
                    "source_file_name": p.source_file_name,
                    "primary_teacher_name": p.primary_teacher_name,
                }
                for p in plans
            ],
        },
    )

    if get_file_manager_fn is None:
        from tools.batch_processor import get_file_manager as _get_fm
        get_file_manager_fn = _get_fm

    return await asyncio.to_thread(
        render_combined_originals_sync,
        processor,
        plans,
        week_of,
        plan_id,
        week_folder_path,
        get_file_manager_fn,
    )

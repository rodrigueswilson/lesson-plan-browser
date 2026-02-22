"""
Single-slot processing flow: resolve file, extract, transform, persist.
Extracted from orchestrator._process_slot for Session 13.
"""

import asyncio
import copy
import gc
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.progress import progress_tracker
from backend.services.objectives_utils import normalize_objectives_in_lesson
from backend.telemetry import logger
from backend.utils.date_formatter import format_week_dates

from tools.batch_processor_pkg.context import SlotProcessingContext


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
    if plan_id:

        def _resolve_with_tracking():
            try:
                with processor.tracker.track_operation(
                    plan_id,
                    "parse_resolve_file",
                    metadata={
                        "slot_number": slot.get("slot_number"),
                        "subject": slot["subject"],
                        "week_of": week_of,
                    },
                ):
                    return processor._resolve_primary_file(
                        slot, week_of, week_folder_path, user_base_path
                    )
            except Exception as e:
                print(f"DEBUG: Error in _resolve_with_tracking: {e}")
                traceback.print_exc()
                raise

        primary_file = await asyncio.to_thread(_resolve_with_tracking)
    else:
        primary_file = processor._resolve_primary_file(
            slot, week_of, week_folder_path, user_base_path
        )
    print(f"DEBUG: _process_slot - Primary file resolved: {primary_file}")

    if not primary_file:
        if week_folder_path:
            week_folder = Path(week_folder_path)
        else:
            file_mgr = processor.get_file_manager(base_path=user_base_path)
            week_folder = file_mgr.get_week_folder(week_of)

        teacher_pattern = (
            slot.get("primary_teacher_file_pattern")
            or slot.get("primary_teacher_name")
            or (
                f"{slot.get('primary_teacher_first_name', '')} {slot.get('primary_teacher_last_name', '')}".strip()
                if slot.get("primary_teacher_first_name")
                or slot.get("primary_teacher_last_name")
                else None
            )
        )

        error_msg = (
            f"No primary teacher file found for slot {slot['slot_number']} (subject: '{slot['subject']}').\n"
            f"Week folder: {week_folder} (exists: {week_folder.exists()})\n"
        )

        if not teacher_pattern:
            error_msg += (
                f"\nCONFIGURATION MISSING: Slot {slot['slot_number']} needs primary teacher information.\n"
                f"Please configure one of the following:\n"
                f"  - primary_teacher_file_pattern (e.g., 'Davies', 'Savoca')\n"
                f"  - primary_teacher_name\n"
                f"  - primary_teacher_first_name + primary_teacher_last_name\n"
            )
        else:
            error_msg += f"\nSearched for pattern: '{teacher_pattern}'\n"
            if week_folder.exists():
                docx_files = list(week_folder.glob("*.docx"))
                error_msg += f"Available files ({len(docx_files)} total):\n"
                for f in docx_files[:10]:
                    error_msg += f"  - {f.name}\n"
                if len(docx_files) > 10:
                    error_msg += f"  ... and {len(docx_files) - 10} more files\n"
                error_msg += (
                    "\nTROUBLESHOOTING:\n"
                    "1. Check if the teacher's name appears in any filename\n"
                    "2. Verify the filename format matches the pattern\n"
                    "3. Ensure files are in the correct week folder\n"
                )
            else:
                error_msg += "\nWeek folder does not exist. Please create it or check the path.\n"

        raise ValueError(error_msg)

    print("DEBUG: _process_slot - Creating DOCXParser")
    update_slot_progress("processing", 15, "Reading lesson plan document...")

    try:
        parser = await processor._open_docx_with_retry(
            primary_file,
            plan_id=plan_id,
            slot_number=slot.get("slot_number"),
            subject=slot.get("subject"),
        )
        print("DEBUG: _process_slot - DOCXParser created successfully")

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

            user_dict = {
                "first_name": processor._user_first_name,
                "last_name": processor._user_last_name,
                "name": processor._user_name,
            }

            return {
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
                    for day in [
                        "monday",
                        "tuesday",
                        "wednesday",
                        "thursday",
                        "friday",
                    ]
                },
                "_images": [],
                "_hyperlinks": [],
            }

        print("DEBUG: _process_slot - Validating slot availability")
        total_tables = len(parser.doc.tables)

        has_signature = False
        if total_tables > 0:
            last_table = parser.doc.tables[-1]
            if last_table.rows and last_table.rows[0].cells:
                first_cell = last_table.rows[0].cells[0].text.strip().lower()
                if "signature" in first_cell or "required signatures" in first_cell:
                    has_signature = True

        if has_signature:
            available_slots = (total_tables - 1) // 2
        else:
            available_slots = total_tables // 2

        requested_slot = slot["slot_number"]
        print(
            f"DEBUG: _process_slot - Document has {available_slots} available slots, requested: {requested_slot}"
        )

        print("DEBUG: _process_slot - Logging table structure")
        logger.info(
            "document_table_structure",
            extra={
                "slot": slot["slot_number"],
                "subject": slot["subject"],
                "file": Path(primary_file).name,
                "total_tables": total_tables,
            },
        )

        for table_idx, table in enumerate(parser.doc.tables):
            first_cell = ""
            if table.rows and table.rows[0].cells:
                first_cell = table.rows[0].cells[0].text.strip()

            first_row_text = ""
            if table.rows:
                first_row_text = " | ".join(
                    cell.text.strip()[:30] for cell in table.rows[0].cells[:5]
                )

            logger.info(
                "table_structure_detail",
                extra={
                    "slot": slot["slot_number"],
                    "file": Path(primary_file).name,
                    "table_idx": table_idx,
                    "first_cell": first_cell[:100],
                    "first_row": first_row_text[:200],
                    "row_count": len(table.rows),
                    "col_count": len(table.columns) if table.rows else 0,
                },
            )

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

    primary_first = slot.get("primary_teacher_first_name", "").strip()
    primary_last = slot.get("primary_teacher_last_name", "").strip()
    teacher_name = (
        f"{primary_first} {primary_last}".strip()
        or slot.get("primary_teacher_name", "").strip()
    )

    print(
        f"DEBUG: _process_slot - Finding actual slot for subject '{slot['subject']}'"
    )
    try:
        if plan_id:
            _parser = parser

            def _find_slot_with_tracking():
                with processor.tracker.track_operation(
                    plan_id,
                    "parse_find_slot",
                    metadata={
                        "requested_slot": slot["slot_number"],
                        "subject": slot["subject"],
                    },
                ):
                    return _parser.find_slot_by_subject(
                        slot["subject"],
                        teacher_name,
                        slot.get("homeroom"),
                        slot.get("grade"),
                    )

            actual_slot_num = await asyncio.to_thread(_find_slot_with_tracking)
        else:
            actual_slot_num = await asyncio.to_thread(
                parser.find_slot_by_subject,
                slot["subject"],
                teacher_name,
                slot.get("homeroom"),
                slot.get("grade"),
            )
        if actual_slot_num != slot["slot_number"]:
            print(
                f"DEBUG: _process_slot - Slot mismatch! Requested slot {slot['slot_number']}, found subject in slot {actual_slot_num}"
            )

            is_single_slot = available_slots == 1
            is_expected = is_single_slot

            warning_type = "slot_subject_mismatch"
            if is_single_slot:
                warning_type = "slot_subject_mismatch_single_slot"
                message = (
                    f"Slot {slot['slot_number']} requested, but document '{Path(primary_file).name}' "
                    f"has only 1 slot. Content correctly extracted from slot 1. "
                    f"This is expected behavior for single-slot documents."
                )
            else:
                warning_type = "slot_subject_mismatch_multi_slot"
                message = (
                    f"Slot {slot['slot_number']} requested for '{slot['subject']}', but document "
                    f"'{Path(primary_file).name}' has '{slot['subject']}' in slot {actual_slot_num}. "
                    f"Content correctly extracted via subject-based detection. "
                    f"Consider updating slot configuration to match document structure (slot {actual_slot_num})."
                )

            logger.warning(
                warning_type,
                extra={
                    "requested_slot": slot["slot_number"],
                    "actual_slot": actual_slot_num,
                    "subject": slot["subject"],
                    "file": Path(primary_file).name,
                    "available_slots": available_slots,
                    "is_single_slot": is_single_slot,
                    "is_expected": is_expected,
                    "message": message,
                    "teacher": teacher_name,
                    "grade": slot.get("grade"),
                    "homeroom": slot.get("homeroom"),
                },
            )
        slot_num = actual_slot_num
    except ValueError as e:
        print(f"DEBUG: _process_slot - Subject detection failed: {e}")

        if slot["slot_number"] > available_slots:
            print(
                f"DEBUG: _process_slot - Requested slot {slot['slot_number']} > available slots ({available_slots}). "
                f"Auto-mapping to slot 1."
            )
            logger.warning(
                "slot_auto_mapped",
                extra={
                    "requested_slot": slot["slot_number"],
                    "available_slots": available_slots,
                    "mapped_to": 1,
                    "subject": slot["subject"],
                    "file": Path(primary_file).name,
                    "message": (
                        f"Slot {slot['slot_number']} requested, but document '{Path(primary_file).name}' "
                        f"has only {available_slots} slot(s). Auto-mapped to slot 1. "
                        f"This is expected behavior for single-slot documents."
                    ),
                    "teacher": teacher_name,
                    "grade": slot.get("grade"),
                    "homeroom": slot.get("homeroom"),
                },
            )
            slot_num = 1
        else:
            print(
                f"DEBUG: _process_slot - Using requested slot {slot['slot_number']} as fallback (validated: {available_slots} slots available)"
            )
            slot_num = slot["slot_number"]

    print(
        f"DEBUG: _process_slot - Extracting images and hyperlinks for slot {slot_num} (subject: {slot['subject']})"
    )
    update_slot_progress("processing", 20, "Extracting content from lesson plan...")

    try:
        if plan_id:
            _parser = parser

            def _extract_media_with_tracking():
                images_result = None
                hyperlinks_result = None
                with processor.tracker.track_operation(
                    plan_id,
                    "parse_extract_images",
                    metadata={
                        "slot_number": slot_num,
                        "subject": slot["subject"],
                    },
                ):
                    images_result = _parser.extract_images_for_slot(slot_num)
                with processor.tracker.track_operation(
                    plan_id,
                    "parse_extract_hyperlinks",
                    metadata={
                        "slot_number": slot_num,
                        "subject": slot["subject"],
                    },
                ):
                    hyperlinks_result = _parser.extract_hyperlinks_for_slot(
                        slot_num
                    )
                return images_result, hyperlinks_result

            images, hyperlinks = await asyncio.to_thread(
                _extract_media_with_tracking
            )
        else:
            images = await asyncio.to_thread(
                parser.extract_images_for_slot, slot_num
            )
            hyperlinks = await asyncio.to_thread(
                parser.extract_hyperlinks_for_slot, slot_num
            )
        print(
            f"[DEBUG] _process_slot (SEQUENTIAL): Extracted {len(images)} images, {len(hyperlinks)} hyperlinks "
            f"for slot {slot['slot_number']}, subject {slot['subject']}"
        )

        from tools.diagnostic_logger import get_diagnostic_logger

        diag = get_diagnostic_logger()
        diag.log_hyperlinks_extracted(
            slot["slot_number"], slot["subject"], hyperlinks, primary_file
        )

        logger.info(
            "slot_media_extracted",
            extra={
                "slot": slot["slot_number"],
                "subject": slot["subject"],
                "images_count": len(images),
                "hyperlinks_count": len(hyperlinks),
                "extraction_mode": "slot_aware",
                "processing_path": "sequential",
            },
        )

        if hyperlinks:
            print(
                f"[DEBUG] _process_slot (SEQUENTIAL): Hyperlink details: "
                f"{[(h.get('text', '')[:30], h.get('url', '')[:50]) for h in hyperlinks[:3]]}"
            )
    except ValueError as e:
        logger.error(
            "slot_structure_invalid",
            extra={
                "slot": slot_num,
                "subject": slot["subject"],
                "file": primary_file,
                "error": str(e),
            },
        )
        raise
    except Exception as e:
        logger.error(
            "media_extraction_failed",
            extra={
                "slot": slot["slot_number"],
                "subject": slot["subject"],
                "file": primary_file,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        images = []
        hyperlinks = []

    print("DEBUG: _process_slot - Checking for No School day")
    if parser.is_no_school_day():
        print(
            "DEBUG: _process_slot - No School day detected, returning minimal JSON"
        )
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

        no_school_json = {
            "metadata": {
                "week_of": week_of,
                "grade": slot["grade"],
                "subject": slot["subject"],
                "homeroom": slot.get("homeroom"),
                "no_school": True,
            },
            "days": {
                day: {
                    "unit_lesson": "No School",
                    "objective": {
                        "content_objective": "No School",
                        "student_goal": "No School",
                        "wida_objective": "No School",
                    },
                    "anticipatory_set": {
                        "original_content": "No School",
                        "bilingual_bridge": "",
                    },
                    "tailored_instruction": {
                        "original_content": "No School",
                        "co_teaching_model": {},
                        "ell_support": [],
                        "special_needs_support": [],
                        "materials": [],
                    },
                    "misconceptions": {
                        "original_content": "No School",
                        "linguistic_note": {},
                    },
                    "assessment": {
                        "primary_assessment": "No School",
                        "bilingual_overlay": {},
                    },
                    "homework": {
                        "original_content": "No School",
                        "family_connection": "",
                    },
                }
                for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]
            },
        }

        if hyperlinks:
            no_school_json["_hyperlinks"] = hyperlinks
            no_school_json["_media_schema_version"] = "2.0"

        del parser
        gc.collect()

        return no_school_json

    print("DEBUG: _process_slot - Extracting subject content (SLOT-AWARE)")
    update_slot_progress("processing", 25, "Parsing lesson content...")
    if plan_id:
        _parser = parser

        def _extract_content_with_tracking():
            with processor.tracker.track_operation(
                plan_id,
                "parse_extract_content",
                metadata={
                    "slot_number": slot_num,
                    "subject": slot["subject"],
                },
            ):
                return _parser.extract_subject_content_for_slot(
                    slot_num, slot["subject"], teacher_name, strip_urls=False
                )

        content = await asyncio.to_thread(_extract_content_with_tracking)
    else:
        content = await asyncio.to_thread(
            parser.extract_subject_content_for_slot,
            slot_num,
            slot["subject"],
            teacher_name,
            strip_urls=False,
        )
    print(
        f"DEBUG: _process_slot - Content extracted, length: {len(content.get('full_text', ''))}, slot: {slot_num}"
    )

    available_days = []
    if "table_content" in content:
        for day, day_content in content["table_content"].items():
            day_lower = day.lower().strip()
            if day_lower == "all days":
                available_days = ["monday"]
                print(
                    "DEBUG: _process_slot - Single-lesson format detected, generating only Monday"
                )
                break
            elif day_lower in [
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
            ]:
                day_text = (
                    " ".join(day_content.values())
                    if isinstance(day_content, dict)
                    else str(day_content)
                )
                if day_text and day_text.strip().lower() not in [
                    "no school",
                    "n/a",
                    "",
                ]:
                    available_days.append(day_lower)
                    print(f"DEBUG: _process_slot - Day {day_lower} has content")

    if not available_days:
        available_days = None
        print(
            "DEBUG: _process_slot - No specific days detected, will generate all 5 days"
        )
    else:
        print(
            f"DEBUG: _process_slot - Generating content for days: {available_days}"
        )

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

    original_unit_lessons = {}
    original_objectives = {}

    if "table_content" in content:
        for day, day_content in content["table_content"].items():
            day_lower = day.lower()

            for label, text in day_content.items():
                label_lower = label.lower().strip()

                if day_lower not in original_unit_lessons:
                    if (
                        (
                            "unit" in label_lower
                            and ("lesson" in label_lower or "module" in label_lower)
                        )
                        or label_lower.startswith("unit")
                        or label_lower.startswith("lesson")
                    ):
                        original_unit_lessons[day_lower] = text
                        print(
                            f"DEBUG: Extracted unit/lesson for {day}: '{text[:50]}...'"
                        )

                if day_lower not in original_objectives:
                    if label_lower.startswith("objective"):
                        original_objectives[day_lower] = text
                        print(
                            f"DEBUG: Extracted objective for {day}: '{text[:50]}...'"
                        )

        print(
            f"DEBUG: Extracted {len(original_unit_lessons)} unit/lessons, {len(original_objectives)} objectives"
        )

    primary_content = content["full_text"]
    no_school_days = content.get("no_school_days", [])
    if no_school_days:
        print(f"DEBUG: _process_slot - No School days detected: {no_school_days}")

        no_school_days_normalized = {day.lower().strip() for day in no_school_days}
        initial_count = len(hyperlinks)

        links_without_day_hint = [h for h in hyperlinks if not h.get("day_hint")]

        hyperlinks = [
            h
            for h in hyperlinks
            if not h.get("day_hint")
            or h.get("day_hint", "").lower().strip()
            not in no_school_days_normalized
        ]

        filtered_count = initial_count - len(hyperlinks)

        if links_without_day_hint:
            logger.info(
                "hyperlinks_preserved_no_day_hint",
                extra={
                    "slot": slot["slot_number"],
                    "subject": slot["subject"],
                    "no_school_days": no_school_days,
                    "links_without_day_hint_count": len(links_without_day_hint),
                    "preserved_links": [
                        {
                            "text": h.get("text", "")[:50],
                            "section_hint": h.get("section_hint"),
                        }
                        for h in links_without_day_hint[:5]
                    ],
                },
            )

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

    primary_content = content.get("full_text", "")

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

        def llm_progress_callback(stage: str, llm_progress: int, message: str):
            slot_progress_min = 8
            slot_progress_max = 70
            slot_progress = slot_progress_min + int(
                (llm_progress - 10)
                / 80
                * (slot_progress_max - slot_progress_min)
            )
            update_slot_progress(stage, slot_progress, message)

        success, lesson_json, error = await asyncio.to_thread(
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

        print(
            f"DEBUG: _process_slot - LLM transform_lesson returned, success: {success}"
        )
        update_slot_progress(
            "processing", 70, "Processing transformation results..."
        )

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

        lesson_json.pop("_usage", {})
        lesson_json.pop("_model", "")
        lesson_json.pop("_provider", "")

        print(
            "DEBUG: _process_slot - Restoring original unit/lesson and objective content"
        )
        for day_lower, day_data in lesson_json.get("days", {}).items():
            if day_lower in original_unit_lessons:
                day_data["unit_lesson"] = original_unit_lessons[day_lower]
                print(f"DEBUG: Restored unit/lesson for {day_lower}")

            if day_lower in original_objectives and "objective" in day_data:
                day_data["objective"]["content_objective"] = original_objectives[
                    day_lower
                ]
                print(f"DEBUG: Restored objective content for {day_lower}")

        update_slot_progress("processing", 85, "Finalizing lesson plan...")
        if no_school_days:
            print(
                f"DEBUG: _process_slot - Replacing {len(no_school_days)} No School days in output"
            )
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
            print(
                f"[DEBUG] _process_slot (SEQUENTIAL): Adding {len(hyperlinks)} hyperlinks to lesson_json "
                f"for slot {slot.get('slot_number')}, subject {slot.get('subject')}"
            )
            lesson_json["_hyperlinks"] = hyperlinks
            logger.info(
                "sequential_hyperlinks_attached",
                extra={
                    "slot": slot.get("slot_number"),
                    "subject": slot.get("subject"),
                    "hyperlinks_count": len(hyperlinks),
                },
            )

            from tools.diagnostic_logger import get_diagnostic_logger

            diag = get_diagnostic_logger()
            diag.log_lesson_json_created(
                slot["slot_number"], slot["subject"], lesson_json
            )
        else:
            print(
                f"[WARN] _process_slot (SEQUENTIAL): No hyperlinks extracted for slot {slot.get('slot_number')}, "
                f"subject {slot.get('subject')}!"
            )
            logger.warning(
                "sequential_no_hyperlinks",
                extra={
                    "slot": slot.get("slot_number"),
                    "subject": slot.get("subject"),
                },
            )

        if images or hyperlinks:
            lesson_json["_media_schema_version"] = "2.0"

        if not isinstance(lesson_json, dict):
            if hasattr(lesson_json, "model_dump"):
                lesson_json = lesson_json.model_dump()
            elif hasattr(lesson_json, "dict"):
                lesson_json = lesson_json.dict()
            else:
                lesson_json = dict(lesson_json) if lesson_json else {}

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

            if slot.get("slot_number") == 2:
                print(f"DEBUG: Preserving Slot 2 Metadata -> Grade: '{lesson_json['metadata']['grade']}', Homeroom: '{lesson_json['metadata']['homeroom']}'")
        except Exception as e:
            print(f"DEBUG: Error copying slot metadata: {e}")
            traceback.print_exc()

        try:
            normalize_objectives_in_lesson(lesson_json)
        except Exception as e:
            print(f"DEBUG: Error in normalize_objectives_in_lesson: {e}")
            traceback.print_exc()

        del parser
        gc.collect()

        return lesson_json

    except Exception:
        raise

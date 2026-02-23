"""
Slot content extraction: resolve primary file, open DOCX with retry, extract slot content, parallel DB extraction.
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.progress import progress_tracker
from backend.telemetry import logger

from tools.docx_parser import DOCXParser

from tools.batch_processor_pkg.context import SlotProcessingContext
from tools.batch_processor_pkg.extraction_primary_file import resolve_primary_file
from tools.batch_processor_pkg.persistence import persist_original_lesson_plan as persistence_persist_original
from tools.batch_processor_pkg.slot_schema import sanitize_slot


async def open_docx_with_retry(
    processor: Any,
    file_path: str,
    plan_id: Optional[str] = None,
    slot_number: Optional[int] = None,
    subject: Optional[str] = None,
    max_retries: int = 3,
    initial_delay: float = 1.0,
) -> DOCXParser:
    """Open DOCX file with retry logic. Delegates to this module from orchestrator."""
    from docx.opc.exceptions import PackageNotFoundError

    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        error_msg = f"File not found: {file_path}" + (
            f" (Slot {slot_number}, {subject})" if slot_number and subject else ""
        )
        logger.error(
            "docx_file_not_found",
            extra={"file": file_path, "slot_number": slot_number, "subject": subject},
        )
        raise FileNotFoundError(error_msg)

    def _try_close_word_file(fp: Path) -> Tuple[bool, Optional[str]]:
        try:
            import sys
            if sys.platform != "win32":
                return False, "Word automation only available on Windows"
            try:
                import win32com.client
            except ImportError:
                return False, "pywin32 not installed (required for Word automation)"
            try:
                word_app = win32com.client.GetActiveObject("Word.Application")
            except Exception:
                return True, None
            file_path_abs = str(fp.resolve())
            document_closed = False
            for doc in word_app.Documents:
                try:
                    doc_path = str(Path(doc.FullName).resolve())
                    if doc_path.lower() == file_path_abs.lower():
                        doc.Close(SaveChanges=False)
                        document_closed = True
                        logger.info("word_file_closed", extra={"file": file_path, "slot_number": slot_number, "subject": subject})
                        break
                except Exception:
                    continue
            return True, "File closed in Word" if document_closed else None
        except Exception as e:
            logger.debug("word_automation_failed", extra={"file": file_path, "error": str(e), "error_type": type(e).__name__})
            return False, f"Word automation failed: {str(e)}"

    def _check_file_accessible(fp: Path) -> Tuple[bool, Optional[str]]:
        try:
            with open(fp, "a+b"):
                pass
            return True, None
        except PermissionError as e:
            close_result, close_msg = _try_close_word_file(fp)
            if close_result and close_msg:
                import time
                time.sleep(0.5)
                try:
                    with open(fp, "a+b"):
                        pass
                    return True, None
                except Exception:
                    pass
            return False, f"File is locked by another process (e.g., Microsoft Word): {str(e)}"
        except OSError as e:
            return False, f"File access error (possibly OneDrive syncing): {str(e)}"
        except Exception as e:
            return False, f"Unexpected error checking file: {str(e)}"

    last_error = None
    for attempt in range(max_retries):
        is_accessible, access_error = await asyncio.to_thread(_check_file_accessible, file_path_obj)
        if not is_accessible:
            if attempt < max_retries - 1:
                delay = initial_delay * (2**attempt)
                logger.warning(
                    "docx_file_not_accessible_retrying",
                    extra={"file": file_path, "attempt": attempt + 1, "max_retries": max_retries, "delay": delay, "slot_number": slot_number, "subject": subject, "error": access_error},
                )
                await asyncio.sleep(delay)
                continue
            logger.error("docx_file_not_accessible_final", extra={"file": file_path, "slot_number": slot_number, "subject": subject, "error": access_error})
            raise PermissionError(
                f"Cannot access file after {max_retries} attempts: {access_error}. "
                "Possible causes: File is open in Word; OneDrive is syncing; permissions; corrupted."
            )

        try:
            if plan_id:
                def _create_parser():
                    with processor.tracker.track_operation(plan_id, "parse_open_docx"):
                        return DOCXParser(file_path)
                parser = await asyncio.to_thread(_create_parser)
            else:
                parser = await asyncio.to_thread(DOCXParser, file_path)
            logger.info("docx_opened_successfully", extra={"file": file_path, "attempt": attempt + 1, "slot_number": slot_number, "subject": subject})
            return parser
        except PackageNotFoundError as e:
            last_error = e
            if attempt < max_retries - 1:
                close_result, close_msg = await asyncio.to_thread(_try_close_word_file, file_path_obj)
                if close_result and close_msg:
                    await asyncio.sleep(0.5)
                delay = initial_delay * (2**attempt)
                logger.warning(
                    "docx_package_not_found_retrying",
                    extra={"file": file_path, "attempt": attempt + 1, "max_retries": max_retries, "delay": delay, "slot_number": slot_number, "subject": subject, "error": str(e), "word_file_closed": close_result and close_msg},
                )
                await asyncio.sleep(delay)
                continue
            logger.error("docx_package_not_found_final", extra={"file": file_path, "slot_number": slot_number, "subject": subject, "error": str(e)})
            raise PackageNotFoundError(
                f"Cannot open DOCX file after {max_retries} attempts: {str(e)}\n\nFile: {file_path}"
                + (f"\nSlot: {slot_number} ({subject})" if slot_number and subject else "")
            )
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                delay = initial_delay * (2**attempt)
                logger.warning("docx_open_error_retrying", extra={"file": file_path, "attempt": attempt + 1, "max_retries": max_retries, "delay": delay, "slot_number": slot_number, "subject": subject, "error": str(e), "error_type": type(e).__name__})
                await asyncio.sleep(delay)
                continue
            logger.error("docx_open_error_final", extra={"file": file_path, "slot_number": slot_number, "subject": subject, "error": str(e), "error_type": type(e).__name__})
            raise

    raise Exception(f"Failed to open file after {max_retries} attempts: {last_error}")


async def extract_slot_content(
    processor: Any,
    context: SlotProcessingContext,
    week_of: str,
    week_folder_path: Optional[str] = None,
    user_base_path: Optional[str] = None,
    plan_id: Optional[str] = None,
) -> SlotProcessingContext:
    """Phase 1: Extract content from DOCX file (sequential, file I/O). Delegates from orchestrator."""
    slot = context.slot

    def update_extraction_progress(progress: int, message: str):
        if plan_id:
            overall_progress = int(progress * 0.20)
            progress_tracker.update(plan_id, "processing", overall_progress, message)

    slot = sanitize_slot(slot)
    context.slot = slot
    update_extraction_progress(5, f"Finding lesson plan file for {slot['subject']}...")

    if plan_id:
        def _resolve_with_tracking():
            try:
                with processor.tracker.track_operation(
                    plan_id,
                    "parse_resolve_file",
                    metadata={"slot_number": slot.get("slot_number"), "subject": slot["subject"], "week_of": week_of},
                ):
                    return processor._resolve_primary_file(slot, week_of, week_folder_path, user_base_path)
            except Exception as e:
                logger.error(f"Error in _resolve_with_tracking: {e}")
                raise
        primary_file = await asyncio.to_thread(_resolve_with_tracking)
    else:
        primary_file = processor._resolve_primary_file(slot, week_of, week_folder_path, user_base_path)

    if not primary_file:
        week_folder = Path(week_folder_path) if week_folder_path else Path(user_base_path or ".")
        teacher_pattern = (
            slot.get("primary_teacher_file_pattern")
            or slot.get("primary_teacher_name")
            or (f"{slot.get('primary_teacher_first_name', '')} {slot.get('primary_teacher_last_name', '')}".strip() if slot.get("primary_teacher_first_name") or slot.get("primary_teacher_last_name") else None)
        )
        error_msg = (
            f"No primary teacher file found for slot {slot['slot_number']} (subject: '{slot['subject']}').\n"
            f"Week folder: {week_folder} (exists: {week_folder.exists()})\n"
        )
        if teacher_pattern:
            error_msg += f"\nSearched for pattern: '{teacher_pattern}'\n"
        context.error = error_msg
        raise ValueError(error_msg)

    context.primary_file = primary_file
    update_extraction_progress(10, "Reading lesson plan document...")

    try:
        parser = await open_docx_with_retry(
            processor,
            primary_file,
            plan_id=plan_id,
            slot_number=slot.get("slot_number"),
            subject=slot.get("subject"),
        )
    except Exception as e:
        logger.error("docx_parser_init_failed", extra={"slot": slot["slot_number"], "subject": slot["subject"], "file": primary_file, "error": str(e)})
        context.error = f"Failed to open DOCX file: {str(e)}"
        raise

    if parser.is_no_school_day():
        logger.info("no_school_week_detected", extra={"slot": slot["slot_number"], "subject": slot["subject"], "file": primary_file})
        context.extracted_content = "__NO_SCHOOL_WEEK__"
        return context

    primary_first = slot.get("primary_teacher_first_name", "").strip()
    primary_last = slot.get("primary_teacher_last_name", "").strip()
    teacher_name = f"{primary_first} {primary_last}".strip() or slot.get("primary_teacher_name", "").strip()
    update_extraction_progress(15, "Locating slot in document...")

    try:
        if plan_id:
            _parser = parser
            def _find_slot_with_tracking():
                with processor.tracker.track_operation(plan_id, "parse_find_slot", metadata={"requested_slot": slot["slot_number"], "subject": slot["subject"]}):
                    return _parser.find_slot_by_subject(slot["subject"], teacher_name, slot.get("homeroom"), slot.get("grade"))
            slot_num = await asyncio.to_thread(_find_slot_with_tracking)
        else:
            slot_num = await asyncio.to_thread(parser.find_slot_by_subject, slot["subject"], teacher_name, slot.get("homeroom"), slot.get("grade"))
    except ValueError:
        slot_num = slot["slot_number"]

    update_extraction_progress(18, "Extracting images and hyperlinks...")
    try:
        if plan_id:
            _parser = parser
            def _extract_media_with_tracking():
                with processor.tracker.track_operation(plan_id, "parse_extract_images", metadata={"slot_number": slot_num, "subject": slot["subject"]}):
                    images_result = _parser.extract_images_for_slot(slot_num)
                with processor.tracker.track_operation(plan_id, "parse_extract_hyperlinks", metadata={"slot_number": slot_num, "subject": slot["subject"]}):
                    hyperlinks_result = _parser.extract_hyperlinks_for_slot(slot_num)
                return images_result, hyperlinks_result
            images, hyperlinks = await asyncio.to_thread(_extract_media_with_tracking)
        else:
            images = await asyncio.to_thread(parser.extract_images_for_slot, slot_num)
            hyperlinks = await asyncio.to_thread(parser.extract_hyperlinks_for_slot, slot_num)
    except Exception as e:
        logger.error("media_extraction_failed", extra={"error": str(e)})
        images = []
        hyperlinks = []

    update_extraction_progress(20, "Extracting lesson content...")
    if plan_id:
        _parser = parser
        def _extract_content_with_tracking():
            with processor.tracker.track_operation(plan_id, "parse_extract_content", metadata={"slot_number": slot_num, "subject": slot["subject"]}):
                return _parser.extract_subject_content_for_slot(slot_num, slot["subject"], teacher_name, strip_urls=False)
        content = await asyncio.to_thread(_extract_content_with_tracking)
    else:
        content = await asyncio.to_thread(
            parser.extract_subject_content_for_slot, slot_num, slot["subject"], teacher_name, strip_urls=False
        )

    available_days = []
    if "table_content" in content:
        for day, day_content in content["table_content"].items():
            day_lower = day.lower().strip()
            if day_lower == "all days":
                available_days = ["monday"]
                break
            elif day_lower in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
                day_text = " ".join(day_content.values()) if isinstance(day_content, dict) else str(day_content)
                if day_text and day_text.strip().lower() not in ["no school", "n/a", ""]:
                    available_days.append(day_lower)
    if not available_days:
        available_days = None

    primary_content = content.get("full_text", "")
    context.slot["_extracted_images"] = images
    context.slot["_extracted_hyperlinks"] = hyperlinks
    context.slot["_extracted_content_dict"] = content

    await persistence_persist_original(
        processor.db,
        getattr(processor, "_current_user_id", ""),
        slot,
        week_of,
        primary_file,
        teacher_name,
        content,
        hyperlinks,
        available_days,
        plan_id,
    )

    context.extracted_content = primary_content
    context.available_days = available_days
    logger.info("parallel_extract_slot_content_hyperlinks_stored", extra={"slot": slot["slot_number"], "subject": slot["subject"], "hyperlinks_count": len(hyperlinks)})
    return context


async def extract_slots_parallel_db(
    processor: Any,
    slots: List[Dict[str, Any]],
    week_of: str,
    week_folder_path: Optional[str],
    user_base_path: Optional[str],
    plan_id: Optional[str],
    progress_tracker_ref: Any,
) -> List[SlotProcessingContext]:
    """Parallel extraction using DB cache and file grouping. Delegates from orchestrator."""
    file_to_slots = {}
    for i, slot in enumerate(slots, 1):
        slot = sanitize_slot(slot)
        primary_file = processor._resolve_primary_file(slot, week_of, week_folder_path, user_base_path)
        key = primary_file if primary_file else "None"
        if key not in file_to_slots:
            file_to_slots[key] = []
        file_to_slots[key].append((i, slot))

    semaphore = asyncio.Semaphore(3)
    tasks = []
    for file_path_key, group in file_to_slots.items():
        file_path = None if file_path_key == "None" else file_path_key
        tasks.append(
            processor._process_file_group(
                file_path, group, week_of, week_folder_path, user_base_path, plan_id, semaphore
            )
        )

    results = await asyncio.gather(*tasks)
    flattened_contexts = []
    for group_contexts in results:
        flattened_contexts.extend(group_contexts)
    return sorted(flattened_contexts, key=lambda x: x.slot_index)

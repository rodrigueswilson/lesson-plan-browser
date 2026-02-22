"""
Slot detection, media extraction, and content extraction for single-slot flow.
Used by slot_flow.process_one_slot.
"""

import asyncio
import gc
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.telemetry import logger


def get_available_slots(parser: Any) -> int:
    """Compute number of available slots from document tables (signature table excluded)."""
    total_tables = len(parser.doc.tables)
    has_signature = False
    if total_tables > 0:
        last_table = parser.doc.tables[-1]
        if last_table.rows and last_table.rows[0].cells:
            first_cell = last_table.rows[0].cells[0].text.strip().lower()
            if "signature" in first_cell or "required signatures" in first_cell:
                has_signature = True
    if has_signature:
        return (total_tables - 1) // 2
    return total_tables // 2


def log_table_structure(parser: Any, slot: dict, primary_file: str) -> None:
    """Log document table structure for debugging."""
    total_tables = len(parser.doc.tables)
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


def get_teacher_name(slot: dict) -> str:
    """Build primary teacher name from slot."""
    primary_first = slot.get("primary_teacher_first_name", "").strip()
    primary_last = slot.get("primary_teacher_last_name", "").strip()
    return (
        f"{primary_first} {primary_last}".strip()
        or slot.get("primary_teacher_name", "").strip()
    )


async def find_slot_number(
    processor: Any,
    parser: Any,
    slot: dict,
    primary_file: str,
    plan_id: Optional[str],
) -> int:
    """Find actual slot number for subject (subject-based detection). Returns slot_num."""
    available_slots = get_available_slots(parser)
    requested_slot = slot["slot_number"]
    print(
        f"DEBUG: _process_slot - Document has {available_slots} available slots, requested: {requested_slot}"
    )
    log_table_structure(parser, slot, primary_file)
    teacher_name = get_teacher_name(slot)
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
        return actual_slot_num
    except ValueError:
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
            return 1
        print(
            f"DEBUG: _process_slot - Using requested slot {slot['slot_number']} as fallback (validated: {available_slots} slots available)"
        )
        return slot["slot_number"]


async def extract_media_for_slot(
    processor: Any,
    parser: Any,
    slot_num: int,
    slot: dict,
    primary_file: str,
    plan_id: Optional[str],
) -> Tuple[List[Any], List[Dict[str, Any]]]:
    """Extract images and hyperlinks for the slot. On non-ValueError exception returns ([], [])."""
    try:
        if plan_id:
            _parser = parser

            def _extract_media_with_tracking():
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
                    hyperlinks_result = _parser.extract_hyperlinks_for_slot(slot_num)
                return images_result, hyperlinks_result
            images, hyperlinks = await asyncio.to_thread(_extract_media_with_tracking)
        else:
            images = await asyncio.to_thread(parser.extract_images_for_slot, slot_num)
            hyperlinks = await asyncio.to_thread(
                parser.extract_hyperlinks_for_slot, slot_num
            )
        print(
            f"[DEBUG] _process_slot (SEQUENTIAL): Extracted {len(images)} images, {len(hyperlinks)} hyperlinks "
            f"for slot {slot['slot_number']}, subject {slot['subject']}"
        )
        try:
            from tools.diagnostic_logger import get_diagnostic_logger
            diag = get_diagnostic_logger()
            diag.log_hyperlinks_extracted(
                slot["slot_number"], slot["subject"], hyperlinks, primary_file
            )
        except ImportError:
            pass
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
        return images, hyperlinks
    except ValueError:
        logger.error(
            "slot_structure_invalid",
            extra={
                "slot": slot_num,
                "subject": slot["subject"],
                "file": primary_file,
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
        return [], []


def build_no_school_day_json(
    week_of: str, slot: dict, hyperlinks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Build minimal lesson JSON for no-school day (entire document)."""
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
    return no_school_json


async def extract_content_for_slot(
    processor: Any,
    parser: Any,
    slot_num: int,
    slot: dict,
    teacher_name: str,
    plan_id: Optional[str],
) -> Dict[str, Any]:
    """Extract subject content for the slot. Returns content dict with full_text, table_content, no_school_days."""
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
    return content


def get_available_days_from_content(content: Dict[str, Any]) -> Optional[List[str]]:
    """Derive available_days from content table_content. Returns None for all 5 days."""
    available_days = []
    if "table_content" not in content:
        return None
    for day, day_content in content["table_content"].items():
        day_lower = day.lower().strip()
        if day_lower == "all days":
            return ["monday"]
        if day_lower in [
            "monday", "tuesday", "wednesday", "thursday", "friday"
        ]:
            day_text = (
                " ".join(day_content.values())
                if isinstance(day_content, dict)
                else str(day_content)
            )
            if day_text and day_text.strip().lower() not in ["no school", "n/a", ""]:
                available_days.append(day_lower)
    if not available_days:
        return None
    return available_days


def build_no_school_week_json(processor: Any, slot: dict, week_of: str) -> Dict[str, Any]:
    """Build minimal lesson JSON for no-school week (entire document)."""
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


def get_original_unit_lessons_and_objectives(
    content: Dict[str, Any],
) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Extract original unit/lesson and objective text per day from table_content."""
    original_unit_lessons = {}
    original_objectives = {}
    if "table_content" not in content:
        return original_unit_lessons, original_objectives
    for day, day_content in content["table_content"].items():
        day_lower = day.lower()
        for label, text in day_content.items():
            label_lower = label.lower().strip()
            if day_lower not in original_unit_lessons:
                if (
                    ("unit" in label_lower and ("lesson" in label_lower or "module" in label_lower))
                    or label_lower.startswith("unit")
                    or label_lower.startswith("lesson")
                ):
                    original_unit_lessons[day_lower] = text
            if day_lower not in original_objectives:
                if label_lower.startswith("objective"):
                    original_objectives[day_lower] = text
    return original_unit_lessons, original_objectives

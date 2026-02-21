"""
Persistence subdomain: save original lesson plan data to the database.
"""
import asyncio
import hashlib
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.telemetry import logger

from tools.batch_processor_pkg.slot_schema import map_day_content_to_schema


async def persist_original_lesson_plan(
    db: Any,
    user_id: str,
    slot: Dict[str, Any],
    week_of: str,
    primary_file: str,
    teacher_name: str,
    content: Dict[str, Any],
    hyperlinks: List[Dict[str, Any]],
    available_days: Optional[List[str]],
    plan_id: Optional[str] = None,
) -> Optional[str]:
    """Persist original lesson plan data to the database.

    Args:
        db: Database instance (create_original_lesson_plan).
        user_id: Current user ID.
        slot: Slot dict (slot_number, subject, grade, homeroom, etc.).
        week_of: Week date range.
        primary_file: Path to the primary DOCX file.
        teacher_name: Primary teacher name.
        content: Extracted content dict (table_content, full_text).
        hyperlinks: List of hyperlink dicts (with day_hint).
        available_days: List of days with content.
        plan_id: Optional plan ID (unused in record; for future use).

    Returns:
        Created record ID, or None on failure.
    """
    try:
        structured_days = {}
        if "table_content" in content:
            for day, day_data in content["table_content"].items():
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
                        if h.get("day_hint", "").lower().strip() == day_lower
                    ]
                    structured_days[f"{day_lower}_content"] = map_day_content_to_schema(
                        day_data, slot, day_hyperlinks=day_links
                    )

        unique_str = f"{user_id}_{week_of}_{slot['slot_number']}_{slot['subject']}"
        stable_id = f"orig_{hashlib.md5(unique_str.encode()).hexdigest()}"

        original_plan_data = {
            "id": stable_id,
            "user_id": user_id,
            "week_of": week_of,
            "slot_number": slot["slot_number"],
            "subject": slot["subject"],
            "grade": slot.get("grade") or "N/A",
            "homeroom": slot.get("homeroom"),
            "source_file_path": str(primary_file),
            "source_file_name": Path(primary_file).name,
            "primary_teacher_name": teacher_name,
            "content_json": content,
            "full_text": content.get("full_text", ""),
            "available_days": available_days,
            "status": "extracted",
            "has_no_school": not available_days or len(available_days) == 0,
            **structured_days,
        }

        print(
            f"DEBUG: Saving OriginalLessonPlan for slot {slot['slot_number']} to DB..."
        )

        def _save_original():
            return db.create_original_lesson_plan(original_plan_data)

        res_id = await asyncio.to_thread(_save_original)
        print(f"DEBUG: OriginalLessonPlan saved with ID: {res_id}")
        return res_id

    except Exception as e:
        logger.error(
            "original_lesson_plan_persistence_failed",
            extra={"error": str(e), "slot": slot["slot_number"]},
        )
        print(f"ERROR: Persistence failed for slot {slot['slot_number']}: {e}")
        traceback.print_exc()
        return None

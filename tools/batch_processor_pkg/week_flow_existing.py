"""
Load existing plan for week and apply missing_only slot filtering.
"""
import asyncio
import json
from typing import Any, Dict, List, Optional, Tuple

from backend.telemetry import logger
from backend.utils.lesson_json_enricher import enrich_lesson_json_from_steps


async def load_existing_plan(
    db: Any,
    user_id: str,
    week_of: str,
    plan_id: Optional[str],
    slots: List[Dict[str, Any]],
    missing_only: bool,
    partial: bool,
) -> Tuple[Optional[Dict], Optional[str], List[Dict[str, Any]], bool]:
    """
    Load existing plan for this week; optionally filter slots to missing only.
    Returns (existing_lesson_json, plan_id, slots, partial).
    slots may be filtered in place when missing_only is True.
    partial is set to False when no existing plan is found.
    """
    existing_lesson_json = None
    existing_plans = await asyncio.to_thread(db.get_user_plans, user_id, limit=5)
    existing_plan = next((p for p in existing_plans if p.week_of == week_of), None)

    if existing_plan:
        if not plan_id:
            plan_id = existing_plan.id

        existing_lesson_json = existing_plan.lesson_json
        if isinstance(existing_lesson_json, str):
            try:
                existing_lesson_json = json.loads(existing_lesson_json)
            except Exception:
                existing_lesson_json = None

        if existing_lesson_json:
            existing_lesson_json = enrich_lesson_json_from_steps(
                existing_lesson_json, existing_plan.id, db
            )
            logger.info(
                "skip_logic_plan_found",
                extra={
                    "plan_id": existing_plan.id,
                    "status": "valid_json_loaded",
                    "week_of": week_of,
                },
            )
            if missing_only:
                existing_slots_data = []
                for day in existing_lesson_json.get("days", {}).values():
                    existing_slots_data.extend(day.get("slots", []))
                existing_slot_numbers = {
                    s.get("slot_number")
                    for s in existing_slots_data
                    if s.get("slot_number") is not None
                }
                slots = [s for s in slots if s.get("slot_number") not in existing_slot_numbers]
        else:
            logger.info(
                "skip_logic_plan_invalid",
                extra={
                    "plan_id": existing_plan.id,
                    "status": "json_empty_or_invalid",
                    "week_of": week_of,
                },
            )
    else:
        logger.info(
            "skip_logic_no_plan",
            extra={"status": "plan_not_found_in_db", "week_of": week_of},
        )
        partial = False
        missing_only = False

    return (existing_lesson_json, plan_id, slots, partial)

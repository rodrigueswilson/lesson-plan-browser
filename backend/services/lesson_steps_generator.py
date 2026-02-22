"""
Core logic for generating lesson steps from a plan phase_plan and slot data.
"""
import json
from typing import List, Optional

from fastapi import HTTPException

from backend.schema import LessonStep
from backend.services.lesson_steps import (
    phase_steps,
    plan_resolve,
    slot_data,
    vocab_frames_steps,
)
from backend.telemetry import logger


def generate_lesson_steps(
    plan_id: str,
    day: str,
    slot: int,
    current_user_id: Optional[str] = None,
) -> List[LessonStep]:
    plan, db_for_plan = plan_resolve.resolve_plan_and_db(
        plan_id, day, slot, current_user_id
    )

    # Get lesson JSON
    lesson_json = plan.lesson_json
    if isinstance(lesson_json, str):
        try:
            lesson_json = json.loads(lesson_json)
        except json.JSONDecodeError:
            logger.error(
                "lesson_json_parse_failed",
                extra={"plan_id": plan_id, "error": "Invalid JSON"},
            )
            lesson_json = {}

    if not lesson_json:
        logger.error(
            "lesson_json_missing",
            extra={
                "plan_id": plan_id,
                "has_lesson_json_field": hasattr(plan, "lesson_json"),
            },
        )
        raise HTTPException(status_code=400, detail="Plan has no lesson JSON data")

    logger.info(
        "lesson_json_loaded",
        extra={
            "plan_id": plan_id,
            "has_days": "days" in lesson_json,
            "days_keys": list(lesson_json.get("days", {}).keys())
            if "days" in lesson_json
            else [],
        },
    )

    extracted = slot_data.extract_slot_data(lesson_json, plan_id, day, slot)
    if extracted is None:
        return []

    day_data, slot_data_val, phase_plan, tailored_instruction = extracted

    # Delete existing steps for this lesson
    deleted_count = db_for_plan.delete_lesson_steps(
        plan_id, day_of_week=day, slot_number=slot
    )
    logger.info(
        "existing_steps_deleted",
        extra={
            "plan_id": plan_id,
            "day": day,
            "slot": slot,
            "deleted_count": deleted_count,
        },
    )

    generated_steps = []
    start_time_offset = phase_steps.generate_phase_steps(
        phase_plan, plan_id, day, slot, db_for_plan, generated_steps
    )

    vocabulary_cognates = (
        slot_data_val.get("vocabulary_cognates")
        or day_data.get("vocabulary_cognates")
        or []
    )
    day_sentence_frames = (
        slot_data_val.get("sentence_frames") or day_data.get("sentence_frames") or []
    )
    vocab_frames_steps.add_vocab_and_frames_steps(
        vocabulary_cognates,
        day_sentence_frames,
        tailored_instruction,
        len(phase_plan),
        plan_id,
        day,
        slot,
        start_time_offset,
        db_for_plan,
        generated_steps,
    )

    logger.info(
        "checking_generated_steps",
        extra={
            "plan_id": plan_id,
            "in_memory_count": len(generated_steps),
            "phase_plan_count": len(phase_plan),
        },
    )

    if generated_steps:
        logger.info(
            "lesson_steps_generated_in_memory",
            extra={
                "count": len(generated_steps),
                "details": "Table missing, returning in-memory steps",
            },
        )
        return generated_steps

    # Fetch from database
    steps = db_for_plan.get_lesson_steps(plan_id, day_of_week=day, slot_number=slot)
    logger.info(
        "lesson_steps_fetched_from_database",
        extra={
            "plan_id": plan_id,
            "count": len(steps),
            "steps_type": str(type(steps)) if steps else "empty",
        },
    )

    return steps

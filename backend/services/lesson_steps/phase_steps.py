"""
Build and persist phase steps from phase_plan; shared persist helper for table-missing fallback.
"""
import uuid
from datetime import datetime
from typing import Any, List

from backend.schema import LessonStep
from backend.telemetry import logger

DEFAULT_PHASES = [
    {
        "phase_name": "Warmup",
        "minutes": 5,
        "content_type": "instruction",
        "details": "Engage students with a brief activity to activate prior knowledge and prepare them for the lesson.",
    },
    {
        "phase_name": "Input",
        "minutes": 15,
        "content_type": "instruction",
        "details": "Present new content, concepts, or skills to students. This is the main teaching phase of the lesson.",
    },
    {
        "phase_name": "Practice",
        "minutes": 20,
        "content_type": "instruction",
        "details": "Students practice the new skills or concepts with teacher support and then independently.",
    },
    {
        "phase_name": "Closure",
        "minutes": 5,
        "content_type": "assessment",
        "details": "Wrap up the lesson by reviewing key concepts, checking for understanding, and preparing for the next lesson.",
    },
]


def persist_step(
    step_data: dict,
    db_for_plan: Any,
    generated_steps: List[LessonStep],
) -> None:
    """
    Create lesson step in DB, or append to generated_steps if lesson_steps table is missing.
    Raises for any other error.
    """
    try:
        db_for_plan.create_lesson_step(step_data)
    except Exception as create_error:
        error_type = type(create_error).__name__
        error_msg = str(create_error)
        is_table_missing = (
            error_type == "LessonStepsTableMissingError"
            or "lesson_steps table does not exist" in error_msg
            or "PGRST205" in error_msg
            or "Could not find the table" in error_msg
            or "lesson_steps" in error_msg.lower()
        )
        if is_table_missing:
            step_data_with_timestamps = {
                **step_data,
                "created_at": datetime.utcnow(),
                "updated_at": None,
            }
            generated_steps.append(LessonStep(**step_data_with_timestamps))
            logger.info(
                "step_stored_in_memory",
                extra={
                    "plan_id": step_data.get("lesson_plan_id"),
                    "step_name": step_data.get("step_name"),
                    "reason": "table missing (exception caught)",
                    "generated_steps_count": len(generated_steps),
                },
            )
        else:
            raise


def generate_phase_steps(
    phase_plan: List[dict],
    plan_id: str,
    day: str,
    slot: int,
    db_for_plan: Any,
    generated_steps: List[LessonStep],
) -> int:
    """
    Generate and persist steps for each phase in phase_plan (or use DEFAULT_PHASES if empty).
    Returns start_time_offset after the last phase.
    """
    if not phase_plan:
        logger.warning(
            "phase_plan_missing_using_defaults",
            extra={"plan_id": plan_id, "day": day, "slot": slot},
        )
        phase_plan = DEFAULT_PHASES

    start_time_offset = 0
    for idx, phase in enumerate(phase_plan, start=1):
        step_id = str(uuid.uuid4())
        content_type = phase.get("content_type", "instruction")
        step_name = phase.get("phase_name", f"Step {idx}")
        duration = phase.get("minutes", phase.get("duration_minutes", 5))
        if duration == 0 or duration is None:
            duration = 5
            logger.warning(
                "lesson_step_zero_duration_fixed",
                extra={
                    "plan_id": plan_id,
                    "day": day,
                    "slot": slot,
                    "step_name": step_name,
                },
            )

        bilingual_role = phase.get("bilingual_teacher_role", "")
        primary_role = phase.get("primary_teacher_role", "")
        details = phase.get("details", "")
        display_content_parts = []
        if bilingual_role:
            display_content_parts.append(f"Bilingual Teacher: {bilingual_role}")
        if primary_role:
            display_content_parts.append(f"Primary Teacher: {primary_role}")
        if details:
            display_content_parts.append(details)
        display_content = (
            "\n\n".join(display_content_parts) if display_content_parts else ""
        )
        sentence_frames = phase.get("sentence_frames", [])
        materials = phase.get("materials", [])

        step_data = {
            "id": step_id,
            "lesson_plan_id": plan_id,
            "day_of_week": day.lower(),
            "slot_number": slot,
            "step_number": idx,
            "step_name": step_name,
            "duration_minutes": duration,
            "start_time_offset": start_time_offset,
            "content_type": content_type,
            "display_content": display_content,
            "hidden_content": [],
            "sentence_frames": sentence_frames,
            "materials_needed": materials,
        }

        persist_step(step_data, db_for_plan, generated_steps)
        logger.debug(
            "step_created_in_database",
            extra={"plan_id": plan_id, "step_name": step_name, "step_id": step_id},
        )
        start_time_offset += duration

    return start_time_offset

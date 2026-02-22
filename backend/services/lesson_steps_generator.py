"""
Core logic for generating lesson steps from a plan phase_plan and slot data.
"""
import json
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException

from backend.config import settings
from backend.schema import LessonStep
from backend.services.lesson_steps import phase_steps, plan_resolve, slot_data
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

    # ============================================================================
    # VOCABULARY/COGNATES AND SENTENCE FRAMES STEP GENERATION
    # ============================================================================
    #
    # CRITICAL: vocabulary_cognates and sentence_frames should be present in
    # lesson_json under days[day]["slots"][slot_number]. If these are missing
    # or empty arrays, vocabulary/frames steps will NOT be created.
    #
    # Expected structure in lesson_json:
    #   days[day]["slots"][slot_number]["vocabulary_cognates"] = [
    #     {"english": "...", "portuguese": "...", "is_cognate": bool, "relevance_note": "..."}
    #   ]
    #   days[day]["slots"][slot_number]["sentence_frames"] = [
    #     {"english": "...", "portuguese": "...", "proficiency_level": "...", ...}
    #   ]
    #
    # If vocabulary/frames are missing, check:
    #   1. The source JSON file during plan creation/import
    #   2. Whether the plan's lesson_json was properly populated
    #   3. Use update_plan_supabase.py script to fix missing data
    #
    # Fallback: We check both slot-level and day-level data for backwards
    # compatibility with legacy plans that stored vocabulary/frames at day level.
    # ============================================================================

    # Get vocabulary and sentence frames from slot-level (preferred) or day-level (fallback)
    vocabulary_cognates = (
        slot_data_val.get("vocabulary_cognates")
        or day_data.get("vocabulary_cognates")
        or []
    )
    day_sentence_frames = (
        slot_data_val.get("sentence_frames") or day_data.get("sentence_frames") or []
    )

    # Validate: Warn if vocabulary/frames are missing when they should be present
    # This helps catch cases where lesson_json was not properly populated
    if not vocabulary_cognates and not day_sentence_frames:
        logger.warning(
            "vocabulary_frames_missing",
            extra={
                "plan_id": plan_id,
                "day": day,
                "slot": slot,
                "warning": (
                    "No vocabulary_cognates or sentence_frames found in lesson_json. "
                    "Vocabulary/frames steps will not be created. "
                    "If this plan should have vocabulary/frames, check the source JSON "
                    "or use update_plan_supabase.py to fix the plan's lesson_json."
                ),
            },
        )

    logger.info(
        f"DEBUG: Generating steps for slot {slot}. Vocab count: {len(vocabulary_cognates)}. Frames count: {len(day_sentence_frames)}"
    )
    print(
        f"[DEBUG] Vocabulary check: vocabulary_cognates exists={bool(vocabulary_cognates)}, type={type(vocabulary_cognates)}, length={len(vocabulary_cognates) if isinstance(vocabulary_cognates, list) else 'N/A'}"
    )
    logger.info(
        "vocabulary_cognates_check",
        extra={
            "plan_id": plan_id,
            "has_vocabulary_cognates": bool(vocabulary_cognates),
            "is_list": isinstance(vocabulary_cognates, list),
            "length": len(vocabulary_cognates)
            if isinstance(vocabulary_cognates, list)
            else 0,
        },
    )

    # Create Vocabulary / Cognate Awareness step if vocabulary_cognates exists
    # NOTE: This step is ONLY created if vocabulary_cognates is a non-empty list.
    # If vocabulary_cognates is None or [], no vocabulary step will be created.
    if vocabulary_cognates:
        # Build simple bullet-style lines from the six pairs.
        lines: list[str] = []
        for pair in vocabulary_cognates:
            if not isinstance(pair, dict):
                continue
            english = str(pair.get("english", "")).strip()
            portuguese = str(pair.get("portuguese", "")).strip()
            if not english or not portuguese:
                continue
            # Use a simple, plain-text arrow separator for the lesson browser
            lines.append(f"- {english} -> {portuguese}")

        if lines:
            vocab_step_id = str(uuid.uuid4())
            vocab_step_number = len(phase_plan) + 1

            # Extract implementation strategy for Cognate Awareness if available
            ell_support = tailored_instruction.get("ell_support") or []
            vocab_strategy_text = ""
            if isinstance(ell_support, list):
                for s in ell_support:
                    if isinstance(s, dict):
                        strategy_id = s.get("strategy_id", "").lower()
                        strategy_name = str(s.get("strategy_name", "")).lower()
                        # Match by ID or name
                        if (
                            strategy_id == "cognate_awareness"
                            or "cognate" in strategy_name
                        ):
                            vocab_strategy_text = s.get(
                                "implementation", ""
                            ) or s.get("implementation_steps", "")
                            if vocab_strategy_text:
                                # If implementation_steps is a list, join it
                                if isinstance(vocab_strategy_text, list):
                                    vocab_strategy_text = "\n".join(
                                        vocab_strategy_text
                                    )
                                break

            display_content = "\n".join(lines)
            if vocab_strategy_text:
                display_content = f"{vocab_strategy_text}\n\n{display_content}"

            vocab_step = {
                "id": vocab_step_id,
                "lesson_plan_id": plan_id,
                "day_of_week": day.lower(),
                "slot_number": slot,
                "step_number": vocab_step_number,
                "step_name": "Vocabulary / Cognate Awareness",
                "duration_minutes": 5,
                "start_time_offset": start_time_offset,
                "content_type": "instruction",
                "display_content": display_content,
                "hidden_content": [],
                "sentence_frames": [],
                "materials_needed": [],
                "vocabulary_cognates": json.dumps(vocabulary_cognates)
                if settings.USE_SUPABASE
                else vocabulary_cognates,  # Include structured data for frontend
            }

        # DEBUG: Log vocabulary_cognates before saving
        print(
            f"[DEBUG] vocab_step vocabulary_cognates: type={type(vocabulary_cognates)}, value={vocabulary_cognates}, length={len(vocabulary_cognates) if isinstance(vocabulary_cognates, list) else 'N/A'}"
        )
        logger.info(
            "vocab_step_before_save",
            extra={
                "plan_id": plan_id,
                "vocab_type": str(type(vocabulary_cognates)),
                "vocab_is_list": isinstance(vocabulary_cognates, list),
                "vocab_length": len(vocabulary_cognates)
                if isinstance(vocabulary_cognates, list)
                else 0,
                "vocab_sample": vocabulary_cognates[0]
                if isinstance(vocabulary_cognates, list)
                and len(vocabulary_cognates) > 0
                else None,
            },
        )

        try:
            created_id = db_for_plan.create_lesson_step(vocab_step)
            logger.debug(
                "Vocab step created in database", extra={"step_id": created_id}
            )
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
                vocab_step_with_timestamps = {
                    **vocab_step,
                    "created_at": datetime.utcnow(),
                    "updated_at": None,
                }
                generated_steps.append(LessonStep(**vocab_step_with_timestamps))
                logger.debug("Stored vocab step in memory (table missing)")
                print(
                    f"[DEBUG] Vocab step stored in memory, total steps: {len(generated_steps)}"
                )
            else:
                raise
        start_time_offset += 5

    # Append a sentence-frames step sourced from slot-level
    # sentence_frames when available, falling back to any legacy
    # day-level sentence_frames.
    # NOTE: This step is ONLY created if sentence_frames is a non-empty list.
    # If sentence_frames is None or [], no sentence frames step will be created.
    if day_sentence_frames:
        import uuid

        frames_step_id = str(uuid.uuid4())
        # Place it after existing steps (phase_plan + optional vocab)
        existing_steps = db_for_plan.get_lesson_steps(
            plan_id, day_of_week=day, slot_number=slot
        )
        next_step_number = (
            (existing_steps[-1].step_number + 1)
            if existing_steps
            else (len(phase_plan) + 1)
        )

        # Extract implementation strategy for Sentence Frames if available
        ell_support = tailored_instruction.get("ell_support") or []
        frames_strategy_text = ""
        if isinstance(ell_support, list):
            for s in ell_support:
                if isinstance(s, dict):
                    strategy_id = s.get("strategy_id", "").lower()
                    strategy_name = str(s.get("strategy_name", "")).lower()
                    # Match by ID or name
                    if (
                        strategy_id == "sentence_frames"
                        or "sentence frames" in strategy_name
                        or "sentence frame" in strategy_name
                    ):
                        frames_strategy_text = s.get("implementation", "") or s.get(
                            "implementation_steps", ""
                        )
                        if frames_strategy_text:
                            # If implementation_steps is a list, join it
                            if isinstance(frames_strategy_text, list):
                                frames_strategy_text = "\n".join(
                                    frames_strategy_text
                                )
                            break

        # Create display content for sentence frames
        # Combine strategy text with the actual frames for robust display
        frames_display_parts = []
        if frames_strategy_text:
            frames_display_parts.append(frames_strategy_text)

        if day_sentence_frames:
            frames_display_parts.append("\nReference Frames:")
            for frame in day_sentence_frames:
                if isinstance(frame, dict):
                    english = frame.get("english", "")
                    if english:
                        frames_display_parts.append(f"- {english}")

        frames_display_content = (
            "\n\n".join(frames_display_parts)
            if frames_display_parts
            else frames_strategy_text
        )

        frames_step = {
            "id": frames_step_id,
            "lesson_plan_id": plan_id,
            "day_of_week": day.lower(),
            "slot_number": slot,
            "step_number": next_step_number,
            "step_name": "Sentence Frames / Stems / Questions",
            "duration_minutes": 5,
            "start_time_offset": start_time_offset,
            "content_type": "sentence_frames",
            "display_content": frames_display_content,
            "hidden_content": [],
            "sentence_frames": day_sentence_frames,
            "materials_needed": [],
        }

        try:
            created_id = db_for_plan.create_lesson_step(frames_step)
            logger.debug(
                "Frames step created in database", extra={"step_id": created_id}
            )
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
                frames_step_with_timestamps = {
                    **frames_step,
                    "created_at": datetime.utcnow(),
                    "updated_at": None,
                }
                generated_steps.append(LessonStep(**frames_step_with_timestamps))
                logger.debug("Stored frames step in memory (table missing)")
                print(
                    f"[DEBUG] Frames step stored in memory, total steps: {len(generated_steps)}"
                )
            else:
                raise
        start_time_offset += 5

    # If we have in-memory steps (table doesn't exist), return those
    # Otherwise, fetch from database
    print(
        f"[DEBUG] Checking generated_steps: count={len(generated_steps)}, phase_plan_count={len(phase_plan)}"
    )
    print(
        f"[DEBUG] generated_steps type: {type(generated_steps)}, is_list: {isinstance(generated_steps, list)}"
    )
    if generated_steps:
        print(
            f"[DEBUG] generated_steps contents: {[s.step_name if hasattr(s, 'step_name') else str(s)[:50] for s in generated_steps]}"
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
        print(f"[DEBUG] Returning {len(generated_steps)} in-memory steps")
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

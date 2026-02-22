"""
Core logic for generating lesson steps from a plan phase_plan and slot data.
"""
import json
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException

from backend.authorization import verify_user_access
from backend.config import settings
from backend.database import get_db
from backend.schema import LessonStep
from backend.telemetry import logger


def generate_lesson_steps(
    plan_id: str,
    day: str,
    slot: int,
    current_user_id: Optional[str] = None,
) -> List[LessonStep]:
    # Find the plan across projects (we only need to locate it)
    plan = None

    # Try to get plan using current_user_id's database first
    if current_user_id:
        db = get_db(user_id=current_user_id)
        plan = db.get_weekly_plan(plan_id)

    # [REGENERATION FIX] Delete existing steps for this specific plan/day/slot
    # to prevent stale data or duplicates when the user triggers regeneration.
    try:
        logger.info(
            "clearing_existing_steps_before_regeneration",
            extra={"plan_id": plan_id, "day": day, "slot": slot},
        )
        # Find the database again to ensure we have the right one for deletion
        db_to_clear = (
            get_db(user_id=current_user_id) if current_user_id else get_db()
        )
        db_to_clear.delete_lesson_steps(
            plan_id, day_of_week=day.lower(), slot_number=slot
        )
    except Exception as e:
        logger.warning(
            "failed_to_clear_steps_before_regeneration", extra={"error": str(e)}
        )

    # If not found and using Supabase, try both projects
    if not plan and settings.USE_SUPABASE:
        from backend.config import Settings
        from backend.supabase_database import SupabaseDatabase

        # Try project1
        if settings.SUPABASE_URL_PROJECT1 and settings.SUPABASE_KEY_PROJECT1:
            try:
                s1 = Settings()
                s1.SUPABASE_PROJECT = "project1"
                db1 = SupabaseDatabase(custom_settings=s1)
                plan = db1.get_weekly_plan(plan_id)
                if plan:
                    logger.info(
                        f"Plan {plan_id} found in project1 for step generation"
                    )
            except Exception as e:
                logger.debug(f"Plan not found in project1: {e}")

        # If still not found, try project2
        if (
            not plan
            and settings.SUPABASE_URL_PROJECT2
            and settings.SUPABASE_KEY_PROJECT2
        ):
            try:
                s2 = Settings()
                s2.SUPABASE_PROJECT = "project2"
                db2 = SupabaseDatabase(custom_settings=s2)
                plan = db2.get_weekly_plan(plan_id)
                if plan:
                    logger.info(
                        f"Plan {plan_id} found in project2 for step generation"
                    )
            except Exception as e:
                logger.debug(f"Plan not found in project2: {e}")

    # Fallback to default database if still not found
    if not plan:
        db = get_db()
        plan = db.get_weekly_plan(plan_id)

    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan not found: {plan_id}")

    verify_user_access(plan.user_id, current_user_id, allow_if_none=True)

    # Use the plan owner's database for all operations
    # This ensures we use the correct Supabase project (project1 or project2)
    db_for_plan = get_db(user_id=plan.user_id)
    logger.info(
        "using_plan_owner_database_for_generation",
        extra={
            "plan_id": plan_id,
            "plan_user_id": plan.user_id,
            "db_type": str(type(db_for_plan).__name__),
        },
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

    # Extract day data
    days = lesson_json.get("days", {})
    logger.info(
        "extracting_day_data",
        extra={
            "plan_id": plan_id,
            "day": day,
            "available_days": list(days.keys()),
            "day_lower": day.lower(),
        },
    )
    day_data = days.get(day.lower())
    if not day_data:
        logger.error(
            "day_not_found_in_plan",
            extra={
                "plan_id": plan_id,
                "requested_day": day,
                "available_days": list(days.keys()),
            },
        )
        raise HTTPException(status_code=404, detail=f"Day {day} not found in plan")

    # Locate the correct slot data for this day/slot. Newer weekly JSON
    # stores most instructional fields (tailored_instruction, vocabulary,
    # sentence_frames) under days[day]["slots"][*]. For backwards
    # compatibility, we fall back to day-level fields if slots are absent.

    slot_data = day_data
    slots_for_day = day_data.get("slots") or []

    if isinstance(slots_for_day, list) and slots_for_day:
        # Prefer the slot that matches the requested slot number.
        matching = None
        for s in slots_for_day:
            if not isinstance(s, dict):
                continue
            s_num = s.get("slot_number", 0)
            print(
                f"[DEBUG] Checking slot: {s_num} (type: {type(s_num)}) against requested: {slot} (type: {type(slot)})"
            )
            if int(s_num) == int(slot):
                matching = s
                print(f"[DEBUG] Found matching slot: {s_num}")
                break
        if matching:
            slot_data = matching
            print(
                f"[DEBUG] Using matched slot_data: slot_number={slot_data.get('slot_number')}"
            )
        else:
            # No matching slot found - return 404 error instead of silently using wrong slot
            available_slots = [
                s.get("slot_number") for s in slots_for_day if isinstance(s, dict)
            ]
            logger.error(
                "slot_not_found_in_plan",
                extra={
                    "plan_id": plan_id,
                    "requested_slot": slot,
                    "requested_day": day,
                    "available_slots": available_slots,
                },
            )
            raise HTTPException(
                status_code=404,
                detail=f"Slot {slot} not found in {day}. Available slots: {available_slots}",
            )

        print(
            f"[DEBUG] Final slot_data: slot_number={slot_data.get('slot_number')}, has_vocabulary_cognates={bool(slot_data.get('vocabulary_cognates'))}"
        )

        # [NO SCHOOL FIX] Skip generation if this is a "No School" slot
        unit_lesson = slot_data.get("unit_lesson", "")
        if unit_lesson and "no school" in unit_lesson.lower():
            logger.info(
                "skipping_step_generation_for_no_school",
                extra={
                    "plan_id": plan_id,
                    "day": day,
                    "slot": slot,
                    "unit_lesson": unit_lesson,
                },
            )
            return []

        print(f"[DEBUG] slot_data keys (first 20): {list(slot_data.keys())[:20]}")

        # Check if vocabulary_cognates exists in slot_data
        if slot_data.get("vocabulary_cognates"):
            vocab_list = slot_data.get("vocabulary_cognates")
            print(
                f"[DEBUG] vocabulary_cognates in slot_data: {len(vocab_list)} items"
            )
            if isinstance(vocab_list, list) and len(vocab_list) > 0:
                print(f"[DEBUG] vocabulary_cognates sample: {vocab_list[0]}")
        else:
            # Check for any vocabulary-related keys
            vocab_keys = [k for k in slot_data.keys() if "vocab" in str(k).lower()]
            if vocab_keys:
                print(
                    f"[DEBUG] WARNING: Found vocabulary-related keys but vocabulary_cognates missing: {vocab_keys}"
                )
            else:
                # Log as info instead of warning - this is expected for older plans
                logger.info(
                    "vocabulary_cognates_not_found_in_slot",
                    extra={
                        "plan_id": plan_id,
                        "day": day,
                        "slot": slot,
                        "message": "vocabulary_cognates not found in slot_data. This may mean the plan was generated before vocabulary_cognates was added to the schema. Consider regenerating the plan to include vocabulary data.",
                    },
                )
                print(
                    "[DEBUG] INFO: vocabulary_cognates not found in slot_data. "
                    "This may mean the plan was generated before vocabulary_cognates was added to the schema. "
                    "Consider regenerating the plan to include vocabulary data."
                )

        # Also check day_data as fallback
        if day_data.get("vocabulary_cognates"):
            print(
                f"[DEBUG] vocabulary_cognates in day_data: {len(day_data.get('vocabulary_cognates'))} items"
            )
            # Use day_data vocabulary_cognates if slot_data doesn't have it
            if not slot_data.get("vocabulary_cognates"):
                print("[DEBUG] Using vocabulary_cognates from day_data as fallback")
                slot_data["vocabulary_cognates"] = day_data.get(
                    "vocabulary_cognates"
                )

    # Extract phase_plan from tailored_instruction (slot-level when present)
    # Check multiple possible locations for phase_plan to handle different data structures
    slot_tailored_instruction = slot_data.get("tailored_instruction", {})
    day_tailored_instruction = day_data.get("tailored_instruction", {})

    # Use slot-level tailored_instruction if available, otherwise fall back to day-level
    # This ensures later code (like ell_support extraction) uses the best available data
    tailored_instruction = (
        slot_tailored_instruction
        if slot_tailored_instruction
        else day_tailored_instruction
    )

    logger.info(
        "tailored_instruction_extracted",
        extra={
            "plan_id": plan_id,
            "day": day,
            "slot": slot,
            "has_tailored_instruction": bool(tailored_instruction),
            "tailored_instruction_keys": list(tailored_instruction.keys())
            if tailored_instruction
            else [],
            "has_day_tailored_instruction": bool(day_tailored_instruction),
            "day_tailored_instruction_keys": list(day_tailored_instruction.keys())
            if day_tailored_instruction
            else [],
        },
    )

    # Try multiple locations for phase_plan:
    # 1. slot_data.tailored_instruction.co_teaching_model.phase_plan (preferred)
    # 2. slot_data.tailored_instruction.phase_plan (direct)
    # 3. day_data.tailored_instruction.co_teaching_model.phase_plan (day-level fallback)
    # 4. day_data.tailored_instruction.phase_plan (day-level direct)

    phase_plan = None
    co_teaching_model = slot_tailored_instruction.get("co_teaching_model", {})

    # Check slot-level: tailored_instruction.co_teaching_model.phase_plan
    if co_teaching_model:
        phase_plan = co_teaching_model.get("phase_plan")
        if phase_plan:
            logger.info(
                "phase_plan_found_in_slot_co_teaching_model",
                extra={
                    "plan_id": plan_id,
                    "day": day,
                    "slot": slot,
                    "location": "slot_data.tailored_instruction.co_teaching_model.phase_plan",
                    "phase_plan_count": len(phase_plan)
                    if isinstance(phase_plan, list)
                    else 0,
                },
            )

    # Check slot-level: tailored_instruction.phase_plan (direct)
    if not phase_plan:
        phase_plan = slot_tailored_instruction.get("phase_plan")
        if phase_plan:
            logger.info(
                "phase_plan_found_in_slot_direct",
                extra={
                    "plan_id": plan_id,
                    "day": day,
                    "slot": slot,
                    "location": "slot_data.tailored_instruction.phase_plan",
                    "phase_plan_count": len(phase_plan)
                    if isinstance(phase_plan, list)
                    else 0,
                },
            )

    # Check day-level: day_data.tailored_instruction.co_teaching_model.phase_plan
    if not phase_plan:
        day_co_teaching_model = day_tailored_instruction.get(
            "co_teaching_model", {}
        )
        if day_co_teaching_model:
            phase_plan = day_co_teaching_model.get("phase_plan")
            if phase_plan:
                logger.info(
                    "phase_plan_found_in_day_co_teaching_model",
                    extra={
                        "plan_id": plan_id,
                        "day": day,
                        "slot": slot,
                        "location": "day_data.tailored_instruction.co_teaching_model.phase_plan",
                        "phase_plan_count": len(phase_plan)
                        if isinstance(phase_plan, list)
                        else 0,
                    },
                )

    # Check day-level: day_data.tailored_instruction.phase_plan (direct)
    if not phase_plan:
        phase_plan = day_tailored_instruction.get("phase_plan")
        if phase_plan:
            logger.info(
                "phase_plan_found_in_day_direct",
                extra={
                    "plan_id": plan_id,
                    "day": day,
                    "slot": slot,
                    "location": "day_data.tailored_instruction.phase_plan",
                    "phase_plan_count": len(phase_plan)
                    if isinstance(phase_plan, list)
                    else 0,
                },
            )

    # Normalize to empty list if None
    if phase_plan is None:
        phase_plan = []

    logger.info(
        "co_teaching_model_extracted",
        extra={
            "plan_id": plan_id,
            "has_co_teaching_model": bool(co_teaching_model),
            "co_teaching_model_keys": list(co_teaching_model.keys())
            if co_teaching_model
            else [],
        },
    )

    logger.info(
        "phase_plan_extracted",
        extra={
            "plan_id": plan_id,
            "day": day,
            "slot": slot,
            "phase_plan_count": len(phase_plan) if phase_plan else 0,
            "phase_plan_is_list": isinstance(phase_plan, list),
            "phase_plan_is_none": phase_plan is None,
        },
    )
    logger.info(
        "phase_plan_extracted",
        extra={
            "plan_id": plan_id,
            "day": day,
            "slot": slot,
            "phase_plan_count": len(phase_plan) if phase_plan else 0,
            "phase_plan_is_list": isinstance(phase_plan, list),
        },
    )

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

    # Generate steps from phase_plan or use default steps if phase_plan is missing
    import uuid
    from datetime import datetime

    from backend.schema import LessonStep

    start_time_offset = 0
    generated_steps = []  # Store steps in memory in case table doesn't exist
    print("[DEBUG] Initialized generated_steps list (empty)")

    if not phase_plan:
        # Generate default lesson steps when phase_plan is missing
        logger.warning(
            "phase_plan_missing_using_defaults",
            extra={
                "plan_id": plan_id,
                "day": day,
                "slot": slot,
            },
        )
        print("[DEBUG] No phase_plan found, generating default lesson steps")

        # Create default 45-minute lesson structure: Warmup (5), Input (15), Practice (20), Closure (5)
        default_phases = [
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
        phase_plan = default_phases
        print(f"[DEBUG] Using default phase_plan with {len(phase_plan)} phases")
    else:
        print(
            f"[DEBUG] Starting step generation, phase_plan has {len(phase_plan)} phases"
        )

    for idx, phase in enumerate(phase_plan, start=1):
        print(
            f"[DEBUG] Processing phase {idx}/{len(phase_plan)}: {phase.get('phase_name', 'unnamed')}"
        )
        step_id = str(uuid.uuid4())

        # Determine content type based on phase
        content_type = phase.get("content_type", "instruction")
        step_name = phase.get("phase_name", f"Step {idx}")
        # Schema uses "minutes", but allow both for compatibility
        # Ensure duration is never 0 - default to 5 minutes if missing or 0
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

        # Extract content from phase details
        # Schema has: bilingual_teacher_role, primary_teacher_role, details
        bilingual_role = phase.get("bilingual_teacher_role", "")
        primary_role = phase.get("primary_teacher_role", "")
        details = phase.get("details", "")

        # Combine roles and details for display content
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

        # Allow sentence_frames and materials from phase if present, otherwise empty
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

        try:
            created_id = db_for_plan.create_lesson_step(step_data)
            logger.debug(
                "step_created_in_database",
                extra={
                    "plan_id": plan_id,
                    "step_name": step_name,
                    "step_id": created_id,
                },
            )
        except Exception as create_error:
            # Check if it's the specific LessonStepsTableMissingError from supabase_database
            error_type = type(create_error).__name__
            error_msg = str(create_error)

            # Check for the specific exception or the error message pattern
            is_table_missing = (
                error_type == "LessonStepsTableMissingError"
                or "lesson_steps table does not exist" in error_msg
                or "PGRST205" in error_msg
                or "Could not find the table" in error_msg
                or "lesson_steps" in error_msg.lower()
            )

            if is_table_missing:
                # Add timestamps for in-memory storage
                step_data_with_timestamps = {
                    **step_data,
                    "created_at": datetime.utcnow(),
                    "updated_at": None,
                }
                # Create a LessonStep object from step_data for in-memory storage
                generated_steps.append(LessonStep(**step_data_with_timestamps))
                logger.info(
                    "step_stored_in_memory",
                    extra={
                        "plan_id": plan_id,
                        "step_name": step_name,
                        "reason": "table missing (exception caught)",
                        "generated_steps_count": len(generated_steps),
                    },
                )
                print(
                    f"[DEBUG] Step stored in memory (exception): {step_name}, total steps: {len(generated_steps)}"
                )
            else:
                # Re-raise other errors
                logger.error(
                    "step_creation_failed",
                    extra={
                        "plan_id": plan_id,
                        "step_name": step_name,
                        "error": str(create_error),
                    },
                )
                raise
        start_time_offset += duration

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
        slot_data.get("vocabulary_cognates")
        or day_data.get("vocabulary_cognates")
        or []
    )
    day_sentence_frames = (
        slot_data.get("sentence_frames") or day_data.get("sentence_frames") or []
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

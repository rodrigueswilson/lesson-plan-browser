"""
Plans, lesson steps, lesson mode, and week status API endpoints.
"""
import asyncio
import copy
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from backend.authorization import get_current_user_id, verify_user_access
from backend.config import settings
from backend.database import get_db
from backend.models import (
    LessonModeSessionCreate,
    LessonModeSessionResponse,
    LessonPlanDetailResponse,
    LessonStepResponse,
    ScheduleEntryResponse,
    WeeklyPlanResponse,
    WeekStatusResponse,
)
from backend.rate_limiter import rate_limit_auth, rate_limit_general
from backend.telemetry import logger
from backend.utils.lesson_json_enricher import enrich_lesson_json_from_steps

router = APIRouter()


# Lesson Plan and Steps Endpoints


@router.get(
    "/plans/{plan_id}",
    response_model=LessonPlanDetailResponse,
    tags=["Weekly Plans"],
)
@rate_limit_general
async def get_plan_detail(
    request: Request,
    plan_id: str,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """Get full lesson plan with JSON content.

    Args:
        plan_id: Plan ID
        current_user_id: Current authenticated user ID

    Returns:
        LessonPlanDetailResponse with full lesson JSON
    """
    logger.info("plan_detail_requested", extra={"plan_id": plan_id})

    try:
        plan = None

        # Try to get plan using current_user_id's database first
        if current_user_id:
            db = get_db(user_id=current_user_id)
            plan = db.get_weekly_plan(plan_id)

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
                        logger.info(f"Plan {plan_id} found in project1")
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
                        logger.info(f"Plan {plan_id} found in project2")
                except Exception as e:
                    logger.debug(f"Plan not found in project2: {e}")

        # Fallback to default database if still not found
        if not plan:
            db = get_db()
            plan = db.get_weekly_plan(plan_id)

        if not plan:
            raise HTTPException(status_code=404, detail=f"Plan not found: {plan_id}")

        # Verify user access
        verify_user_access(plan.user_id, current_user_id, allow_if_none=True)

        # Note: For consistency, if this endpoint needed to do database operations,
        # we would use: db = get_db(user_id=plan.user_id) to ensure we use the
        # plan owner's database (correct Supabase project)

        # Log week_of for debugging
        logger.info(
            "plan_detail_retrieved",
            extra={
                "plan_id": plan_id,
                "week_of": plan.week_of,
                "user_id": plan.user_id,
                "has_lesson_json": plan.lesson_json is not None,
            },
        )

        # Ensure lesson_json is a dict (SQLite stores JSON as TEXT, so parse if string)
        lesson_json = plan.lesson_json
        if isinstance(lesson_json, str):
            try:
                lesson_json = json.loads(lesson_json)
            except json.JSONDecodeError:
                logger.warning("plan_detail_invalid_json", extra={"plan_id": plan_id})
                lesson_json = {}
        if not lesson_json:
            lesson_json = {}

        # CRITICAL: Ensure lesson_json is a plain dict, not a Pydantic model
        # This prevents any field filtering during serialization
        if hasattr(lesson_json, "model_dump"):
            lesson_json = lesson_json.model_dump()
        elif hasattr(lesson_json, "dict"):
            lesson_json = lesson_json.dict()

        # Deep copy to ensure we're working with a plain dict structure
        import copy

        lesson_json = copy.deepcopy(lesson_json)

        # Extract vocabulary_cognates and sentence_frames from lesson steps if missing from lesson_json
        # This ensures DOCX export includes vocabulary/frames even if they're not in the original JSON
        from backend.utils.lesson_json_enricher import enrich_lesson_json_from_steps

        db_for_plan = get_db(user_id=plan.user_id)
        lesson_json = enrich_lesson_json_from_steps(lesson_json, plan_id, db_for_plan)

        # Debug: Check if vocabulary and sentence frames are in the response
        # Check for Monday slot 2 specifically
        monday_data = lesson_json.get("days", {}).get("monday", {})
        monday_slots = monday_data.get("slots", [])
        slot_2_data = None
        if isinstance(monday_slots, list):
            slot_2_data = next(
                (
                    s
                    for s in monday_slots
                    if isinstance(s, dict) and s.get("slot_number") == 2
                ),
                None,
            )
        if slot_2_data:
            logger.info(
                "plan_detail_slot_2_debug",
                extra={
                    "plan_id": plan_id,
                    "has_vocabulary": bool(slot_2_data.get("vocabulary_cognates")),
                    "vocab_count": len(slot_2_data.get("vocabulary_cognates", [])),
                    "has_sentence_frames": bool(slot_2_data.get("sentence_frames")),
                    "frames_count": len(slot_2_data.get("sentence_frames", [])),
                    "slot_keys": list(slot_2_data.keys())[:20],
                },
            )
            # Also print to console for immediate visibility
            print(
                f"[DEBUG] Slot 2 in API response: vocab={bool(slot_2_data.get('vocabulary_cognates'))}, frames={bool(slot_2_data.get('sentence_frames'))}"
            )
            print(f"[DEBUG] Slot 2 keys: {list(slot_2_data.keys())[:30]}")
            # Check all slots to see which ones have vocabulary
            for idx, s in enumerate(monday_slots):
                if isinstance(s, dict):
                    print(
                        f"[DEBUG] Slot {s.get('slot_number')}: vocab={bool(s.get('vocabulary_cognates'))}, frames={bool(s.get('sentence_frames'))}"
                    )

        # Create response - ensure lesson_json is a plain dict to avoid any Pydantic filtering
        response = LessonPlanDetailResponse(
            id=plan.id,
            user_id=plan.user_id,
            week_of=plan.week_of,
            lesson_json=lesson_json,  # Already a plain dict from deepcopy above
            status=plan.status or "pending",
            generated_at=plan.generated_at.isoformat()
            if hasattr(plan.generated_at, "isoformat")
            else str(plan.generated_at),
            output_file=plan.output_file,
        )

        # Double-check: Verify vocabulary_cognates is still in the response
        response_monday_data = response.lesson_json.get("days", {}).get("monday", {})
        response_monday_slots = response_monday_data.get("slots", [])
        response_slot_2 = next(
            (
                s
                for s in response_monday_slots
                if isinstance(s, dict) and s.get("slot_number") == 2
            ),
            None,
        )
        if response_slot_2:
            print(
                f"[DEBUG] After LessonPlanDetailResponse creation - Slot 2 vocab: {bool(response_slot_2.get('vocabulary_cognates'))}, frames: {bool(response_slot_2.get('sentence_frames'))}"
            )
            if not response_slot_2.get("vocabulary_cognates"):
                print(
                    "[DEBUG] WARNING: vocabulary_cognates missing after response creation!"
                )
                print(f"[DEBUG] Slot 2 keys: {list(response_slot_2.keys())[:30]}")

        # Serialize to JSON to check if vocabulary_cognates survives serialization
        import json as json_module

        try:
            response_dict = response.model_dump()
            response_json_str = json_module.dumps(response_dict, default=str)
            # Check if vocabulary_cognates is in the serialized JSON
            if "vocabulary_cognates" in response_json_str:
                print("[DEBUG] vocabulary_cognates found in serialized JSON")
            else:
                print(
                    "[DEBUG] WARNING: vocabulary_cognates NOT found in serialized JSON!"
                )
            if "sentence_frames" in response_json_str:
                print("[DEBUG] sentence_frames found in serialized JSON")
            else:
                print("[DEBUG] WARNING: sentence_frames NOT found in serialized JSON!")
        except Exception as e:
            print(f"[DEBUG] Failed to serialize response for check: {e}")

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error("plan_detail_failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500, detail=f"Failed to get plan detail: {str(e)}"
        )


@router.get(
    "/lesson-steps/{plan_id}/{day}/{slot}",
    response_model=List[LessonStepResponse],
    tags=["Lesson Steps"],
)
@rate_limit_general
async def get_lesson_steps(
    request: Request,
    plan_id: str,
    day: str,
    slot: int,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """Get lesson steps for a specific lesson.

    Args:
        plan_id: Plan ID
        day: Day of week (monday, tuesday, etc.)
        slot: Slot number
        current_user_id: Current authenticated user ID

    Returns:
        List of LessonStepResponse objects
    """
    logger.info(
        "lesson_steps_requested", extra={"plan_id": plan_id, "day": day, "slot": slot}
    )
    print(f"[DEBUG] get_lesson_steps called: plan_id={plan_id}, day={day}, slot={slot}")

    try:
        # Find the plan across projects and track where we found it
        plan = None
        db_where_plan_found = None

        # Try to get plan using current_user_id's database first
        if current_user_id:
            db = get_db(user_id=current_user_id)
            plan = db.get_weekly_plan(plan_id)
            if plan:
                db_where_plan_found = db

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
                            f"Plan {plan_id} found in project1 for lesson steps"
                        )
                        db_where_plan_found = db1
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
                            f"Plan {plan_id} found in project2 for lesson steps"
                        )
                        db_where_plan_found = db2
                except Exception as e:
                    logger.debug(f"Plan not found in project2: {e}")

        # Fallback to default database if still not found
        if not plan:
            db = get_db()
            plan = db.get_weekly_plan(plan_id)
            if plan:
                db_where_plan_found = db

        if not plan:
            raise HTTPException(status_code=404, detail=f"Plan not found: {plan_id}")

        verify_user_access(plan.user_id, current_user_id, allow_if_none=True)

        # Use the plan owner's database to get lesson steps
        # This ensures we use the correct Supabase project (project1 or project2)
        db_for_steps = get_db(user_id=plan.user_id)
        logger.info(
            "using_plan_owner_database",
            extra={
                "plan_id": plan_id,
                "plan_user_id": plan.user_id,
                "db_where_plan_found": str(type(db_where_plan_found).__name__)
                if db_where_plan_found
                else None,
            },
        )

        # Get steps from the plan owner's database
        try:
            steps = db_for_steps.get_lesson_steps(
                plan_id, day_of_week=day, slot_number=slot
            )
            logger.info(
                "steps_fetched_from_plan_owner_db",
                extra={"plan_id": plan_id, "count": len(steps)},
            )
        except Exception as e:
            # Import here to avoid circular dependency
            from backend.supabase_database import LessonStepsTableMissingError

            # If table doesn't exist, get_lesson_steps should return empty list
            # But if it still raises, catch it here
            error_msg = str(e)
            error_type = type(e).__name__

            # Handle the specific exception type for missing table
            if isinstance(e, LessonStepsTableMissingError) or (
                "PGRST205" in error_msg
                or "Could not find the table" in error_msg
                or "lesson_steps" in error_msg.lower()
                or error_type == "LessonStepsTableMissingError"
            ):
                logger.warning(
                    "lesson_steps_table_missing",
                    extra={
                        "plan_id": plan_id,
                        "error": error_msg,
                        "error_type": error_type,
                    },
                )
                steps = []
            else:
                # For other errors, log but return empty list instead of raising
                # This prevents 500 errors when steps don't exist or can't be fetched
                logger.warning(
                    "error_fetching_steps_from_plan_owner_db",
                    extra={
                        "plan_id": plan_id,
                        "error": str(e),
                        "error_type": error_type,
                    },
                )
                steps = []

        # If no steps found in plan owner's database, try the database where we found the plan
        # This handles cases where steps might have been created in a different database
        if not steps and db_where_plan_found and db_where_plan_found != db_for_steps:
            logger.info(
                "no_steps_in_plan_owner_db_trying_fallback",
                extra={
                    "plan_id": plan_id,
                    "db_where_plan_found_type": str(type(db_where_plan_found).__name__),
                },
            )
            try:
                steps = db_where_plan_found.get_lesson_steps(
                    plan_id, day_of_week=day, slot_number=slot
                )
                if steps:
                    logger.info(
                        "steps_found_in_fallback_db",
                        extra={"plan_id": plan_id, "count": len(steps)},
                    )
                else:
                    logger.info(
                        "no_steps_in_fallback_db",
                        extra={"plan_id": plan_id},
                    )
            except Exception as e:
                # Silently fail - we already tried the plan owner's database
                # Don't raise, just log and continue with empty steps
                logger.debug(
                    "error_checking_fallback_db",
                    extra={
                        "plan_id": plan_id,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )
                # Ensure steps is set to empty list if exception occurred
                if "steps" not in locals() or steps is None:
                    steps = []

        # If still no steps, try the default database as a last resort
        # This handles cases where steps might be in the default SQLite or default Supabase
        if not steps:
            try:
                default_db = get_db()
                if default_db != db_for_steps and (
                    not db_where_plan_found or default_db != db_where_plan_found
                ):
                    logger.info(
                        "trying_default_database_as_last_resort",
                        extra={"plan_id": plan_id},
                    )
                    steps = default_db.get_lesson_steps(
                        plan_id, day_of_week=day, slot_number=slot
                    )
                    if steps:
                        logger.info(
                            "steps_found_in_default_db",
                            extra={"plan_id": plan_id, "count": len(steps)},
                        )
            except Exception as e:
                # Silently fail - this is a last resort attempt
                logger.debug(
                    "error_checking_default_db",
                    extra={
                        "plan_id": plan_id,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )
                # Ensure steps is set to empty list if exception occurred
                if "steps" not in locals() or steps is None:
                    steps = []

        # If no steps found and we have lesson_json, log a message
        # The frontend can handle empty steps or call generate endpoint
        if not steps and plan.lesson_json:
            logger.info(
                f"No lesson steps found for plan {plan_id}, day {day}, slot {slot}. "
                "Steps may need to be generated via /api/lesson-steps/generate (or lesson-steps/generate) endpoint."
            )

        # Convert LessonStep objects to LessonStepResponse
        # FastAPI should handle this automatically with from_attributes=True,
        # but we'll do it explicitly to ensure proper serialization
        # Use model_validate with mode='python' to ensure all fields are included
        step_responses = []
        for step in steps:
            try:
                # Handle potential serialization issues with vocabulary_cognates
                # If it's a string (JSON), we might need to parse it if the model expects a list
                vocab = getattr(step, "vocabulary_cognates", None)
                if isinstance(vocab, str):
                    try:
                        import json

                        vocab = json.loads(vocab)
                    except:
                        vocab = []

                step_responses.append(
                    LessonStepResponse.model_validate(
                        {
                            **step.__dict__,
                            "vocabulary_cognates": vocab,
                            "sentence_frames": getattr(step, "sentence_frames", None),
                        }
                    )
                )
            except Exception as e:
                logger.warning(
                    "step_validation_failed",
                    extra={
                        "plan_id": plan_id,
                        "step_id": getattr(step, "id", "unknown"),
                        "error": str(e),
                    },
                )
                # Continue processing other steps
                continue
        logger.info(
            "returning_lesson_steps",
            extra={
                "plan_id": plan_id,
                "count": len(step_responses),
                "is_list": isinstance(step_responses, list),
                "first_step_id": step_responses[0].id if step_responses else None,
            },
        )

        # Safety check: ensure we're returning a list, not plan data
        if not isinstance(step_responses, list):
            logger.error(
                "invalid_return_type",
                extra={
                    "plan_id": plan_id,
                    "return_type": str(type(step_responses)),
                    "return_value": str(step_responses)[:200],
                },
            )
            raise HTTPException(
                status_code=500,
                detail="Internal error: Invalid return type from get_lesson_steps",
            )

        return step_responses
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        import traceback

        traceback.print_exc()
        logger.error(
            "get_lesson_steps_failed_unhandled",
            extra={
                "plan_id": plan_id,
                "error": str(e),
                "traceback": traceback.format_exc(),
            },
        )
        # Return empty list on failure instead of 500
        return []


@router.post(
    "/lesson-steps/generate",
    response_model=List[LessonStepResponse],
    tags=["Lesson Steps"],
)
@rate_limit_auth
async def generate_lesson_steps(
    request: Request,
    plan_id: str,
    day: str,
    slot: int,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """Generate lesson steps from lesson plan phase_plan.

    Args:
        plan_id: Plan ID
        day: Day of week (monday, tuesday, etc.)
        slot: Slot number
        current_user_id: Current authenticated user ID

    Returns:
        List of generated LessonStepResponse objects
    """
    logger.info(
        "lesson_steps_generate_requested",
        extra={"plan_id": plan_id, "day": day, "slot": slot},
    )
    print(
        f"[DEBUG] generate_lesson_steps called: plan_id={plan_id}, day={day}, slot={slot}"
    )

    try:
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
            # Convert LessonStep objects to LessonStepResponse
            from datetime import datetime

            steps = [
                LessonStepResponse(
                    id=step.id,
                    lesson_plan_id=step.lesson_plan_id,
                    day_of_week=step.day_of_week,
                    slot_number=step.slot_number,
                    step_number=step.step_number,
                    step_name=step.step_name,
                    duration_minutes=step.duration_minutes,
                    start_time_offset=step.start_time_offset,
                    content_type=step.content_type,
                    display_content=step.display_content,
                    hidden_content=step.hidden_content or [],
                    sentence_frames=step.sentence_frames or [],
                    materials_needed=step.materials_needed or [],
                    vocabulary_cognates=step.vocabulary_cognates or [],
                    created_at=datetime.utcnow(),
                    updated_at=None,
                )
                for step in generated_steps
            ]
            logger.info("returning_in_memory_steps", extra={"count": len(steps)})
            return steps

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

        # Convert LessonStep objects to LessonStepResponse
        step_responses = [LessonStepResponse.model_validate(step) for step in steps]
        logger.info(
            "returning_generated_steps",
            extra={
                "plan_id": plan_id,
                "count": len(step_responses),
                "is_list": isinstance(step_responses, list),
                "first_step_id": step_responses[0].id if step_responses else None,
            },
        )

        # Safety check: ensure we're returning a list
        if not isinstance(step_responses, list):
            logger.error(
                "invalid_return_type_generate",
                extra={
                    "plan_id": plan_id,
                    "return_type": str(type(step_responses)),
                },
            )
            raise HTTPException(
                status_code=500,
                detail="Internal error: Invalid return type from generate_lesson_steps",
            )

        return step_responses

    except HTTPException:
        raise
    except Exception as e:
        logger.error("lesson_steps_generate_failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500, detail=f"Failed to generate steps: {str(e)}"
        )


# Lesson Mode Session endpoints
@router.post(
    "/lesson-mode/session",
    response_model=LessonModeSessionResponse,
    tags=["Lesson Mode"],
)
@rate_limit_auth
async def create_lesson_mode_session(
    request: Request,
    session_data: LessonModeSessionCreate,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """Create or update a lesson mode session."""
    logger.info(
        "lesson_mode_session_create_requested",
        extra={"user_id": session_data.user_id, "plan_id": session_data.lesson_plan_id},
    )

    try:
        verify_user_access(session_data.user_id, current_user_id, allow_if_none=True)
        db = get_db(user_id=session_data.user_id)

        # Check if active session already exists
        existing = db.get_active_lesson_mode_session(
            user_id=session_data.user_id,
            lesson_plan_id=session_data.lesson_plan_id,
            day_of_week=session_data.day_of_week,
            slot_number=session_data.slot_number,
        )

        if existing:
            # Update existing session
            import uuid

            # Keep datetimes ISO formatted before hitting Supabase/PostgREST.
            # Otherwise json.dumps inside the client raises "datetime is not JSON serializable".
            session_dict = session_data.model_dump(mode="json")
            updated = db.update_lesson_mode_session(existing.id, session_dict)
            if updated:
                updated_session = db.get_lesson_mode_session(existing.id)
                if updated_session:
                    # Convert session to response model, which will serialize datetime fields
                    return LessonModeSessionResponse.model_validate(updated_session)
            raise HTTPException(status_code=500, detail="Failed to update session")
        else:
            # Create new session
            # Note: If table is missing, create_lesson_mode_session returns None
            # In that case, we'll return a mock session response
            import uuid

            # Same JSON-friendly dump here so inserts never carry raw datetime objects.
            session_dict = session_data.model_dump(mode="json")
            session_dict["id"] = str(uuid.uuid4())

            session_id = db.create_lesson_mode_session(session_dict)
            if session_id is None:
                # Table is missing, create an in-memory session object
                from datetime import datetime

                from backend.schema import LessonModeSession

                in_memory_session = LessonModeSession(
                    id=session_dict["id"],
                    user_id=session_dict["user_id"],
                    lesson_plan_id=session_dict["lesson_plan_id"],
                    schedule_entry_id=session_dict.get("schedule_entry_id"),
                    day_of_week=session_dict["day_of_week"],
                    slot_number=session_dict["slot_number"],
                    current_step_index=session_dict["current_step_index"],
                    remaining_time=session_dict["remaining_time"],
                    is_running=session_dict["is_running"],
                    is_paused=session_dict["is_paused"],
                    is_synced=session_dict["is_synced"],
                    timer_start_time=session_dict.get("timer_start_time"),
                    paused_at=session_dict.get("paused_at"),
                    adjusted_durations=session_dict.get("adjusted_durations"),
                    created_at=datetime.utcnow(),
                    updated_at=None,
                )
                logger.info(
                    "lesson_mode_session_created_in_memory",
                    extra={
                        "session_id": in_memory_session.id,
                        "reason": "table missing",
                    },
                )
                # Convert in-memory session to response model, which will serialize datetime fields
                return LessonModeSessionResponse.model_validate(in_memory_session)

            session = db.get_lesson_mode_session(session_id)
            if session:
                # Convert session to response model, which will serialize datetime fields
                return LessonModeSessionResponse.model_validate(session)
            raise HTTPException(status_code=500, detail="Failed to create session")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("lesson_mode_session_create_failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500, detail=f"Failed to create/update session: {str(e)}"
        )


@router.get(
    "/lesson-mode/session/active",
    response_model=Optional[LessonModeSessionResponse],
    tags=["Lesson Mode"],
)
@rate_limit_general
async def get_active_lesson_mode_session(
    request: Request,
    user_id: str,
    lesson_plan_id: Optional[str] = None,
    day_of_week: Optional[str] = None,
    slot_number: Optional[int] = None,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """Get the active lesson mode session for a user/lesson."""
    try:
        verify_user_access(user_id, current_user_id, allow_if_none=True)
        db = get_db(user_id=user_id)
        session = db.get_active_lesson_mode_session(
            user_id=user_id,
            lesson_plan_id=lesson_plan_id,
            day_of_week=day_of_week,
            slot_number=slot_number,
        )
        # Convert session to response model, which will serialize datetime fields
        if session:
            return LessonModeSessionResponse.model_validate(session)
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error("active_lesson_mode_session_get_failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500, detail=f"Failed to get active session: {str(e)}"
        )


@router.get(
    "/lesson-mode/session/{session_id}",
    response_model=LessonModeSessionResponse,
    tags=["Lesson Mode"],
)
@rate_limit_general
async def get_lesson_mode_session(
    request: Request,
    session_id: str,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """Get a lesson mode session by ID."""
    try:
        db = get_db()
        session = db.get_lesson_mode_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404, detail=f"Session not found: {session_id}"
            )
        verify_user_access(session.user_id, current_user_id, allow_if_none=True)
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error("lesson_mode_session_get_failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")


@router.put(
    "/lesson-mode/session/{session_id}",
    response_model=LessonModeSessionResponse,
    tags=["Lesson Mode"],
)
@rate_limit_auth
async def update_lesson_mode_session_endpoint(
    request: Request,
    session_id: str,
    updates: Dict[str, Any],
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """Update a lesson mode session."""
    try:
        db = get_db()
        session = db.get_lesson_mode_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404, detail=f"Session not found: {session_id}"
            )
        verify_user_access(session.user_id, current_user_id, allow_if_none=True)
        updated = db.update_lesson_mode_session(session_id, updates)
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to update session")
        updated_session = db.get_lesson_mode_session(session_id)
        if not updated_session:
            raise HTTPException(
                status_code=500, detail="Failed to retrieve updated session"
            )
        # Convert session to response model, which will serialize datetime fields
        return LessonModeSessionResponse.model_validate(updated_session)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("lesson_mode_session_update_failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500, detail=f"Failed to update session: {str(e)}"
        )


@router.post(
    "/lesson-mode/session/{session_id}/end",
    response_model=dict,
    tags=["Lesson Mode"],
)
@rate_limit_auth
async def end_lesson_mode_session_endpoint(
    request: Request,
    session_id: str,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """End a lesson mode session."""
    try:
        db = get_db()
        session = db.get_lesson_mode_session(session_id)
        if not session:
            logger.warning(
                "lesson_mode_session_end_noop",
                extra={
                    "session_id": session_id,
                    "details": "session not found or table missing; treating end as success",
                },
            )
            return {
                "success": True,
                "message": "Session already ended or not persisted (no-op).",
            }
        verify_user_access(session.user_id, current_user_id, allow_if_none=True)
        ended = db.end_lesson_mode_session(session_id)
        if not ended:
            logger.warning(
                "lesson_mode_session_end_failed_noop",
                extra={
                    "session_id": session_id,
                    "details": "database update failed; treating as success",
                },
            )
            return {
                "success": True,
                "message": "Session already ended or not persisted (no-op).",
            }
        return {"success": True, "message": "Session ended"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("lesson_mode_session_end_failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to end session: {str(e)}")


@router.get(
    "/users/{user_id}/plans",
    response_model=list[WeeklyPlanResponse],
    tags=["Weekly Plans"],
)
@rate_limit_general
async def get_user_plans(
    request: Request,
    user_id: str,
    limit: Optional[int] = None,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """
    Get weekly plans for a user.

    Args:
        user_id: User ID
        limit: Maximum number of plans to return (defaults to settings.DEFAULT_PLAN_LIMIT)
        current_user_id: Current authenticated user ID (from X-Current-User-Id header)

    Returns:
        List of WeeklyPlanResponse objects
    """
    logger.info("plans_get_requested", extra={"user_id": user_id})

    try:
        # Verify user access
        verify_user_access(user_id, current_user_id, allow_if_none=True)

        logger.info(
            f"[DEBUG] get_user_plans: Request for user_id={user_id}, current_user={current_user_id}"
        )

        db = get_db(user_id=user_id)
        plans = db.get_user_plans(user_id, limit)

        logger.info(
            f"[DEBUG] get_user_plans: Found {len(plans)} plans for user_id={user_id}"
        )

        # Log week_of values for debugging
        logger.info(
            "plans_retrieved",
            extra={
                "user_id": user_id,
                "plan_count": len(plans),
                "week_of_values": [p.week_of for p in plans if p.week_of],
                "first_plan_week_of": plans[0].week_of if plans else None,
            },
        )

        return plans
    except Exception as e:
        logger.error(f"Error getting user plans: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/plans/status/{user_id}/{week_of}",
    response_model=WeekStatusResponse,
    tags=["Weekly Plans"],
)
@rate_limit_general
async def get_week_status(
    request: Request,
    user_id: str,
    week_of: str,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """
    Get the status of slots for a specific week.
    Returns which slots are already 'done' (have data in lesson_json).
    """
    try:
        # Verify user access
        verify_user_access(user_id, current_user_id, allow_if_none=True)

        db = get_db(user_id=user_id)

        # Get user slots to know what *should* be there
        slots_raw = await asyncio.to_thread(db.get_user_slots, user_id)
        total_slots_count = len(slots_raw)
        all_slot_numbers = [s.slot_number for s in slots_raw]

        # Get existing plans for this week
        plans = db.get_user_plans(user_id, limit=20)
        plan = next((p for p in plans if p.week_of == week_of), None)

        if not plan:
            return WeekStatusResponse(
                week_of=week_of,
                status=None,
                done_slots=[],
                missing_slots=all_slot_numbers,
                total_slots=total_slots_count,
            )

        # Get plan detail to see lesson_json (using await to_thread because get_plan_detail might be slow/complex)
        full_plan = await asyncio.to_thread(db.get_weekly_plan, plan.id)
        if not full_plan:
            return WeekStatusResponse(
                week_of=week_of,
                status=plan.status,
                plan_id=plan.id,
                done_slots=[],
                missing_slots=all_slot_numbers,
                total_slots=total_slots_count,
                generated_at=plan.generated_at,
            )

        done_slots_set = set()
        if full_plan.lesson_json:
            lj = full_plan.lesson_json

            # Case 1: Merged Structure (days -> {day} -> slots -> [...])
            if "days" in lj and isinstance(lj["days"], dict):
                for day_name, day_data in lj["days"].items():
                    if isinstance(day_data, dict) and "slots" in day_data:
                        for s in day_data["slots"]:
                            if isinstance(s, dict) and s.get("slot_number"):
                                try:
                                    done_slots_set.add(int(s["slot_number"]))
                                except (ValueError, TypeError):
                                    pass

            # Case 2: Top-level metadata (Fallback/Single-slot)
            if "metadata" in lj and isinstance(lj["metadata"], dict):
                if lj["metadata"].get("slot_number"):
                    try:
                        done_slots_set.add(int(lj["metadata"]["slot_number"]))
                    except (ValueError, TypeError):
                        pass

            # Case 3: Top-level slots (Fallback for other potential structures)
            if "slots" in lj and isinstance(lj["slots"], dict):
                for k in lj["slots"].keys():
                    if k.isdigit():
                        done_slots_set.add(int(k))

            # Case 4: Nested lesson_json (Legacy/Wrapper)
            if "lesson_json" in lj and isinstance(lj["lesson_json"], dict):
                inner = lj["lesson_json"]
                if (
                    "metadata" in inner
                    and isinstance(inner, dict)
                    and inner.get("metadata", {}).get("slot_number")
                ):
                    try:
                        done_slots_set.add(int(inner["metadata"]["slot_number"]))
                    except (ValueError, TypeError):
                        pass

        done_slots = sorted(list(done_slots_set))
        missing_slots = [s for s in all_slot_numbers if s not in done_slots]

        return WeekStatusResponse(
            week_of=week_of,
            status=full_plan.status,
            plan_id=full_plan.id,
            done_slots=done_slots,
            missing_slots=missing_slots,
            total_slots=total_slots_count,
            generated_at=full_plan.generated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting week status: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

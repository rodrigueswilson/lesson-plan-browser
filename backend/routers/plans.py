"""
Plans, lesson steps, lesson mode, and week status API endpoints.
"""
import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse

from backend.authorization import get_current_user_id, verify_user_access
from backend.config import settings
from backend.database import get_db
from backend.services import lesson_steps_generator
from backend.models import (
    LessonPlanDetailResponse,
    LessonStepResponse,
    WeeklyPlanResponse,
    WeekStatusResponse,
)
from backend.rate_limiter import rate_limit_auth, rate_limit_general
from backend.telemetry import logger

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


@router.get("/plans/{plan_id}/download", tags=["Weekly Plans"])
async def download_plan_file(
    plan_id: str,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """
    Download a weekly plan file by plan ID.

    Uses the stored output_file path from the database, with proper authorization checks.
    """
    logger.info("plan_download_requested", extra={"plan_id": plan_id})

    try:
        db = get_db()
        plan = db.get_weekly_plan(plan_id)

        if not plan:
            raise HTTPException(status_code=404, detail=f"Plan not found: {plan_id}")

        verify_user_access(plan.user_id, current_user_id, allow_if_none=True)

        output_file = plan.output_file
        if not output_file:
            raise HTTPException(status_code=404, detail="Plan has no output file")

        file_path = Path(output_file)
        if not file_path.exists():
            logger.warning(
                "plan_file_not_found", extra={"plan_id": plan_id, "path": output_file}
            )
            raise HTTPException(status_code=404, detail="File not found on server")

        filename = file_path.name
        logger.info(
            "plan_file_download", extra={"plan_id": plan_id, "filename": filename}
        )
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("plan_download_error", extra={"plan_id": plan_id, "error": str(e)})
        raise HTTPException(
            status_code=500, detail=f"Failed to download file: {str(e)}"
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
                    except Exception:
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
        steps = lesson_steps_generator.generate_lesson_steps(plan_id, day, slot, current_user_id)
        return [LessonStepResponse.model_validate(s) for s in steps]


    except HTTPException:
        raise
    except Exception as e:
        logger.error("lesson_steps_generate_failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500, detail=f"Failed to generate steps: {str(e)}"
        )


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

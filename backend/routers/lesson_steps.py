"""
Lesson steps API endpoints: get and generate lesson steps.
"""
import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.authorization import get_current_user_id, verify_user_access
from backend.config import settings
from backend.database import get_db
from backend.models import LessonStepResponse
from backend.rate_limiter import rate_limit_auth, rate_limit_general
from backend.services import lesson_steps_generator
from backend.telemetry import logger

router = APIRouter()


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
        steps = lesson_steps_generator.generate_lesson_steps(
            plan_id, day, slot, current_user_id
        )
        return [LessonStepResponse.model_validate(s) for s in steps]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("lesson_steps_generate_failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500, detail=f"Failed to generate steps: {str(e)}"
        )

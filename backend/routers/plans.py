"""
Plans and week status API endpoints: plan detail, download, user plans, week status.
"""
import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse

from backend.authorization import get_current_user_id, verify_user_access
from backend.config import settings
from backend.database import get_db
from backend.models import (
    LessonPlanDetailResponse,
    WeeklyPlanResponse,
    WeekStatusResponse,
)
from backend.rate_limiter import rate_limit_auth, rate_limit_general
from backend.telemetry import logger

router = APIRouter()


# Plan detail, download, user plans, week status


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

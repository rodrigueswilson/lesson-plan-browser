"""
Plans and week status API endpoints: plan detail, download, user plans, week status.
"""
import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse

from backend.authorization import get_current_user_id, verify_user_access
from backend.config import settings
from backend.database import get_db
from backend.database.plans import parse_export_generated_at
from backend.models import (
    DeletePlanResponse,
    DuplicateWeekResponse,
    LessonPlanDetailResponse,
    ResolveDuplicatesRequest,
    ResolveDuplicatesResponse,
    RestorePlanResponse,
    WeeklyPlanExportResponse,
    WeeklyPlanResponse,
    WeeklyPlanRestoreRequest,
    WeekPlansGroupResponse,
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
    "/users/{user_id}/plans/by-week",
    response_model=list[WeekPlansGroupResponse],
    tags=["Weekly Plans"],
)
@rate_limit_general
async def get_plans_by_week(
    request: Request,
    user_id: str,
    sort: Literal["school", "recent"] = Query(
        "school",
        description="school: Aug–Jun school-year order (newer years first); recent: max generated_at per week",
    ),
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """List all weeks and their plan versions for Settings > Database (includes single-version weeks)."""
    try:
        verify_user_access(user_id, current_user_id, allow_if_none=True)
        db = get_db(user_id=user_id)
        rows = await asyncio.to_thread(
            db.get_plans_grouped_by_week, user_id, sort
        )
        return [
            WeekPlansGroupResponse(week_of=r["week_of"], plans=r["plans"]) for r in rows
        ]
    except Exception as e:
        logger.error(f"Error getting plans by week: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/users/{user_id}/plans/duplicates",
    response_model=list[DuplicateWeekResponse],
    tags=["Weekly Plans"],
)
@rate_limit_general
async def get_duplicate_weeks(
    request: Request,
    user_id: str,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """Get weeks that have more than one plan for this user (for Settings > Database)."""
    try:
        verify_user_access(user_id, current_user_id, allow_if_none=True)
        db = get_db(user_id=user_id)
        rows = await asyncio.to_thread(db.get_duplicate_weeks, user_id)
        return [DuplicateWeekResponse(week_of=r["week_of"], plans=r["plans"]) for r in rows]
    except Exception as e:
        logger.error(f"Error getting duplicate weeks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/users/{user_id}/plans/resolve-duplicates",
    response_model=ResolveDuplicatesResponse,
    tags=["Weekly Plans"],
)
@rate_limit_general
async def resolve_duplicates(
    request: Request,
    user_id: str,
    body: ResolveDuplicatesRequest,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """Keep one plan for a week and remove the others; optionally create a backup first."""
    try:
        verify_user_access(user_id, current_user_id, allow_if_none=True)
        db = get_db(user_id=user_id)
        rows = await asyncio.to_thread(db.get_duplicate_weeks, user_id)
        week_entry = next((r for r in rows if r["week_of"] == body.week_of), None)
        if not week_entry:
            raise HTTPException(
                status_code=400,
                detail=f"No duplicate week found for week_of={body.week_of!r}",
            )
        plan_ids = [p["id"] for p in week_entry["plans"]]
        if body.keep_plan_id not in plan_ids:
            raise HTTPException(
                status_code=400,
                detail=f"keep_plan_id {body.keep_plan_id!r} is not in this week's plans",
            )
        backup_path = None
        if body.create_backup:
            from backend.maintenance import DatabaseMaintenance
            maintenance = DatabaseMaintenance()
            backup_path = await asyncio.to_thread(maintenance.create_backup)
        to_remove = [pid for pid in plan_ids if pid != body.keep_plan_id]
        for plan_id in to_remove:
            await asyncio.to_thread(db.delete_plan_and_dependents, plan_id)
        return ResolveDuplicatesResponse(
            success=True,
            backup_path=backup_path,
            removed_count=len(to_remove),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving duplicates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _weekly_plan_to_export_response(plan) -> WeeklyPlanExportResponse:
    return WeeklyPlanExportResponse(
        id=plan.id,
        user_id=plan.user_id,
        week_of=plan.week_of,
        status=plan.status or "pending",
        output_file=plan.output_file,
        week_folder_path=plan.week_folder_path,
        consolidated=int(plan.consolidated) if plan.consolidated is not None else 0,
        total_slots=plan.total_slots if plan.total_slots is not None else 1,
        generated_at=plan.generated_at.isoformat() if plan.generated_at else None,
        processing_time_ms=plan.processing_time_ms,
        total_tokens=plan.total_tokens,
        total_cost_usd=plan.total_cost_usd,
        llm_model=plan.llm_model,
        error_message=plan.error_message,
        lesson_json=plan.lesson_json,
    )


@router.get(
    "/users/{user_id}/plans/{plan_id}/export",
    response_model=WeeklyPlanExportResponse,
    tags=["Weekly Plans"],
)
@rate_limit_general
async def export_weekly_plan_json(
    request: Request,
    user_id: str,
    plan_id: str,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """Export one weekly plan as JSON (metadata + lesson_json) for backup."""
    try:
        verify_user_access(user_id, current_user_id, allow_if_none=True)
        db = get_db(user_id=user_id)
        plan = await asyncio.to_thread(db.get_weekly_plan, plan_id)
        if not plan or plan.user_id != user_id:
            raise HTTPException(status_code=404, detail="Plan not found")
        return _weekly_plan_to_export_response(plan)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/users/{user_id}/plans/{plan_id}",
    response_model=DeletePlanResponse,
    tags=["Weekly Plans"],
)
@rate_limit_general
async def delete_user_plan(
    request: Request,
    user_id: str,
    plan_id: str,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """Delete one weekly plan and its dependents (lesson_steps, metrics, lesson_mode sessions)."""
    try:
        verify_user_access(user_id, current_user_id, allow_if_none=True)
        db = get_db(user_id=user_id)
        plan = await asyncio.to_thread(db.get_weekly_plan, plan_id)
        if not plan or plan.user_id != user_id:
            raise HTTPException(status_code=404, detail="Plan not found")
        await asyncio.to_thread(db.delete_plan_and_dependents, plan_id)
        return DeletePlanResponse(success=True)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/users/{user_id}/plans/restore-from-export",
    response_model=RestorePlanResponse,
    tags=["Weekly Plans"],
)
@rate_limit_general
async def restore_plan_from_export(
    request: Request,
    user_id: str,
    body: WeeklyPlanRestoreRequest,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """Restore a weekly plan from per-plan export JSON (Settings > Database)."""
    try:
        verify_user_access(user_id, current_user_id, allow_if_none=True)
        if body.user_id != user_id:
            raise HTTPException(
                status_code=400,
                detail="user_id in JSON must match the user_id in the URL",
            )
        db = get_db(user_id=user_id)
        existing = await asyncio.to_thread(db.get_weekly_plan, body.id)
        if existing:
            if existing.user_id != user_id:
                raise HTTPException(status_code=404, detail="Plan not found")
            if not body.replace_existing:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "A plan with this id already exists. "
                        "Check 'Replace existing plan' to overwrite it "
                        "(this removes the current row and dependents first)."
                    ),
                )
            await asyncio.to_thread(db.delete_plan_and_dependents, body.id)
        ga = parse_export_generated_at(body.generated_at)
        await asyncio.to_thread(
            db.insert_weekly_plan_from_export,
            body.id,
            body.user_id,
            body.week_of,
            body.status,
            body.output_file,
            body.week_folder_path,
            body.consolidated,
            body.total_slots,
            ga,
            body.processing_time_ms,
            body.total_tokens,
            body.total_cost_usd,
            body.llm_model,
            body.error_message,
            body.lesson_json,
        )
        return RestorePlanResponse(success=True, plan_id=body.id)
    except HTTPException:
        raise
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        logger.error(f"Error restoring plan from export: {e}")
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

        from backend.utils.date_formatter import normalize_week_of_canonical, normalize_week_of_for_match

        try:
            week_of = normalize_week_of_canonical(week_of)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid week_of format; use MM/DD-MM/DD or MM-DD-MM-DD")

        plans = db.get_user_plans(user_id, limit=20)
        canonical = week_of
        plan = next(
            (p for p in plans if p.week_of == week_of or (canonical and normalize_week_of_for_match(p.week_of or "") == canonical)),
            None,
        )

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

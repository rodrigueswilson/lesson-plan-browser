"""
Schedule API endpoints.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.authorization import get_current_user_id, verify_user_access
from backend.database import get_db
from backend.models import (
    ScheduleBulkCreateRequest,
    ScheduleBulkCreateResponse,
    ScheduleEntryCreate,
    ScheduleEntryResponse,
    ScheduleEntryUpdate,
)
from backend.rate_limiter import rate_limit_auth
from backend.telemetry import logger
from backend.utils.schedule_utils import prepare_schedule_entry

router = APIRouter()


@router.post("/schedules", response_model=ScheduleEntryResponse, tags=["Schedules"])
@rate_limit_auth
async def create_schedule_entry(
    request: Request,
    entry: ScheduleEntryCreate,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """
    Create a new schedule entry.

    Args:
        entry: ScheduleEntryCreate with schedule data
        current_user_id: Current authenticated user ID

    Returns:
        ScheduleEntryResponse with created entry data
    """
    logger.info(
        "schedule_create_requested",
        extra={"user_id": entry.user_id, "day": entry.day_of_week},
    )

    # Verify user access
    user_id = verify_user_access(entry.user_id, current_user_id, allow_if_none=True)
    db = get_db(user_id=user_id)

    try:
        # Prepare entry with normalization
        prepared = prepare_schedule_entry(
            user_id=entry.user_id,
            day_of_week=entry.day_of_week,
            start_time=entry.start_time,
            end_time=entry.end_time,
            subject=entry.subject,
            homeroom=entry.homeroom,
            grade=entry.grade,
            slot_number=entry.slot_number,
            plan_slot_group_id=entry.plan_slot_group_id,
        )

        schedule_id = db.create_schedule_entry(**prepared)
        schedule_entry = db.get_user_schedule(
            user_id=entry.user_id, day_of_week=entry.day_of_week
        )
        created_entry = next((e for e in schedule_entry if e.id == schedule_id), None)

        if not created_entry:
            raise HTTPException(
                status_code=500, detail="Failed to retrieve created entry"
            )

        logger.info("schedule_created", extra={"schedule_id": schedule_id})
        return ScheduleEntryResponse.model_validate(created_entry)
    except Exception as e:
        logger.error("schedule_create_failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500, detail=f"Failed to create schedule entry: {str(e)}"
        )


@router.get(
    "/schedules/{user_id}",
    response_model=List[ScheduleEntryResponse],
    tags=["Schedules"],
)
@rate_limit_auth
async def get_user_schedule(
    request: Request,
    user_id: str,
    day_of_week: Optional[str] = None,
    homeroom: Optional[str] = None,
    grade: Optional[str] = None,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """
    Get schedule entries for a user.

    Args:
        user_id: User ID
        day_of_week: Optional filter by day of week
        homeroom: Optional filter by homeroom
        grade: Optional filter by grade
        current_user_id: Current authenticated user ID

    Returns:
        List of ScheduleEntryResponse objects
    """
    logger.info(
        "schedule_get_requested", extra={"user_id": user_id, "day": day_of_week}
    )

    # Verify user access
    verified_user_id = verify_user_access(user_id, current_user_id, allow_if_none=True)
    db = get_db(user_id=verified_user_id)

    try:
        entries = db.get_user_schedule(
            user_id=user_id,
            day_of_week=day_of_week,
            homeroom=homeroom,
            grade=grade,
        )

        # Convert SQLModel objects to response models
        result = [ScheduleEntryResponse.model_validate(entry) for entry in entries]

        logger.info("schedule_retrieved", extra={"count": len(result)})
        return result
    except Exception as e:
        logger.error("schedule_get_failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to get schedule: {str(e)}")


@router.get(
    "/schedules/{user_id}/current",
    response_model=Optional[ScheduleEntryResponse],
    tags=["Schedules"],
)
@rate_limit_auth
async def get_current_lesson(
    request: Request,
    user_id: str,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """
    Get current lesson based on current time.

    Args:
        user_id: User ID
        current_user_id: Current authenticated user ID

    Returns:
        ScheduleEntryResponse for current lesson or None
    """
    logger.info("current_lesson_requested", extra={"user_id": user_id})

    # Verify user access
    verified_user_id = verify_user_access(user_id, current_user_id, allow_if_none=True)
    db = get_db(user_id=verified_user_id)

    try:
        current_lesson = db.get_current_lesson(user_id=user_id)

        if current_lesson:
            logger.info(
                "current_lesson_found", extra={"schedule_id": current_lesson.id}
            )
            return current_lesson
        else:
            logger.info("no_current_lesson", extra={"user_id": user_id})
            return None
    except Exception as e:
        logger.error("current_lesson_failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500, detail=f"Failed to get current lesson: {str(e)}"
        )


@router.put(
    "/schedules/{schedule_id}",
    response_model=ScheduleEntryResponse,
    tags=["Schedules"],
)
@rate_limit_auth
async def update_schedule_entry(
    request: Request,
    schedule_id: str,
    update: ScheduleEntryUpdate,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """
    Update a schedule entry.

    Args:
        schedule_id: Schedule entry ID
        update: ScheduleEntryUpdate with fields to update
        current_user_id: Current authenticated user ID

    Returns:
        ScheduleEntryResponse with updated entry data
    """
    logger.info("schedule_update_requested", extra={"schedule_id": schedule_id})

    db = get_db()

    # Get the entry to find user_id - need to search across all users
    # For now, we'll get all schedules and find the one we need
    # In production, you might want a more efficient lookup
    all_entries = []
    try:
        # Try to get from current user first
        if current_user_id:
            db_user = get_db(user_id=current_user_id)
            all_entries = db_user.get_user_schedule(user_id=current_user_id)
            entry = next((e for e in all_entries if e.id == schedule_id), None)
            if entry:
                user_id = entry.user_id
                verified_user_id = verify_user_access(
                    user_id, current_user_id, allow_if_none=True
                )
                db = get_db(user_id=verified_user_id)
            else:
                raise HTTPException(
                    status_code=404, detail=f"Schedule entry not found: {schedule_id}"
                )
        else:
            raise HTTPException(
                status_code=404, detail=f"Schedule entry not found: {schedule_id}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("schedule_update_lookup_failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=404, detail=f"Schedule entry not found: {schedule_id}"
        )

    try:
        # Prepare update data
        update_data = update.dict(exclude_unset=True)

        if "plan_slot_group_id" in update_data:
            value = update_data["plan_slot_group_id"]
            update_data["plan_slot_group_id"] = (
                value or None
            )  # normalize empty strings to None

        # Normalize subject if being updated
        if "subject" in update_data:
            from backend.utils.schedule_utils import (
                is_meeting_period,
                is_non_class_period,
                prepare_schedule_entry,
            )

            normalized_subject = prepare_schedule_entry(
                user_id=user_id,
                day_of_week=entry.day_of_week,
                start_time=entry.start_time,
                end_time=entry.end_time,
                subject=update_data["subject"],
                homeroom=update_data.get("homeroom", entry.homeroom),
                grade=update_data.get("grade", entry.grade),
                slot_number=entry.slot_number or 0,
            )["subject"]

            update_data["subject"] = normalized_subject

            # Auto-clear homeroom/grade for non-class periods (meetings PLC/GLM may keep grade/room)
            if is_non_class_period(normalized_subject) and not is_meeting_period(normalized_subject):
                update_data["homeroom"] = None
                update_data["grade"] = None
                update_data["is_active"] = False
                update_data["plan_slot_group_id"] = None

        success = db.update_schedule_entry(schedule_id, update_data)

        if not success:
            raise HTTPException(
                status_code=404, detail=f"Schedule entry not found: {schedule_id}"
            )

        # Get the updated entry to return full object
        entries = db.get_user_schedule(user_id=user_id)
        updated_entry = next((e for e in entries if e.id == schedule_id), None)

        if not updated_entry:
            raise HTTPException(
                status_code=500, detail="Failed to retrieve updated entry"
            )

        logger.info("schedule_updated", extra={"schedule_id": schedule_id})
        return updated_entry
    except HTTPException:
        raise
    except Exception as e:
        logger.error("schedule_update_failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500, detail=f"Failed to update schedule entry: {str(e)}"
        )


@router.delete("/schedules/{schedule_id}", tags=["Schedules"])
@rate_limit_auth
async def delete_schedule_entry(
    request: Request,
    schedule_id: str,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """
    Delete a schedule entry.

    Args:
        schedule_id: Schedule entry ID
        current_user_id: Current authenticated user ID

    Returns:
        Success message
    """
    logger.info("schedule_delete_requested", extra={"schedule_id": schedule_id})

    db = get_db()

    # Get the entry to find user_id
    if current_user_id:
        db_user = get_db(user_id=current_user_id)
        entries = db_user.get_user_schedule(user_id=current_user_id)
        entry = next((e for e in entries if e.id == schedule_id), None)

        if not entry:
            raise HTTPException(
                status_code=404, detail=f"Schedule entry not found: {schedule_id}"
            )

        user_id = entry.user_id
        verified_user_id = verify_user_access(
            user_id, current_user_id, allow_if_none=True
        )
        db = get_db(user_id=verified_user_id)
    else:
        raise HTTPException(
            status_code=404, detail=f"Schedule entry not found: {schedule_id}"
        )

    try:
        success = db.delete_schedule_entry(schedule_id)

        if not success:
            raise HTTPException(
                status_code=404, detail=f"Schedule entry not found: {schedule_id}"
            )

        logger.info("schedule_deleted", extra={"schedule_id": schedule_id})
        return {"success": True, "message": "Schedule entry deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("schedule_delete_failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500, detail=f"Failed to delete schedule entry: {str(e)}"
        )


@router.post(
    "/schedules/{user_id}/bulk",
    response_model=ScheduleBulkCreateResponse,
    tags=["Schedules"],
)
@rate_limit_auth
async def bulk_create_schedule(
    request: Request,
    user_id: str,
    bulk_request: ScheduleBulkCreateRequest,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """
    Bulk create schedule entries (for importing from table).

    Args:
        user_id: User ID
        bulk_request: ScheduleBulkCreateRequest with list of entries
        current_user_id: Current authenticated user ID

    Returns:
        ScheduleBulkCreateResponse with created count and errors
    """
    logger.info(
        "schedule_bulk_create_requested",
        extra={"user_id": user_id, "count": len(bulk_request.entries)},
    )

    # Verify user access
    verified_user_id = verify_user_access(user_id, current_user_id, allow_if_none=True)
    db = get_db(user_id=verified_user_id)

    # Verify all entries belong to the same user
    for entry in bulk_request.entries:
        if entry.user_id != user_id:
            raise HTTPException(
                status_code=400, detail="All entries must belong to the same user"
            )

    try:
        # Clear existing schedule before inserting replacements
        cleared = db.clear_user_schedule(user_id)
        logger.info(
            "schedule_cleared_before_bulk_create",
            extra={"user_id": user_id, "cleared_count": cleared},
        )

        # Prepare entries with normalization
        prepared_entries = []
        for entry in bulk_request.entries:
            prepared = prepare_schedule_entry(
                user_id=entry.user_id,
                day_of_week=entry.day_of_week,
                start_time=entry.start_time,
                end_time=entry.end_time,
                subject=entry.subject,
                homeroom=entry.homeroom,
                grade=entry.grade,
                slot_number=entry.slot_number,
                plan_slot_group_id=entry.plan_slot_group_id,
            )
            prepared_entries.append(prepared)

        created_count, errors = db.bulk_create_schedule_entries(prepared_entries)

        logger.info(
            "schedule_bulk_created",
            extra={"created": created_count, "errors": len(errors)},
        )
        return ScheduleBulkCreateResponse(
            success=len(errors) == 0,
            created_count=created_count,
            errors=errors if errors else None,
        )
    except Exception as e:
        logger.error("schedule_bulk_create_failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500, detail=f"Failed to bulk create schedule entries: {str(e)}"
        )

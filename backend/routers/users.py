"""
Users, class slots, and schedules API endpoints.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.authorization import get_current_user_id, verify_slot_ownership, verify_user_access
from backend.config import settings
from backend.database import get_db
from backend.models import (
    ClassSlotCreate,
    ClassSlotResponse,
    ClassSlotUpdate,
    ScheduleBulkCreateRequest,
    ScheduleBulkCreateResponse,
    ScheduleEntryCreate,
    ScheduleEntryResponse,
    ScheduleEntryUpdate,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from backend.rate_limiter import rate_limit_auth, rate_limit_general
from backend.telemetry import logger
from backend.utils.schedule_utils import prepare_schedule_entry
from backend.week_detector import detect_weeks_from_folder, format_week_display

router = APIRouter()

# Log Supabase fallback warning once per process to avoid log noise
_supabase_fallback_logged: set = set()


# User Management Endpoints


@router.post("/users", response_model=UserResponse, tags=["Users"])
async def create_user(request: UserCreate):
    """
    Create a new user profile.

    Args:
        request: UserCreate with first_name, last_name, and email

    Returns:
        UserResponse with created user data
    """
    logger.info(
        "user_create_requested",
        extra={"first_name": request.first_name, "last_name": request.last_name},
    )

    try:
        db = get_db()
        user_id = db.create_user(
            first_name=request.first_name,
            last_name=request.last_name,
            email=request.email,
        )
        user = db.get_user(user_id)

        logger.info("user_created", extra={"user_id": user_id})
        return user
    except Exception as e:
        logger.error("user_create_failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@router.get("/users", response_model=list[UserResponse], tags=["Users"])
async def list_users():
    """
    List all users from all configured Supabase projects.

    Returns:
        List of UserResponse objects from all projects
    """
    logger.info("users_list_requested")

    try:
        all_users = []

        # If using Supabase, query both projects
        if settings.USE_SUPABASE:
            from backend.config import Settings
            from backend.supabase_database import SupabaseDatabase

            # Supabase connection failures are expected until fully implemented in a later stage.
            # SQLite fallback below handles it when Supabase is unreachable (e.g. offline).
            _supabase_note = (
                "Supabase will be fully implemented in a later stage. "
                "SQLite fallback in use. This warning is expected."
            )

            # Query project1 if configured
            if settings.SUPABASE_URL_PROJECT1 and settings.SUPABASE_KEY_PROJECT1:
                try:
                    s1 = Settings()
                    s1.SUPABASE_PROJECT = "project1"
                    db1 = SupabaseDatabase(custom_settings=s1)
                    users1 = db1.list_users()
                    all_users.extend(users1)
                    logger.info(
                        "users_loaded_from_project",
                        extra={"project": "project1", "count": len(users1)},
                    )
                except Exception as e:
                    if "project1" not in _supabase_fallback_logged:
                        _supabase_fallback_logged.add("project1")
                        logger.warning(
                            "users_load_project1_failed",
                            extra={"error": str(e), "note": _supabase_note},
                        )
                    else:
                        logger.debug(
                            "users_load_project1_failed",
                            extra={"error": str(e), "note": _supabase_note},
                        )

            # Query project2 if configured
            if settings.SUPABASE_URL_PROJECT2 and settings.SUPABASE_KEY_PROJECT2:
                try:
                    s2 = Settings()
                    s2.SUPABASE_PROJECT = "project2"
                    db2 = SupabaseDatabase(custom_settings=s2)
                    users2 = db2.list_users()
                    all_users.extend(users2)
                    logger.info(
                        "users_loaded_from_project",
                        extra={"project": "project2", "count": len(users2)},
                    )
                except Exception as e:
                    if "project2" not in _supabase_fallback_logged:
                        _supabase_fallback_logged.add("project2")
                        logger.warning(
                            "users_load_project2_failed",
                            extra={"error": str(e), "note": _supabase_note},
                        )
                    else:
                        logger.debug(
                            "users_load_project2_failed",
                            extra={"error": str(e), "note": _supabase_note},
                        )

            # Fallback to SQLite when Supabase is unreachable (e.g. getaddrinfo failed)
            if not all_users:
                try:
                    db = get_db()
                    fallback_users = db.list_users()
                    all_users.extend(fallback_users)
                    logger.info(
                        "users_loaded_from_sqlite_fallback",
                        extra={"count": len(fallback_users)},
                    )
                except Exception as e:
                    logger.warning(
                        "users_load_sqlite_fallback_failed",
                        extra={"error": str(e)},
                    )
        else:
            # Use SQLite
            db = get_db()
            all_users = db.list_users()

        # Deduplicate by user ID (in case same users exist in multiple projects)
        seen_ids = set()
        unique_users = []
        for user in all_users:
            if user.id not in seen_ids:
                seen_ids.add(user.id)
                unique_users.append(user)

        # Filter to only show User 1 (Wilson Rodrigues) and User 2 (Daniela Silva)
        # All other users are archived and should not appear in the frontend
        ALLOWED_USER_IDS = {
            "04fe8898-cb89-4a73-affb-64a97a98f820",  # User 1: Wilson Rodrigues
            "29fa9ed7-3174-4999-86fd-40a542c28cff",  # User 2: Daniela Silva
        }
        active_users = [u for u in unique_users if u.id in ALLOWED_USER_IDS]

        # Sort by name for consistent ordering
        active_users.sort(key=lambda u: u.name or "")

        return active_users
    except Exception as e:
        logger.error("users_list_failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to list users: {str(e)}")


@router.get("/recent-weeks", tags=["Users"])
@rate_limit_general
async def get_recent_weeks(
    request: Request,
    user_id: str,
    limit: int = 3,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """
    Get recent weeks from folder detection or database.

    First attempts to detect week folders from the user's base_path_override directory
    (e.g., folders like "25 W47", "25 W48", "25 W49"). If no folders are found or
    base_path_override is not set, falls back to querying the database for already
    generated weeks.

    Args:
        user_id: User ID
        limit: Maximum number of recent weeks to return (default 3)
        current_user_id: Current authenticated user ID (from X-Current-User-Id header)

    Returns:
        List of recent weeks with week_of dates and display names
    """
    logger.info("recent_weeks_requested", extra={"user_id": user_id, "limit": limit})

    try:
        # Verify user access
        verify_user_access(user_id, current_user_id, allow_if_none=True)

        db = get_db(user_id=user_id)
        user = db.get_user(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        result = []

        # First, try to detect weeks from folder structure if base_path_override is configured
        if user.base_path_override:
            try:
                logger.info(
                    "detecting_weeks_from_folder",
                    extra={"path": user.base_path_override, "user_id": user_id},
                )
                detected_weeks = detect_weeks_from_folder(
                    user.base_path_override, limit=limit
                )

                if detected_weeks:
                    # Format detected weeks for frontend
                    for week_info in detected_weeks:
                        week_of = week_info.get("week_of")
                        folder_name = week_info.get("folder_name", week_of)

                        if week_of:
                            # Use format_week_display to create display string
                            display = format_week_display(week_info)

                            result.append(
                                {
                                    "week_of": week_of,
                                    "display": display,
                                    "folder_name": folder_name,
                                }
                            )

                    logger.info(
                        "weeks_detected_from_folder",
                        extra={"count": len(result), "user_id": user_id},
                    )
                    return result
                else:
                    logger.info(
                        "no_weeks_found_in_folder",
                        extra={"path": user.base_path_override, "user_id": user_id},
                    )
            except Exception as folder_error:
                logger.warning(
                    "folder_detection_failed",
                    extra={
                        "error": str(folder_error),
                        "path": user.base_path_override,
                        "user_id": user_id,
                    },
                )
                # Continue to database fallback

        # Fallback: Query database for distinct weeks
        from sqlmodel import Session, select

        from backend.schema import WeeklyPlan

        with Session(db.engine) as session:
            # Get distinct week_of values, ordered by most recent generated_at
            statement = (
                select(WeeklyPlan.week_of)
                .where(WeeklyPlan.user_id == user_id)
                .where(WeeklyPlan.week_of.isnot(None))
                .distinct()
                .order_by(WeeklyPlan.generated_at.desc())
                .limit(limit)
            )
            # Execute and get unique weeks (in case of duplicates)
            rows = session.exec(statement).all()
            # Get unique weeks while preserving order
            seen_weeks = set()
            unique_weeks = []
            for week_of in rows:
                if week_of and week_of not in seen_weeks:
                    seen_weeks.add(week_of)
                    unique_weeks.append(week_of)
                    if len(unique_weeks) >= limit:
                        break

        # Format for frontend
        for week_of in unique_weeks:
            # Format display name
            try:
                parts = week_of.split("-")
                if len(parts) == 4:
                    start = f"{parts[0]}/{parts[1]}"
                    end = f"{parts[2]}/{parts[3]}"
                    display = f"{start} to {end}"
                else:
                    display = week_of
            except Exception:
                display = week_of

            result.append(
                {
                    "week_of": week_of,
                    "display": display,
                    "folder_name": week_of,  # Use week_of as folder_name for compatibility
                }
            )

        logger.info(
            "recent_weeks_found", extra={"count": len(result), "source": "database"}
        )
        return result

    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        logger.error(
            "recent_weeks_error", extra={"error": str(e), "traceback": error_details}
        )
        raise HTTPException(status_code=500, detail=f"Failed to detect weeks: {str(e)}")


@router.get("/users/{user_id}", response_model=UserResponse, tags=["Users"])
@rate_limit_auth
async def get_user(
    request: Request,
    user_id: str,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """
    Get user by ID.

    Args:
        user_id: User ID
        current_user_id: Current authenticated user ID (from X-Current-User-Id header)

    Returns:
        UserResponse with user data

    Raises:
        HTTPException: If user not found or access denied
    """
    logger.info("user_get_requested", extra={"user_id": user_id})

    try:
        # Verify user access
        verify_user_access(user_id, current_user_id, allow_if_none=True)

        db = get_db(user_id=user_id)
        user = db.get_user(user_id)

        if not user:
            raise HTTPException(status_code=404, detail=f"User not found: {user_id}")

        return user
    except HTTPException:
        raise


@router.put("/users/{user_id}", response_model=UserResponse, tags=["Users"])
@rate_limit_auth
async def update_user(
    request: Request,
    user_id: str,
    user_update: UserUpdate,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """
    Update user profile.

    Args:
        user_id: User ID
        request: UserUpdate with optional first_name, last_name, email
        current_user_id: Current authenticated user ID (from X-Current-User-Id header)

    Returns:
        UserResponse with updated user data

    Raises:
        HTTPException: If user not found or access denied
    """
    logger.info("user_update_requested", extra={"user_id": user_id})

    try:
        # Verify user access
        verify_user_access(user_id, current_user_id, allow_if_none=True)

        db = get_db(user_id=user_id)
        user = db.get_user(user_id)

        if not user:
            raise HTTPException(status_code=404, detail=f"User not found: {user_id}")

        # Update user fields
        success = db.update_user(
            user_id,
            first_name=user_update.first_name,
            last_name=user_update.last_name,
            email=user_update.email,
        )

        if not success:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Get updated user
        user = db.get_user(user_id)
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error("user_update_failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")


@router.put("/users/{user_id}/base-path", response_model=UserResponse, tags=["Users"])
@rate_limit_auth
async def update_user_base_path(
    request: Request,
    user_id: str,
    base_path: str,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """
    Update user's base path override.

    Args:
        user_id: User ID
        base_path: Base path for lesson plans
        current_user_id: Current authenticated user ID (from X-Current-User-Id header)

    Returns:
        UserResponse with updated user data

    Raises:
        HTTPException: If user not found or access denied
    """
    logger.info("user_base_path_update_requested", extra={"user_id": user_id})

    try:
        # Verify user access
        verify_user_access(user_id, current_user_id, allow_if_none=True)

        db = get_db(user_id=user_id)
        user = db.get_user(user_id)

        if not user:
            raise HTTPException(status_code=404, detail=f"User not found: {user_id}")

        # Update base path
        success = db.update_user_base_path(user_id, base_path)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to update base path")

        # Get updated user
        user = db.get_user(user_id)
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error("user_base_path_update_failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500, detail=f"Failed to update base path: {str(e)}"
        )


@router.put(
    "/users/{user_id}/template-paths", response_model=UserResponse, tags=["Users"]
)
@rate_limit_auth
async def update_user_template_paths(
    request: Request,
    user_id: str,
    template_path: Optional[str] = None,
    signature_image_path: Optional[str] = None,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """
    Update user's template path and/or signature image path.

    Args:
        user_id: User ID
        template_path: Optional path to lesson plan template document
        signature_image_path: Optional path to signature image file (empty string to remove)
        current_user_id: Current authenticated user ID (from X-Current-User-Id header)

    Returns:
        UserResponse with updated user data

    Raises:
        HTTPException: If user not found or access denied
    """
    logger.info(
        "user_template_paths_update_requested",
        extra={
            "user_id": user_id,
            "has_template_path": template_path is not None,
            "has_signature_path": signature_image_path is not None,
        },
    )

    try:
        # Verify user access
        verify_user_access(user_id, current_user_id, allow_if_none=True)

        db = get_db(user_id=user_id)
        user = db.get_user(user_id)

        if not user:
            raise HTTPException(status_code=404, detail=f"User not found: {user_id}")

        # Update template paths
        success = db.update_user_template_paths(
            user_id, template_path, signature_image_path
        )

        if not success:
            raise HTTPException(
                status_code=400, detail="Failed to update template paths"
            )

        # Get updated user
        user = db.get_user(user_id)
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error("user_template_paths_update_failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500, detail=f"Failed to update template paths: {str(e)}"
        )


@router.delete("/users/{user_id}", tags=["Users"])
@rate_limit_auth
async def delete_user(
    request: Request,
    user_id: str,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """
    Delete a user and all associated data.

    Args:
        user_id: User ID to delete
        current_user_id: Current authenticated user ID (from X-Current-User-Id header)

    Returns:
        Success message

    Raises:
        HTTPException: If user not found or access denied
    """
    logger.info("user_delete_requested", extra={"user_id": user_id})

    try:
        # Verify user access
        verify_user_access(user_id, current_user_id, allow_if_none=True)

        db = get_db(user_id=user_id)
        user = db.get_user(user_id)

        if not user:
            raise HTTPException(status_code=404, detail=f"User not found: {user_id}")

        success = db.delete_user(user_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete user")

        logger.info("user_deleted", extra={"user_id": user_id})
        return {"success": True, "message": f"User {user_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("user_delete_failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")


@router.post(
    "/users/{user_id}/slots", response_model=ClassSlotResponse, tags=["Class Slots"]
)
@rate_limit_auth
async def create_class_slot(
    request: Request,
    user_id: str,
    slot_data: ClassSlotCreate,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """
    Create a class slot for a user.

    Args:
        user_id: User ID
        request: ClassSlotCreate with slot configuration
        current_user_id: Current authenticated user ID (from X-Current-User-Id header)

    Returns:
        ClassSlotResponse with created slot data
    """
    logger.info(
        "slot_create_requested",
        extra={"user_id": user_id, "slot_number": slot_data.slot_number},
    )

    try:
        # Verify user access
        verify_user_access(user_id, current_user_id, allow_if_none=True)

        db = get_db(user_id=user_id)

        # Verify user exists
        user = db.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User not found: {user_id}")

        # Create slot
        slot_id = db.create_class_slot(
            user_id=user_id,
            slot_number=slot_data.slot_number,
            subject=slot_data.subject,
            grade=slot_data.grade,
            homeroom=slot_data.homeroom,
            plan_group_label=slot_data.plan_group_label,
            proficiency_levels=slot_data.proficiency_levels,
            primary_teacher_file=slot_data.primary_teacher_file,
            primary_teacher_first_name=slot_data.primary_teacher_first_name,
            primary_teacher_last_name=slot_data.primary_teacher_last_name,
        )

        slot = db.get_slot(slot_id)
        logger.info("slot_created", extra={"slot_id": slot_id})
        return slot
    except HTTPException:
        raise
    except Exception as e:
        logger.error("slot_create_failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to create slot: {str(e)}")


@router.get(
    "/users/{user_id}/slots",
    response_model=list[ClassSlotResponse],
    tags=["Class Slots"],
)
@rate_limit_general
async def get_user_slots(
    request: Request,
    user_id: str,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """
    Get all class slots for a user.

    Args:
        user_id: User ID
        current_user_id: Current authenticated user ID (from X-Current-User-Id header)

    Returns:
        List of ClassSlotResponse objects
    """
    logger.info("slots_get_requested", extra={"user_id": user_id})

    try:
        # Verify user access
        verify_user_access(user_id, current_user_id, allow_if_none=True)

        db = get_db(user_id=user_id)
        slots = db.get_user_slots(user_id)
        return slots
    except HTTPException:
        raise
    except Exception as e:
        logger.error("slots_get_failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to get slots: {str(e)}")


@router.put("/slots/{slot_id}", response_model=ClassSlotResponse, tags=["Class Slots"])
@rate_limit_auth
async def update_class_slot(
    request: Request,
    slot_id: str,
    slot_update: ClassSlotUpdate,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """
    Update a class slot.

    Args:
        slot_id: Slot ID
        request: ClassSlotUpdate with fields to update
        current_user_id: Current authenticated user ID (from X-Current-User-Id header)

    Returns:
        ClassSlotResponse with updated slot data
    """
    logger.info("slot_update_requested", extra={"slot_id": slot_id})

    try:
        # Get the slot to find its user_id and verify ownership
        # For SQLite, we can directly query. For Supabase, we need to find the project first.
        db = get_db()

        # If using Supabase and we have a current_user_id, try that database first
        if settings.USE_SUPABASE and current_user_id:
            try:
                db_with_user = get_db(user_id=current_user_id)
                slot_check = db_with_user.get_slot(slot_id)
                if slot_check:
                    db = db_with_user
                    logger.info(
                        "slot_found_in_user_db",
                        extra={"slot_id": slot_id, "user_id": current_user_id},
                    )
            except Exception as e:
                logger.debug(
                    "slot_not_in_user_db_trying_default",
                    extra={"slot_id": slot_id, "error": str(e)},
                )

        # If slot not found and using Supabase, try searching all projects
        if settings.USE_SUPABASE:
            slot_check = db.get_slot(slot_id)
            if not slot_check:
                logger.info(
                    "slot_not_found_in_default_db_searching_all_projects",
                    extra={"slot_id": slot_id},
                )
                slot_found = False
                # Try project1
                if (
                    not slot_found
                    and settings.SUPABASE_URL_PROJECT1
                    and settings.SUPABASE_KEY_PROJECT1
                ):
                    try:
                        from backend.config import Settings
                        from backend.supabase_database import SupabaseDatabase

                        s1 = Settings()
                        s1.SUPABASE_PROJECT = "project1"
                        db1 = SupabaseDatabase(custom_settings=s1)
                        slot1 = db1.get_slot(slot_id)
                        if slot1:
                            db = db1
                            slot_found = True
                            logger.info(
                                "slot_found_in_project1", extra={"slot_id": slot_id}
                            )
                    except Exception as e:
                        logger.debug(
                            "slot_not_in_project1",
                            extra={"slot_id": slot_id, "error": str(e)},
                        )

                # Try project2
                if (
                    not slot_found
                    and settings.SUPABASE_URL_PROJECT2
                    and settings.SUPABASE_KEY_PROJECT2
                ):
                    try:
                        from backend.config import Settings
                        from backend.supabase_database import SupabaseDatabase

                        s2 = Settings()
                        s2.SUPABASE_PROJECT = "project2"
                        db2 = SupabaseDatabase(custom_settings=s2)
                        slot2 = db2.get_slot(slot_id)
                        if slot2:
                            db = db2
                            logger.info(
                                "slot_found_in_project2", extra={"slot_id": slot_id}
                            )
                    except Exception as e:
                        logger.debug(
                            "slot_not_in_project2",
                            extra={"slot_id": slot_id, "error": str(e)},
                        )

        user_id = verify_slot_ownership(
            slot_id, current_user_id, db, allow_if_none=True
        )
        # Get the correct database instance for the user (might be different from db if we found slot in different project)
        db = get_db(user_id=user_id)

        # Update slot
        update_data = slot_update.dict(exclude_unset=True)
        logger.info(
            "slot_update_attempt",
            extra={"slot_id": slot_id, "update_fields": list(update_data.keys())},
        )
        success = db.update_class_slot(slot_id, **update_data)

        if not success:
            # Verify slot exists to provide better error message
            slot_check = db.get_slot(slot_id)
            if not slot_check:
                raise HTTPException(
                    status_code=404, detail=f"Slot not found: {slot_id}"
                )
            else:
                # Slot exists but update failed for another reason
                logger.error(
                    "slot_update_returned_false",
                    extra={
                        "slot_id": slot_id,
                        "update_fields": list(update_data.keys()),
                    },
                )
                raise HTTPException(
                    status_code=500, detail=f"Failed to update slot: {slot_id}"
                )

        slot = db.get_slot(slot_id)
        logger.info("slot_updated", extra={"slot_id": slot_id})
        return slot
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e) if str(e) else repr(e)
        logger.error(
            "slot_update_failed",
            extra={
                "error": error_msg,
                "slot_id": slot_id,
                "error_type": type(e).__name__,
            },
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to update slot: {error_msg}"
        )


@router.delete("/slots/{slot_id}", tags=["Class Slots"])
@rate_limit_auth
async def delete_class_slot(
    request: Request,
    slot_id: str,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """
    Delete a class slot.

    Args:
        slot_id: Slot ID
        current_user_id: Current authenticated user ID (from X-Current-User-Id header)

    Returns:
        Success message
    """
    logger.info("slot_delete_requested", extra={"slot_id": slot_id})

    try:
        # Get the slot to find its user_id and verify ownership
        # For SQLite, we can directly query. For Supabase, we need to find the project first.
        db = get_db()
        user_id = verify_slot_ownership(
            slot_id, current_user_id, db, allow_if_none=True
        )
        db = get_db(user_id=user_id)

        success = db.delete_class_slot(slot_id)

        if not success:
            raise HTTPException(status_code=404, detail=f"Slot not found: {slot_id}")

        logger.info("slot_deleted", extra={"slot_id": slot_id})
        return {"success": True, "message": "Slot deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("slot_delete_failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to delete slot: {str(e)}")


# Schedule Management Endpoints


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
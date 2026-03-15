"""
Users API endpoints.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.authorization import get_current_user_id, verify_user_access
from backend.database import get_db
from backend.models import UserCreate, UserResponse, UserUpdate
from backend.rate_limiter import rate_limit_auth, rate_limit_general
from backend.telemetry import logger
from backend.utils.date_formatter import normalize_week_of_for_match
from backend.week_detector import detect_weeks_from_folder, format_week_display

from backend.routers.users_list_logic import fetch_active_users

router = APIRouter()


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
        return fetch_active_users()
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

        # Prefer database so order is "most recent first" (generated_at desc), matching Android.
        # Use folder detection only when database has no weeks.
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

        # Format for frontend; normalize week_of to canonical so selector gets one format
        for week_of in unique_weeks:
            canonical_week = normalize_week_of_for_match(week_of) or week_of
            display = format_week_display({"week_of": canonical_week, "folder_name": canonical_week or ""})
            result.append(
                {
                    "week_of": canonical_week,
                    "display": display,
                    "folder_name": canonical_week,
                }
            )

        source = "database"

        # If database had no weeks, try folder detection (e.g. base_path_override)
        if not result and user.base_path_override:
            try:
                logger.info(
                    "detecting_weeks_from_folder",
                    extra={"path": user.base_path_override, "user_id": user_id},
                )
                detected_weeks = detect_weeks_from_folder(
                    user.base_path_override, limit=limit
                )
                if detected_weeks:
                    source = "folder"
                    for week_info in detected_weeks:
                        week_of = week_info.get("week_of")
                        folder_name = week_info.get("folder_name", week_of)
                        if week_of:
                            canonical_week = normalize_week_of_for_match(week_of) or week_of
                            display = format_week_display({"week_of": canonical_week, "folder_name": folder_name or canonical_week})
                            result.append(
                                {
                                    "week_of": canonical_week,
                                    "display": display,
                                    "folder_name": folder_name,
                                }
                            )
                    logger.info(
                        "weeks_detected_from_folder",
                        extra={"count": len(result), "user_id": user_id},
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

        logger.info(
            "recent_weeks_found", extra={"count": len(result), "source": source}
        )
        return result

    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        logger.error(
            "recent_weeks_error", extra={"error": str(e), "traceback": error_details}
        )
        raise HTTPException(status_code=500, detail=f"Failed to detect weeks: {str(e)}")


@router.get("/users/{user_id}/available-weeks", tags=["Users"])
@rate_limit_general
async def get_available_weeks(
    request: Request,
    user_id: str,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """
    Get all available week folders from the user's lesson plan directory (YY W## format).

    Scans user's base_path_override for week subfolders (e.g. 25 W36, 25 W37)
    and returns them for the Generate Weekly Plan selector.

    Args:
        user_id: User ID
        current_user_id: Current authenticated user ID (from X-Current-User-Id header)

    Returns:
        List of { week_of, display, folder_name } in YY W## format; empty if no path configured.
    """
    logger.info("available_weeks_requested", extra={"user_id": user_id})

    try:
        verify_user_access(user_id, current_user_id, allow_if_none=True)

        db = get_db(user_id=user_id)
        user = db.get_user(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.base_path_override:
            logger.info("available_weeks_no_path", extra={"user_id": user_id})
            return []

        detected_weeks = detect_weeks_from_folder(
            user.base_path_override, limit=500
        )
        result = []
        for week_info in detected_weeks:
            folder_name = week_info.get("folder_name") or ""
            if folder_name:
                result.append(
                    {
                        "week_of": folder_name,
                        "display": folder_name,
                        "folder_name": folder_name,
                    }
                )

        logger.info(
            "available_weeks_found",
            extra={"user_id": user_id, "count": len(result)},
        )
        return result

    except HTTPException:
        raise
    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        logger.error(
            "available_weeks_error",
            extra={"error": str(e), "traceback": error_details},
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to list available weeks: {str(e)}"
        )


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


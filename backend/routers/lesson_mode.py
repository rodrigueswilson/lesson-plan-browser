"""
Lesson mode session API endpoints.
"""
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.authorization import get_current_user_id, verify_user_access
from backend.database import get_db
from backend.models import LessonModeSessionCreate, LessonModeSessionResponse
from backend.rate_limiter import rate_limit_auth, rate_limit_general
from backend.telemetry import logger

router = APIRouter()


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
        return LessonModeSessionResponse.model_validate(session)
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

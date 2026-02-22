"""
Class slots API endpoints.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.authorization import get_current_user_id, verify_slot_ownership, verify_user_access
from backend.config import settings
from backend.database import get_db
from backend.models import ClassSlotCreate, ClassSlotResponse, ClassSlotUpdate
from backend.rate_limiter import rate_limit_auth, rate_limit_general
from backend.telemetry import logger

router = APIRouter()


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

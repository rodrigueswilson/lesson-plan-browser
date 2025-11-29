"""
Authorization helpers for API endpoints.

Provides user access verification to prevent unauthorized access to other users' data.

Security Notes:
- Header-based authentication is acceptable for desktop app with local backend
- For production web apps, use JWT tokens with Supabase Auth
- Never log sensitive user data (PII) in authorization logs
"""

import re
from fastapi import Header, HTTPException
from typing import Optional

from backend.telemetry import logger

# Pattern for valid UUID-like user IDs (alphanumeric, dashes, underscores)
USER_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')


def _sanitize_user_id(user_id: str) -> str:
    """
    Sanitize user ID for logging (remove PII, truncate if needed).
    
    Args:
        user_id: User ID to sanitize
    
    Returns:
        Sanitized user ID (first 8 chars + "..." if long)
    """
    if not user_id:
        return "empty"
    # Truncate long IDs, show first 8 chars
    if len(user_id) > 12:
        return f"{user_id[:8]}..."
    return user_id


def _validate_user_id_format(user_id: str) -> bool:
    """
    Validate user ID format (basic sanity check).
    
    Args:
        user_id: User ID to validate
    
    Returns:
        True if format is valid
    """
    if not user_id or not isinstance(user_id, str):
        return False
    if len(user_id) > 255:  # Reasonable max length
        return False
    return bool(USER_ID_PATTERN.match(user_id))


def verify_user_access(
    requested_user_id: str,
    current_user_id: Optional[str] = None,
    allow_if_none: bool = True,
) -> None:
    """
    Verify that the current user is authorized to access the requested user's data.
    
    Args:
        requested_user_id: The user_id from the request path/body
        current_user_id: The authenticated user's ID (from header/token)
        allow_if_none: If True, allow access when current_user_id is None (for backward compatibility)
    
    Raises:
        HTTPException: 403 if access is denied, 400 if user_id format is invalid
    """
    # Validate requested_user_id format
    if not _validate_user_id_format(requested_user_id):
        logger.warning(
            "authorization_invalid_user_id",
            extra={
                "reason": "invalid_format",
                "user_id_length": len(requested_user_id) if requested_user_id else 0,
            },
        )
        raise HTTPException(
            status_code=400,
            detail="Invalid user ID format",
        )
    
    # If no current_user_id provided and we allow it, skip check (backward compatibility)
    if current_user_id is None and allow_if_none:
        logger.warning(
            "authorization_skipped",
            extra={
                "reason": "no_current_user_id",
                "requested_user_id": _sanitize_user_id(requested_user_id),
            },
        )
        return
    
    # Validate current_user_id format if provided
    if current_user_id and not _validate_user_id_format(current_user_id):
        logger.warning(
            "authorization_invalid_current_user_id",
            extra={
                "reason": "invalid_format",
                "user_id_length": len(current_user_id) if current_user_id else 0,
            },
        )
        raise HTTPException(
            status_code=400,
            detail="Invalid current user ID format",
        )
    
    # Verify user IDs match
    if current_user_id != requested_user_id:
        logger.warning(
            "authorization_denied",
            extra={
                "current_user_id": _sanitize_user_id(current_user_id) if current_user_id else None,
                "requested_user_id": _sanitize_user_id(requested_user_id),
                "mismatch": True,
            },
        )
        raise HTTPException(
            status_code=403,
            detail="Access denied: Cannot access this user's data",
        )
    
    logger.debug(
        "authorization_granted",
        extra={"user_id": _sanitize_user_id(requested_user_id)},
    )


def get_current_user_id(
    x_current_user_id: Optional[str] = Header(
        None,
        alias="X-Current-User-Id",
        description="Current authenticated user ID",
    ),
) -> Optional[str]:
    """
    Extract current user ID from request header.
    
    This is a FastAPI dependency that can be used in route handlers.
    
    Args:
        x_current_user_id: User ID from X-Current-User-Id header
    
    Returns:
        User ID string or None if not provided
    """
    return x_current_user_id


def verify_slot_ownership(
    slot_id: str,
    current_user_id: Optional[str],
    db,
    allow_if_none: bool = True,
) -> str:
    """
    Verify that the current user owns the slot, and return the slot's user_id.
    
    Args:
        slot_id: The slot ID to check
        current_user_id: The authenticated user's ID
        db: Database instance
        allow_if_none: If True, allow access when current_user_id is None
    
    Returns:
        The user_id that owns the slot
    
    Raises:
        HTTPException: 404 if slot not found, 403 if access denied, 400 if slot_id format is invalid
    """
    # Validate slot_id format
    if not _validate_user_id_format(slot_id):
        logger.warning(
            "authorization_invalid_slot_id",
            extra={
                "reason": "invalid_format",
                "slot_id_length": len(slot_id) if slot_id else 0,
            },
        )
        raise HTTPException(
            status_code=400,
            detail="Invalid slot ID format",
        )
    
    # Get slot to find its owner
    slot = db.get_slot(slot_id)
    if not slot:
        logger.warning(
            "authorization_slot_not_found",
            extra={"slot_id": _sanitize_user_id(slot_id)},
        )
        raise HTTPException(status_code=404, detail="Slot not found")
    
    slot_user_id = None
    if isinstance(slot, dict):
        slot_user_id = slot.get("user_id")
    else:
        slot_user_id = getattr(slot, "user_id", None)
        if slot_user_id is None and hasattr(slot, "model_dump"):
            slot_dict = slot.model_dump(exclude_unset=False)  # type: ignore[attr-defined]
            slot_user_id = slot_dict.get("user_id")

    if not slot_user_id:
        logger.error(
            "authorization_slot_missing_user_id",
            extra={"slot_id": _sanitize_user_id(slot_id)},
        )
        raise HTTPException(status_code=500, detail="Slot data integrity error")
    
    # Verify ownership
    verify_user_access(slot_user_id, current_user_id, allow_if_none=allow_if_none)
    
    return slot_user_id


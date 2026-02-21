"""
Settings API endpoints (e.g. Supabase sync toggle).
"""
from fastapi import APIRouter, Body

from backend.settings_store import (
    get_supabase_sync_enabled,
    set_supabase_sync_enabled,
)
from backend.telemetry import logger

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/supabase-sync")
async def get_supabase_sync_setting():
    """
    Get the Supabase sync enabled setting.
    """
    return {"enable_supabase_sync": get_supabase_sync_enabled()}


@router.put("/supabase-sync")
async def set_supabase_sync_setting(enabled: bool = Body(..., embed=True)):
    """
    Set the Supabase sync enabled setting.

    Args:
        enabled: Boolean to enable/disable Supabase sync (sent in request body as {"enabled": true/false})
    """
    set_supabase_sync_enabled(enabled)
    logger.info(f"Supabase sync setting updated: {enabled}")
    return {"enable_supabase_sync": enabled, "message": "Setting updated successfully"}

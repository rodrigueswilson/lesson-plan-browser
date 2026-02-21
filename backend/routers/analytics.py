from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse

from backend.authorization import get_current_user_id
from backend.performance_tracker import get_tracker

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
async def get_analytics_summary(
    days: int = Query(30, ge=1, le=365),
    user_id: Optional[str] = Depends(get_current_user_id),
):
    """Get aggregate analytics summary."""
    tracker = get_tracker()
    return tracker.get_aggregate_stats(days=days, user_id=user_id)


@router.get("/daily")
async def get_daily_analytics(
    days: int = Query(30, ge=1, le=365),
    user_id: Optional[str] = Depends(get_current_user_id),
):
    """Get daily analytics breakdown."""
    tracker = get_tracker()
    return tracker.get_daily_breakdown(days=days, user_id=user_id)


@router.get("/sessions")
async def get_session_analytics(
    days: int = Query(30, ge=1, le=365),
    user_id: Optional[str] = Depends(get_current_user_id),
):
    """Get session-by-session analytics."""
    tracker = get_tracker()
    return tracker.get_session_breakdown(days=days, user_id=user_id)


@router.get("/operations")
async def get_operation_analytics(
    days: int = Query(30, ge=1, le=365),
    user_id: Optional[str] = Depends(get_current_user_id),
):
    """Get time breakdown by operation type."""
    tracker = get_tracker()
    return tracker.get_operation_stats(days=days, user_id=user_id)


@router.get("/errors")
async def get_error_analytics(
    days: int = Query(30, ge=1, le=365),
    user_id: Optional[str] = Depends(get_current_user_id),
):
    """Get success vs failure analytics."""
    tracker = get_tracker()
    return tracker.get_error_stats(days=days, user_id=user_id)


@router.get("/parallel")
async def get_parallel_processing_analytics(
    days: int = Query(30, ge=1, le=365),
    user_id: Optional[str] = Depends(get_current_user_id),
):
    """Get parallel processing analytics."""
    tracker = get_tracker()
    return tracker.get_parallel_processing_stats(days=days, user_id=user_id)


@router.get("/export")
async def export_analytics_csv(
    days: int = Query(30, ge=1, le=365),
    user_id: Optional[str] = Depends(get_current_user_id),
):
    """Export analytics data as CSV."""
    tracker = get_tracker()
    csv_data = tracker.export_analytics_csv(days=days, user_id=user_id)
    
    filename = f"analytics_export_{datetime.now().strftime('%Y%m%d')}.csv"
    
    return PlainTextResponse(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

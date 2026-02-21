"""
Health, system redirects, metrics, and admin maintenance endpoints.
"""
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import RedirectResponse, Response

from backend.config import settings
from backend.maintenance import DatabaseMaintenance, run_maintenance
from backend.metrics import get_metrics_response
from backend.models import HealthResponse
from backend.telemetry import logger
from backend.week_detector import detect_weeks_from_folder

router = APIRouter(tags=["System"])


@router.get("/", status_code=307)
async def root():
    """
    Root endpoint - redirects to API documentation.
    """
    return RedirectResponse(url="/api/docs", status_code=307)


@router.get("/docs", status_code=307)
async def docs_redirect():
    """
    Convenience endpoint - redirects /docs to /api/docs.
    """
    return RedirectResponse(url="/api/docs", status_code=307)


@router.get("/api/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    """
    logger.info("health_check_requested")
    return HealthResponse(
        status="healthy", version="1.0.0", timestamp=datetime.utcnow().isoformat()
    )


@router.get("/api/health/database")
async def database_health():
    """
    Check which database backend is being used.
    """
    db_type = "Supabase" if settings.USE_SUPABASE else "SQLite"

    info = {
        "database_type": db_type,
        "use_supabase": settings.USE_SUPABASE,
        "supabase_project": settings.SUPABASE_PROJECT
        if settings.USE_SUPABASE
        else None,
    }

    if settings.USE_SUPABASE:
        info["supabase_url_project1"] = bool(settings.SUPABASE_URL_PROJECT1)
        info["supabase_url_project2"] = bool(settings.SUPABASE_URL_PROJECT2)

    return info


@router.get("/api/health/redis")
async def redis_health():
    """
    Check Redis connection health for rate limiting.
    """
    from backend.rate_limiter import (
        get_redis_circuit_breaker_status,
        test_redis_connection,
    )

    if not settings.REDIS_URL:
        return {
            "status": "not_configured",
            "message": "Redis not configured, using in-memory storage",
            "storage_type": "memory",
        }

    is_healthy = test_redis_connection()
    circuit_breaker = get_redis_circuit_breaker_status()

    response = {
        "status": "healthy" if is_healthy else "unhealthy",
        "redis_url": settings.REDIS_URL.split("@")[-1]
        if "@" in settings.REDIS_URL
        else settings.REDIS_URL,
        "storage_type": "redis",
        "key_prefix": settings.REDIS_KEY_PREFIX,
        "environment": settings.REDIS_ENVIRONMENT,
        "circuit_breaker": circuit_breaker,
    }

    if circuit_breaker["circuit_open"]:
        response["warning"] = "Circuit breaker is open - rate limiting may be degraded"
    if circuit_breaker["fallback_count"] > 0:
        response["warning"] = (
            f"Fallback to memory occurred {circuit_breaker['fallback_count']} times"
        )

    return response


@router.get("/metrics")
async def metrics_endpoint():
    """
    Prometheus metrics endpoint.
    """
    metrics_data, content_type = get_metrics_response()
    return Response(content=metrics_data, media_type=content_type)


@router.get("/api/admin/maintenance/stats")
async def get_maintenance_stats():
    """Get database maintenance statistics."""
    try:
        m = DatabaseMaintenance()
        return m.get_stats()
    except Exception as e:
        logger.error(f"Error getting maintenance stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/admin/maintenance")
async def trigger_maintenance(background_tasks: BackgroundTasks):
    """Trigger full database maintenance."""
    try:
        background_tasks.add_task(run_maintenance)
        return {
            "status": "started",
            "message": "Database maintenance started in background",
        }
    except Exception as e:
        logger.error(f"Error triggering maintenance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/test-weeks")
async def test_week_detection(
    path: str = "F:/rodri/Documents/OneDrive/AS/Lesson Plan",
):
    """
    Test week detection with a specific path (for debugging).
    """
    weeks = detect_weeks_from_folder(path, limit=10)
    return {"path": path, "weeks_found": len(weeks), "weeks": weeks}

"""
FastAPI Backend for Bilingual Lesson Plan Builder.

Provides REST API endpoints for:
- JSON validation
- DOCX rendering
- Progress streaming (SSE)
- Health checks
"""

import json
import sys

# FORCE UTF-8 ENCODING FOR STDOUT/STDERR (Windows Fix)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, Body, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from sse_starlette.sse import EventSourceResponse

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.authorization import (
    get_current_user_id,
    verify_slot_ownership,
    verify_user_access,
)
from backend.config import settings
from backend.database import get_db
from backend.errors import (
    RenderError,
    TemplateNotFoundError,
    ValidationError,
    general_exception_handler,
    render_error_handler,
    validation_error_handler,
)
from backend.llm_service import get_llm_service
from backend.maintenance import DatabaseMaintenance, run_maintenance
from backend.metrics import get_metrics_response
from backend.mock_llm_service import get_mock_llm_service
from backend.models import (
    BatchProcessRequest,
    BatchProcessResponse,
    ClassSlotCreate,
    ClassSlotResponse,
    ClassSlotUpdate,
    HealthResponse,
    LessonModeSessionCreate,
    LessonModeSessionResponse,
    LessonPlanDetailResponse,
    LessonStepResponse,
    RenderRequest,
    RenderResponse,
    ScheduleBulkCreateRequest,
    ScheduleBulkCreateResponse,
    ScheduleEntryCreate,
    ScheduleEntryResponse,
    ScheduleEntryUpdate,
    TabletExportDbCounts,
    TabletExportDbRequest,
    TabletExportDbResponse,
    TransformRequest,
    TransformResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
    ValidationRequest,
    ValidationResponse,
    WeeklyPlanResponse,
    WeekStatusResponse,
)
from backend.models import ValidationError as ValidationErrorModel
from backend.performance_tracker import get_tracker
from backend.progress import simulate_render_progress, stream_render_progress
from backend.rate_limiter import (
    rate_limit_auth,
    rate_limit_batch,
    rate_limit_general,
    setup_rate_limiting,
)
from backend.routers.analytics import router as analytics_router
from backend.services.objectives_utils import normalize_objectives_in_lesson
from backend.services.sorting_utils import sort_slots
from backend.settings_store import (
    get_supabase_sync_enabled,
    set_supabase_sync_enabled,
)
from backend.tablet_db_export import TabletDbExportError, export_user_tablet_db
from backend.telemetry import logger
from backend.utils.schedule_utils import prepare_schedule_entry
from backend.week_detector import detect_weeks_from_folder, format_week_display
from tools.batch_processor import BatchProcessor
from tools.docx_renderer import DOCXRenderer
from tools.json_repair import repair_json
from tools.validate_schema import load_schema
from tools.validate_schema import validate_json as validate_schema

# Load schema once at startup
SCHEMA_PATH = Path("schemas/lesson_output_schema.json")
SCHEMA = load_schema(SCHEMA_PATH)

# Initialize FastAPI app
app = FastAPI(
    title="Bilingual Lesson Plan Builder API",
    description="REST API for generating bilingual lesson plans with WIDA support",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Include Analytics Router (prefix=/api so routes are /api/analytics/*)
app.include_router(analytics_router, prefix="/api")

# Add CORS middleware for Tauri frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register error handlers
app.add_exception_handler(ValidationError, validation_error_handler)
app.add_exception_handler(RenderError, render_error_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Set up rate limiting
setup_rate_limiting(app)

# Add rate limit metrics middleware (optional - tracks allowed requests)
# Note: Blocked requests are tracked in exception handler
try:
    from backend.rate_limit_middleware import RateLimitMetricsMiddleware

    app.add_middleware(RateLimitMetricsMiddleware)
except ImportError:
    # Metrics not available, skip middleware
    pass


# Startup and shutdown event handlers
@app.on_event("startup")
async def startup_event():
    """
    Initialize application on startup.
    """
    import gc

    try:
        # Initialize database connection early to catch any issues
        db = get_db()
        # Try to verify database is working by checking if we can access it
        try:
            # Simple test query - just check if we can get a connection
            if hasattr(db, "engine"):
                # SQLite database - connection is verified
                logger.info("Database initialized successfully (SQLite)")
            elif hasattr(db, "client"):
                # Supabase database - connection is verified
                logger.info("Database initialized successfully (Supabase)")
            else:
                logger.warning("Database initialized but type unknown")
        except Exception as db_test_error:
            logger.warning(
                f"Database initialized but test query failed: {db_test_error}",
                exc_info=True,
            )

        # Clean up old completed tasks in progress tracker
        from backend.progress import progress_tracker

        progress_tracker._cleanup_old_tasks()

        # Force garbage collection
        gc.collect()
        print("Cache cleared on startup")
        logger.info("Application startup completed")
    except Exception as e:
        logger.error(
            f"Startup error during database initialization: {e}",
            exc_info=True,
        )
        # Don't raise - let the app start anyway, errors will be caught on first request
        # This allows graceful degradation if database is temporarily unavailable
        print(f"Warning: Startup initialization had issues: {e}")
        print("Application will continue to start, but database operations may fail.")


def enrich_lesson_json_with_times(lesson_json: Dict[str, Any], user_id: str) -> None:
    """Enrich lesson_json with start_time and end_time from schedules table.

    Matches slots to schedule entries by (day, subject, grade, homeroom) since schedule
    slot_numbers may differ from class slot_numbers. This ensures correct chronological
    ordering for each day based on the actual schedule, considering all three attributes:
    subject, grade, and room (homeroom).
    """
    if not lesson_json or "days" not in lesson_json:
        return

    db = get_db(user_id=user_id)
    schedule = db.get_user_schedule(user_id=user_id)

    # Build maps for flexible matching
    # Map (day, subject, grade, homeroom) -> list of (start_time, end_time, slot_number)
    # This allows matching by all three attributes even if slot_numbers don't match
    full_match_map = {}
    # Map (day, subject, grade) -> list of (start_time, end_time, slot_number, homeroom)
    # Fallback if homeroom doesn't match
    subject_grade_map = {}
    # Map (day, subject) -> list of (start_time, end_time, slot_number, grade, homeroom)
    # Fallback if grade/homeroom don't match
    subject_time_map = {}
    # Map (day, slot_number, subject) -> (start_time, end_time) for exact slot matches
    exact_map = {}

    def normalize_value(val):
        """Normalize a value for comparison (lowercase, strip, handle None)."""
        if val is None:
            return None
        return str(val).lower().strip() if str(val).strip() else None

    for entry in schedule:
        day = entry.day_of_week.lower()
        slot_num = entry.slot_number
        subject = normalize_value(entry.subject)
        grade = normalize_value(entry.grade)
        homeroom = normalize_value(entry.homeroom)

        # Exact match map (day, slot_number, subject)
        exact_map[(day, slot_num, subject)] = (entry.start_time, entry.end_time)

        # Full match: (day, subject, grade, homeroom)
        key_full = (day, subject, grade, homeroom)
        if key_full not in full_match_map:
            full_match_map[key_full] = []
        full_match_map[key_full].append((entry.start_time, entry.end_time, slot_num))

        # Subject + Grade match: (day, subject, grade)
        key_sg = (day, subject, grade)
        if key_sg not in subject_grade_map:
            subject_grade_map[key_sg] = []
        subject_grade_map[key_sg].append(
            (entry.start_time, entry.end_time, slot_num, homeroom)
        )

        # Subject only match: (day, subject)
        key_subj = (day, subject)
        if key_subj not in subject_time_map:
            subject_time_map[key_subj] = []
        subject_time_map[key_subj].append(
            (entry.start_time, entry.end_time, slot_num, grade, homeroom)
        )

    # Sort all map entries by time
    for key in full_match_map:
        full_match_map[key].sort(key=lambda x: x[0])
    for key in subject_grade_map:
        subject_grade_map[key].sort(key=lambda x: x[0])
    for key in subject_time_map:
        subject_time_map[key].sort(key=lambda x: x[0])

    for day_name, day_data in lesson_json["days"].items():
        day_lower = day_name.lower()
        slots = day_data.get("slots", [])

        if not isinstance(slots, list):
            if isinstance(slots, dict):
                slots = list(slots.values())
            else:
                continue

        # Track which schedule entries we've already used for each subject
        # This ensures we match slots to schedule entries in chronological order
        used_entries = {}  # (day, subject) -> list of used indices

        def get_times(slot_dict, slot_index_in_day):
            """Get times for a slot, trying multiple matching strategies.

            Tries matching in order of specificity:
            1. Exact match by (day, slot_number, subject)
            2. Full match by (day, subject, grade, homeroom)
            3. Match by (day, subject, grade)
            4. Match by (day, subject) - fallback
            """
            slot_num = slot_dict.get("slot_number")
            subject = normalize_value(slot_dict.get("subject"))
            grade = normalize_value(slot_dict.get("grade"))
            homeroom = normalize_value(slot_dict.get("homeroom"))

            if not subject:
                return None

            # Strategy 1: Exact match by (day, slot_number, subject)
            if slot_num is not None:
                times = exact_map.get((day_lower, slot_num, subject))
                if times:
                    return times

            # Strategy 2: Full match by (day, subject, grade, homeroom)
            key_full = (day_lower, subject, grade, homeroom)
            candidates = full_match_map.get(key_full, [])
            if candidates:
                key = key_full
                if key not in used_entries:
                    used_entries[key] = []
                existing_time = slot_dict.get("start_time")
                if existing_time:
                    for idx, (start_time, end_time, _) in enumerate(candidates):
                        if start_time == existing_time and idx not in used_entries[key]:
                            used_entries[key].append(idx)
                            return (start_time, end_time)
                for idx, (start_time, end_time, _) in enumerate(candidates):
                    if idx not in used_entries[key]:
                        used_entries[key].append(idx)
                        return (start_time, end_time)

            # Strategy 3: Match by (day, subject, grade)
            if grade:
                key_sg = (day_lower, subject, grade)
                candidates = subject_grade_map.get(key_sg, [])
                if candidates:
                    key = key_sg
                    if key not in used_entries:
                        used_entries[key] = []
                    existing_time = slot_dict.get("start_time")
                    if existing_time:
                        for idx, (start_time, end_time, _, _) in enumerate(candidates):
                            if (
                                start_time == existing_time
                                and idx not in used_entries[key]
                            ):
                                used_entries[key].append(idx)
                                return (start_time, end_time)
                    for idx, (start_time, end_time, _, _) in enumerate(candidates):
                        if idx not in used_entries[key]:
                            used_entries[key].append(idx)
                            return (start_time, end_time)

            # Strategy 4: Match by (day, subject) - fallback
            key_subj = (day_lower, subject)
            candidates = subject_time_map.get(key_subj, [])
            if not candidates:
                return None

            if key_subj not in used_entries:
                used_entries[key_subj] = []

            existing_time = slot_dict.get("start_time")
            if existing_time:
                for idx, (start_time, end_time, _, _, _) in enumerate(candidates):
                    if (
                        start_time == existing_time
                        and idx not in used_entries[key_subj]
                    ):
                        used_entries[key_subj].append(idx)
                        return (start_time, end_time)

            for idx, (start_time, end_time, _, _, _) in enumerate(candidates):
                if idx not in used_entries[key_subj]:
                    used_entries[key_subj].append(idx)
                    return (start_time, end_time)

            return None

        # Sort slots by their current start_time (if available) or slot_number
        # This ensures we match them to schedule entries in the right order
        def get_slot_sort_key(slot):
            start_time = slot.get("start_time", "")
            slot_num = slot.get("slot_number", 0)
            try:
                slot_num = int(slot_num)
            except (ValueError, TypeError):
                slot_num = 0

            if start_time:
                try:
                    parts = str(start_time).split(":")
                    if len(parts) >= 2:
                        time_sort = int(parts[0]) * 60 + int(parts[1])
                        return (0, time_sort, slot_num)
                except (ValueError, TypeError):
                    pass
            return (1, 0, slot_num)

        # Sort slots to match them in chronological order
        sorted_slots = sorted(
            [s for s in slots if isinstance(s, dict)], key=get_slot_sort_key
        )

        # Now match each slot to schedule entries
        for slot in sorted_slots:
            times = get_times(slot, None)
            if times:
                slot["start_time"] = times[0]
                slot["end_time"] = times[1]

        # Re-sort slots after updating times to ensure chronological order
        final_slots = sort_slots(sorted_slots)

        # Update the original slots list with correctly sorted order
        # Always update day_data["slots"] with enriched and sorted slots
        day_data["slots"] = final_slots


@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleanup on shutdown to free memory.
    """
    import gc

    try:
        # Save progress tracker state before shutdown
        from backend.progress import progress_tracker

        progress_tracker._save_state()

        gc.collect()  # Force garbage collection
        print("✓ Cache cleared on shutdown")
        logger.info("Application shutdown completed")
    except Exception as e:
        logger.error(f"Shutdown error: {e}", exc_info=True)


@app.get("/", tags=["System"], status_code=307)
async def root():
    """
    Root endpoint - redirects to API documentation.

    Returns:
        Redirect response to /api/docs
    """
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/api/docs", status_code=307)


@app.get("/docs", tags=["System"], status_code=307)
async def docs_redirect():
    """
    Convenience endpoint - redirects /docs to /api/docs.

    Returns:
        Redirect response to /api/docs
    """
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/api/docs", status_code=307)


@app.get("/api/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Health check endpoint.

    Returns:
        HealthResponse with status and version
    """
    logger.info("health_check_requested")
    return HealthResponse(
        status="healthy", version="1.0.0", timestamp=datetime.utcnow().isoformat()
    )


@app.get("/api/health/database", tags=["System"])
async def database_health():
    """
    Check which database backend is being used.

    Returns:
        Dictionary with database type and configuration
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


@app.post(
    "/api/tablet/export-db", response_model=TabletExportDbResponse, tags=["Tablet"]
)
async def export_tablet_db(
    request: TabletExportDbRequest,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """
    Export a user-only SQLite DB suitable for bundling into the tablet APK.

    Output path:
      data/tablet_db_exports/<user_id>/lesson_planner.db
    """
    user_id = request.user_id
    verify_user_access(
        user_id, current_user_id
    )  # header optional, enforced if provided

    source_db = settings.SQLITE_DB_PATH
    output_path = Path("data") / "tablet_db_exports" / user_id / "lesson_planner.db"
    output_path = (Path(__file__).resolve().parents[1] / output_path).resolve()

    try:
        result = export_user_tablet_db(
            source_db_path=source_db,
            user_id=user_id,
            output_db_path=output_path,
            vacuum=True,
            keep_previous_backup=True,
        )
        return TabletExportDbResponse(
            user_id=result.user_id,
            output_path=result.output_path,
            output_bytes=result.output_bytes,
            created_at=result.created_at,
            counts=TabletExportDbCounts(
                users=result.counts.users,
                class_slots=result.counts.class_slots,
                weekly_plans=result.counts.weekly_plans,
                schedules=result.counts.schedules,
                lesson_steps=result.counts.lesson_steps,
                lesson_mode_sessions=result.counts.lesson_mode_sessions,
            ),
        )
    except TabletDbExportError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # noqa: BLE001
        logger.exception("Tablet DB export failed")
        raise HTTPException(status_code=500, detail=f"Tablet DB export failed: {e}")


@app.get("/api/settings/supabase-sync", tags=["Settings"])
async def get_supabase_sync_setting():
    """
    Get the Supabase sync enabled setting.

    Returns:
        Dictionary with enable_supabase_sync boolean
    """
    return {"enable_supabase_sync": get_supabase_sync_enabled()}


@app.put("/api/settings/supabase-sync", tags=["Settings"])
async def set_supabase_sync_setting(enabled: bool = Body(..., embed=True)):
    """
    Set the Supabase sync enabled setting.

    Args:
        enabled: Boolean to enable/disable Supabase sync (sent in request body as {"enabled": true/false})

    Returns:
        Dictionary with updated setting
    """
    set_supabase_sync_enabled(enabled)
    logger.info(f"Supabase sync setting updated: {enabled}")
    return {"enable_supabase_sync": enabled, "message": "Setting updated successfully"}


@app.get("/api/health/redis", tags=["System"])
async def redis_health():
    """
    Check Redis connection health for rate limiting.

    Returns:
        Dictionary with Redis status, configuration, and circuit breaker metrics
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

    # Add warning if circuit breaker is open or fallback is happening
    if circuit_breaker["circuit_open"]:
        response["warning"] = "Circuit breaker is open - rate limiting may be degraded"
    if circuit_breaker["fallback_count"] > 0:
        response["warning"] = (
            f"Fallback to memory occurred {circuit_breaker['fallback_count']} times"
        )

    return response


@app.get("/metrics", tags=["System"])
async def metrics_endpoint():
    """
    Prometheus metrics endpoint.

    Returns:
        Prometheus-formatted metrics
    """
    metrics_data, content_type = get_metrics_response()
    return Response(content=metrics_data, media_type=content_type)


@app.get("/api/admin/maintenance/stats", tags=["System"])
async def get_maintenance_stats():
    """Get database maintenance statistics."""
    try:
        m = DatabaseMaintenance()
        return m.get_stats()
    except Exception as e:
        logger.error(f"Error getting maintenance stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/maintenance", tags=["System"])
async def trigger_maintenance(background_tasks: BackgroundTasks):
    """Trigger full database maintenance."""
    try:
        # Run in background to avoid timeout
        background_tasks.add_task(run_maintenance)
        return {
            "status": "started",
            "message": "Database maintenance started in background",
        }
    except Exception as e:
        logger.error(f"Error triggering maintenance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/test-weeks", tags=["System"])
async def test_week_detection(path: str = "F:/rodri/Documents/OneDrive/AS/Lesson Plan"):
    """
    Test week detection with a specific path (for debugging).

    Args:
        path: Path to scan (default: user's lesson plan folder)

    Returns:
        Detected weeks and debug info
    """
    weeks = detect_weeks_from_folder(path, limit=10)
    return {"path": path, "weeks_found": len(weeks), "weeks": weeks}


@app.post("/api/validate", response_model=ValidationResponse, tags=["Validation"])
async def validate_json(request: ValidationRequest):
    """
    Validate lesson plan JSON against schema.

    Args:
        request: ValidationRequest with JSON data

    Returns:
        ValidationResponse with validation results

    Raises:
        ValidationError: If validation fails
    """
    logger.info("validation_requested", extra={"has_data": bool(request.json_data)})

    try:
        # Validate against schema
        is_valid, errors = validate_schema(request.json_data, SCHEMA)

        if is_valid:
            logger.info("validation_success")
            return ValidationResponse(valid=True, errors=None)
        else:
            # Convert errors to ValidationErrorModel
            error_models = []
            for err in errors:
                if isinstance(err, dict):
                    error_models.append(
                        ValidationErrorModel(
                            field=err.get("field", "unknown"),
                            message=err.get("message", str(err)),
                            value=err.get("value"),
                        )
                    )
                else:
                    # Error is a string
                    error_models.append(
                        ValidationErrorModel(
                            field="unknown", message=str(err), value=None
                        )
                    )

            logger.warning("validation_failed", extra={"error_count": len(errors)})
            return ValidationResponse(valid=False, errors=error_models)

    except Exception as e:
        logger.error("validation_error", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")


@app.post("/api/render", response_model=RenderResponse, tags=["Rendering"])
async def render_lesson_plan(request: RenderRequest, background_tasks: BackgroundTasks):
    """
    Render lesson plan JSON to DOCX format.

    Args:
        request: RenderRequest with JSON data and options
        background_tasks: FastAPI background tasks

    Returns:
        RenderResponse with output path and metadata

    Raises:
        ValidationError: If JSON is invalid
        RenderError: If rendering fails
        TemplateNotFoundError: If template not found
    """
    logger.info(
        "render_requested",
        extra={
            "output_filename": request.output_filename,
            "template_path": request.template_path,
        },
    )

    start_time = time.time()

    try:
        # Validate JSON first
        is_valid, errors = validate_schema(request.json_data, SCHEMA)
        if not is_valid:
            logger.warning(
                "render_validation_failed", extra={"error_count": len(errors)}
            )
            raise ValidationError(errors)

        # Check template exists
        template_path = Path(request.template_path)
        if not template_path.exists():
            logger.error(
                "template_not_found", extra={"template_path": str(template_path)}
            )
            raise TemplateNotFoundError(str(template_path))

        # Create output directory
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        # Generate output path
        output_path = output_dir / request.output_filename

        # Render DOCX
        logger.info("rendering_docx", extra={"output_path": str(output_path)})
        renderer = DOCXRenderer(str(template_path))
        success = renderer.render(request.json_data, str(output_path))

        if not success:
            logger.error("render_failed")
            raise RenderError("Failed to render DOCX file")

        # Get file size
        file_size = output_path.stat().st_size
        render_time_ms = (time.time() - start_time) * 1000

        logger.info(
            "render_success",
            extra={
                "output_path": str(output_path),
                "file_size": file_size,
                "render_time_ms": render_time_ms,
            },
        )

        return RenderResponse(
            success=True,
            output_path=str(output_path),
            file_size=file_size,
            render_time_ms=render_time_ms,
        )

    except (ValidationError, TemplateNotFoundError):
        raise
    except Exception as e:
        logger.error("render_error", extra={"error": str(e)})
        raise RenderError("Rendering failed", detail=str(e))


@app.get("/api/render/{filename}", tags=["Rendering"])
async def download_rendered_file(filename: str):
    """
    Download a rendered DOCX file.

    Args:
        filename: Name of the file to download

    Returns:
        FileResponse with DOCX file

    Raises:
        HTTPException: If file not found
    """
    file_path = Path("output") / filename

    if not file_path.exists():
        logger.warning("file_not_found", extra={"filename": filename})
        raise HTTPException(status_code=404, detail="File not found")

    logger.info("file_download", extra={"filename": filename})
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@app.get("/api/plans/{plan_id}/download", tags=["Weekly Plans"])
async def download_plan_file(
    plan_id: str,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """
    Download a weekly plan file by plan ID.

    Uses the stored output_file path from the database, with proper authorization checks.

    Args:
        plan_id: Plan ID
        current_user_id: Current authenticated user ID (from X-Current-User-Id header)

    Returns:
        FileResponse with DOCX file

    Raises:
        HTTPException: If plan not found, access denied, or file not found
    """
    logger.info("plan_download_requested", extra={"plan_id": plan_id})

    try:
        # Get plan from database
        db = get_db()
        plan = db.get_weekly_plan(plan_id)

        if not plan:
            raise HTTPException(status_code=404, detail=f"Plan not found: {plan_id}")

        # Verify user access
        verify_user_access(plan.user_id, current_user_id, allow_if_none=True)

        # Get output file path
        output_file = plan.output_file
        if not output_file:
            raise HTTPException(status_code=404, detail="Plan has no output file")

        # Check if file exists
        file_path = Path(output_file)
        if not file_path.exists():
            logger.warning(
                "plan_file_not_found", extra={"plan_id": plan_id, "path": output_file}
            )
            raise HTTPException(status_code=404, detail="File not found on server")

        # Extract filename for download
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


@app.get("/api/progress", tags=["Progress"])
async def stream_progress():
    """
    Stream rendering progress via Server-Sent Events (SSE).

    Returns:
        EventSourceResponse with progress updates
    """
    logger.info("progress_stream_requested")
    return EventSourceResponse(simulate_render_progress())


@app.get("/api/progress/{task_id}", tags=["Progress"])
async def stream_task_progress(task_id: str):
    """
    Stream progress for a specific task via SSE.

    Args:
        task_id: Task ID to stream progress for

    Returns:
        EventSourceResponse with task progress updates
    """
    logger.info("task_progress_stream_requested", extra={"task_id": task_id})
    return EventSourceResponse(stream_render_progress(task_id))


@app.get("/api/progress/{task_id}/poll", tags=["Progress"])
async def poll_task_progress(task_id: str):
    """
    Poll progress for a specific task (Tauri-compatible alternative to SSE).

    Args:
        task_id: Task ID to get progress for

    Returns:
        JSON with current task progress
    """
    from backend.progress import progress_tracker

    # Debug logging
    print(f"DEBUG: Polling progress for task_id: {task_id}")
    print(f"DEBUG: Available task IDs: {list(progress_tracker.tasks.keys())[:5]}")

    # Use get_task which will try loading from persistence if not in memory
    task = progress_tracker.get_task(task_id)

    if not task:
        print(
            f"DEBUG: Task {task_id} not found in progress tracker (may have completed or expired)"
        )
        return {
            "status": "not_found",
            "progress": 0,
            "message": "Task not found. It may have completed, expired, or the server was restarted.",
            "stage": "unknown",
            "current": 0,
            "total": 0,
        }

    progress_pct = task.get("progress", 0)

    # Calculate current/total from progress percentage
    # Assume 100 total steps for simplicity
    current = int(progress_pct)
    total = 100

    print(
        f"DEBUG: Task {task_id} status: {task.get('stage')}, progress: {progress_pct}%"
    )

    return {
        "status": task.get("stage", "unknown"),
        "progress": progress_pct,
        "message": task.get("message", ""),
        "stage": task.get("stage", "unknown"),
        "current": current,
        "total": total,
    }


@app.post("/api/transform", response_model=TransformResponse, tags=["LLM"])
async def transform_lesson(request: TransformRequest):
    """
    Transform primary teacher content to bilingual lesson plan using LLM.

    Args:
        request: TransformRequest with primary content and metadata

    Returns:
        TransformResponse with generated lesson JSON

    Raises:
        HTTPException: If transformation fails
    """
    logger.info(
        "llm_transform_requested",
        extra={
            "grade": request.grade,
            "subject": request.subject,
            "provider": request.provider,
        },
    )

    start_time = time.time()

    try:
        # Try to get real LLM service. Do not fall back to mock data on failure.
        try:
            llm_service = get_llm_service(provider=request.provider)
            logger.info(
                "llm_service_initialized",
                extra={
                    "provider": request.provider,
                    "service_type": "real",
                    "message": "Using real LLM service (OpenAI/Anthropic API)",
                },
            )
        except ValueError as e:
            # API key missing or invalid
            error_msg = str(e)
            logger.error(
                "llm_service_failed_api_key",
                extra={
                    "provider": request.provider,
                    "error": error_msg,
                    "reason": "API key missing or invalid",
                },
            )
            raise HTTPException(
                status_code=500,
                detail=f"LLM Configuration Error: {error_msg}. Please check your .env file.",
            )
        except Exception as e:
            # Other initialization errors
            error_msg = str(e)
            error_type = type(e).__name__
            logger.error(
                "llm_service_failed_initialization",
                extra={
                    "provider": request.provider,
                    "error_type": error_type,
                    "error": error_msg,
                    "reason": "LLM service initialization failed",
                },
                exc_info=True,
            )
            raise HTTPException(
                status_code=500, detail=f"Failed to initialize LLM service: {error_msg}"
            )

        # Transform content
        success, lesson_json, error = llm_service.transform_lesson(
            primary_content=request.primary_content,
            grade=request.grade,
            subject=request.subject,
            week_of=request.week_of,
            teacher_name=request.teacher_name,
            homeroom=request.homeroom,
        )

        transform_time_ms = (time.time() - start_time) * 1000

        if success:
            logger.info(
                "llm_transform_success", extra={"transform_time_ms": transform_time_ms}
            )
            if isinstance(lesson_json, dict):
                normalize_objectives_in_lesson(lesson_json)
                # Enrich with schedule times
                enrich_lesson_json_with_times(
                    lesson_json,
                    request.user_id
                    if hasattr(request, "user_id")
                    else currentUser.id
                    if "currentUser" in locals()
                    else "",
                )
            return TransformResponse(
                success=True,
                lesson_json=lesson_json,
                transform_time_ms=transform_time_ms,
            )
        else:
            logger.error("llm_transform_failed", extra={"error": error})
            return TransformResponse(
                success=False, error=error, transform_time_ms=transform_time_ms
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("llm_transform_error", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Transformation failed: {str(e)}")


@app.post("/api/repair", tags=["Utilities"])
async def repair_json_endpoint(json_string: str):
    """
    Attempt to repair malformed JSON.

    Args:
        json_string: JSON string to repair

    Returns:
        Repaired JSON object

    Raises:
        HTTPException: If repair fails
    """
    logger.info("json_repair_requested")

    try:
        repaired = repair_json(json_string)
        logger.info("json_repair_success")
        return {"success": True, "repaired_json": repaired}
    except Exception as e:
        logger.error("json_repair_failed", extra={"error": str(e)})
        raise HTTPException(status_code=400, detail=f"Repair failed: {str(e)}")


# User Management Endpoints


@app.post("/api/users", response_model=UserResponse, tags=["Users"])
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


@app.get("/api/users", response_model=list[UserResponse], tags=["Users"])
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
                    logger.warning(
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
                    logger.warning(
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


@app.get("/api/recent-weeks", tags=["Users"])
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


@app.get("/api/users/{user_id}", response_model=UserResponse, tags=["Users"])
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


@app.put("/api/users/{user_id}", response_model=UserResponse, tags=["Users"])
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


@app.put("/api/users/{user_id}/base-path", response_model=UserResponse, tags=["Users"])
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


@app.put(
    "/api/users/{user_id}/template-paths", response_model=UserResponse, tags=["Users"]
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


@app.delete("/api/users/{user_id}", tags=["Users"])
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


@app.post(
    "/api/users/{user_id}/slots", response_model=ClassSlotResponse, tags=["Class Slots"]
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


@app.get(
    "/api/users/{user_id}/slots",
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


@app.put("/api/slots/{slot_id}", response_model=ClassSlotResponse, tags=["Class Slots"])
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


@app.delete("/api/slots/{slot_id}", tags=["Class Slots"])
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


@app.post("/api/schedules", response_model=ScheduleEntryResponse, tags=["Schedules"])
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


@app.get(
    "/api/schedules/{user_id}",
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


@app.get(
    "/api/schedules/{user_id}/current",
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


@app.put(
    "/api/schedules/{schedule_id}",
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


@app.delete("/api/schedules/{schedule_id}", tags=["Schedules"])
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


@app.post(
    "/api/schedules/{user_id}/bulk",
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


# Lesson Plan and Steps Endpoints


@app.get(
    "/api/plans/{plan_id}",
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

        # Debug: Check if vocabulary and sentence frames are in the response
        # Check for Monday slot 2 specifically
        monday_data = lesson_json.get("days", {}).get("monday", {})
        monday_slots = monday_data.get("slots", [])
        slot_2_data = None
        if isinstance(monday_slots, list):
            slot_2_data = next(
                (
                    s
                    for s in monday_slots
                    if isinstance(s, dict) and s.get("slot_number") == 2
                ),
                None,
            )
        if slot_2_data:
            logger.info(
                "plan_detail_slot_2_debug",
                extra={
                    "plan_id": plan_id,
                    "has_vocabulary": bool(slot_2_data.get("vocabulary_cognates")),
                    "vocab_count": len(slot_2_data.get("vocabulary_cognates", [])),
                    "has_sentence_frames": bool(slot_2_data.get("sentence_frames")),
                    "frames_count": len(slot_2_data.get("sentence_frames", [])),
                    "slot_keys": list(slot_2_data.keys())[:20],
                },
            )
            # Also print to console for immediate visibility
            print(
                f"[DEBUG] Slot 2 in API response: vocab={bool(slot_2_data.get('vocabulary_cognates'))}, frames={bool(slot_2_data.get('sentence_frames'))}"
            )
            print(f"[DEBUG] Slot 2 keys: {list(slot_2_data.keys())[:30]}")
            # Check all slots to see which ones have vocabulary
            for idx, s in enumerate(monday_slots):
                if isinstance(s, dict):
                    print(
                        f"[DEBUG] Slot {s.get('slot_number')}: vocab={bool(s.get('vocabulary_cognates'))}, frames={bool(s.get('sentence_frames'))}"
                    )

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

        # Double-check: Verify vocabulary_cognates is still in the response
        response_monday_data = response.lesson_json.get("days", {}).get("monday", {})
        response_monday_slots = response_monday_data.get("slots", [])
        response_slot_2 = next(
            (
                s
                for s in response_monday_slots
                if isinstance(s, dict) and s.get("slot_number") == 2
            ),
            None,
        )
        if response_slot_2:
            print(
                f"[DEBUG] After LessonPlanDetailResponse creation - Slot 2 vocab: {bool(response_slot_2.get('vocabulary_cognates'))}, frames: {bool(response_slot_2.get('sentence_frames'))}"
            )
            if not response_slot_2.get("vocabulary_cognates"):
                print(
                    "[DEBUG] WARNING: vocabulary_cognates missing after response creation!"
                )
                print(f"[DEBUG] Slot 2 keys: {list(response_slot_2.keys())[:30]}")

        # Serialize to JSON to check if vocabulary_cognates survives serialization
        import json as json_module

        try:
            response_dict = response.model_dump()
            response_json_str = json_module.dumps(response_dict, default=str)
            # Check if vocabulary_cognates is in the serialized JSON
            if "vocabulary_cognates" in response_json_str:
                print("[DEBUG] vocabulary_cognates found in serialized JSON")
            else:
                print(
                    "[DEBUG] WARNING: vocabulary_cognates NOT found in serialized JSON!"
                )
            if "sentence_frames" in response_json_str:
                print("[DEBUG] sentence_frames found in serialized JSON")
            else:
                print("[DEBUG] WARNING: sentence_frames NOT found in serialized JSON!")
        except Exception as e:
            print(f"[DEBUG] Failed to serialize response for check: {e}")

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error("plan_detail_failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500, detail=f"Failed to get plan detail: {str(e)}"
        )


@app.get(
    "/api/lesson-steps/{plan_id}/{day}/{slot}",
    response_model=List[LessonStepResponse],
    tags=["Lesson Steps"],
)
@rate_limit_general
async def get_lesson_steps(
    request: Request,
    plan_id: str,
    day: str,
    slot: int,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """Get lesson steps for a specific lesson.

    Args:
        plan_id: Plan ID
        day: Day of week (monday, tuesday, etc.)
        slot: Slot number
        current_user_id: Current authenticated user ID

    Returns:
        List of LessonStepResponse objects
    """
    logger.info(
        "lesson_steps_requested", extra={"plan_id": plan_id, "day": day, "slot": slot}
    )
    print(f"[DEBUG] get_lesson_steps called: plan_id={plan_id}, day={day}, slot={slot}")

    try:
        # Find the plan across projects and track where we found it
        plan = None
        db_where_plan_found = None

        # Try to get plan using current_user_id's database first
        if current_user_id:
            db = get_db(user_id=current_user_id)
            plan = db.get_weekly_plan(plan_id)
            if plan:
                db_where_plan_found = db

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
                        logger.info(
                            f"Plan {plan_id} found in project1 for lesson steps"
                        )
                        db_where_plan_found = db1
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
                        logger.info(
                            f"Plan {plan_id} found in project2 for lesson steps"
                        )
                        db_where_plan_found = db2
                except Exception as e:
                    logger.debug(f"Plan not found in project2: {e}")

        # Fallback to default database if still not found
        if not plan:
            db = get_db()
            plan = db.get_weekly_plan(plan_id)
            if plan:
                db_where_plan_found = db

        if not plan:
            raise HTTPException(status_code=404, detail=f"Plan not found: {plan_id}")

        verify_user_access(plan.user_id, current_user_id, allow_if_none=True)

        # Use the plan owner's database to get lesson steps
        # This ensures we use the correct Supabase project (project1 or project2)
        db_for_steps = get_db(user_id=plan.user_id)
        logger.info(
            "using_plan_owner_database",
            extra={
                "plan_id": plan_id,
                "plan_user_id": plan.user_id,
                "db_where_plan_found": str(type(db_where_plan_found).__name__)
                if db_where_plan_found
                else None,
            },
        )

        # Get steps from the plan owner's database
        try:
            steps = db_for_steps.get_lesson_steps(
                plan_id, day_of_week=day, slot_number=slot
            )
            logger.info(
                "steps_fetched_from_plan_owner_db",
                extra={"plan_id": plan_id, "count": len(steps)},
            )
        except Exception as e:
            # Import here to avoid circular dependency
            from backend.supabase_database import LessonStepsTableMissingError

            # If table doesn't exist, get_lesson_steps should return empty list
            # But if it still raises, catch it here
            error_msg = str(e)
            error_type = type(e).__name__

            # Handle the specific exception type for missing table
            if isinstance(e, LessonStepsTableMissingError) or (
                "PGRST205" in error_msg
                or "Could not find the table" in error_msg
                or "lesson_steps" in error_msg.lower()
                or error_type == "LessonStepsTableMissingError"
            ):
                logger.warning(
                    "lesson_steps_table_missing",
                    extra={
                        "plan_id": plan_id,
                        "error": error_msg,
                        "error_type": error_type,
                    },
                )
                steps = []
            else:
                # For other errors, log but return empty list instead of raising
                # This prevents 500 errors when steps don't exist or can't be fetched
                logger.warning(
                    "error_fetching_steps_from_plan_owner_db",
                    extra={
                        "plan_id": plan_id,
                        "error": str(e),
                        "error_type": error_type,
                    },
                )
                steps = []

        # If no steps found in plan owner's database, try the database where we found the plan
        # This handles cases where steps might have been created in a different database
        if not steps and db_where_plan_found and db_where_plan_found != db_for_steps:
            logger.info(
                "no_steps_in_plan_owner_db_trying_fallback",
                extra={
                    "plan_id": plan_id,
                    "db_where_plan_found_type": str(type(db_where_plan_found).__name__),
                },
            )
            try:
                steps = db_where_plan_found.get_lesson_steps(
                    plan_id, day_of_week=day, slot_number=slot
                )
                if steps:
                    logger.info(
                        "steps_found_in_fallback_db",
                        extra={"plan_id": plan_id, "count": len(steps)},
                    )
                else:
                    logger.info(
                        "no_steps_in_fallback_db",
                        extra={"plan_id": plan_id},
                    )
            except Exception as e:
                # Silently fail - we already tried the plan owner's database
                # Don't raise, just log and continue with empty steps
                logger.debug(
                    "error_checking_fallback_db",
                    extra={
                        "plan_id": plan_id,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )
                # Ensure steps is set to empty list if exception occurred
                if "steps" not in locals() or steps is None:
                    steps = []

        # If still no steps, try the default database as a last resort
        # This handles cases where steps might be in the default SQLite or default Supabase
        if not steps:
            try:
                default_db = get_db()
                if default_db != db_for_steps and (
                    not db_where_plan_found or default_db != db_where_plan_found
                ):
                    logger.info(
                        "trying_default_database_as_last_resort",
                        extra={"plan_id": plan_id},
                    )
                    steps = default_db.get_lesson_steps(
                        plan_id, day_of_week=day, slot_number=slot
                    )
                    if steps:
                        logger.info(
                            "steps_found_in_default_db",
                            extra={"plan_id": plan_id, "count": len(steps)},
                        )
            except Exception as e:
                # Silently fail - this is a last resort attempt
                logger.debug(
                    "error_checking_default_db",
                    extra={
                        "plan_id": plan_id,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )
                # Ensure steps is set to empty list if exception occurred
                if "steps" not in locals() or steps is None:
                    steps = []

        # If no steps found and we have lesson_json, log a message
        # The frontend can handle empty steps or call generate endpoint
        if not steps and plan.lesson_json:
            logger.info(
                f"No lesson steps found for plan {plan_id}, day {day}, slot {slot}. "
                "Steps may need to be generated via /api/lesson-steps/generate endpoint."
            )

        # Convert LessonStep objects to LessonStepResponse
        # FastAPI should handle this automatically with from_attributes=True,
        # but we'll do it explicitly to ensure proper serialization
        # Use model_validate with mode='python' to ensure all fields are included
        step_responses = []
        for step in steps:
            try:
                # Handle potential serialization issues with vocabulary_cognates
                # If it's a string (JSON), we might need to parse it if the model expects a list
                vocab = getattr(step, "vocabulary_cognates", None)
                if isinstance(vocab, str):
                    try:
                        import json

                        vocab = json.loads(vocab)
                    except:
                        vocab = []

                step_responses.append(
                    LessonStepResponse.model_validate(
                        {
                            **step.__dict__,
                            "vocabulary_cognates": vocab,
                            "sentence_frames": getattr(step, "sentence_frames", None),
                        }
                    )
                )
            except Exception as e:
                logger.warning(
                    "step_validation_failed",
                    extra={
                        "plan_id": plan_id,
                        "step_id": getattr(step, "id", "unknown"),
                        "error": str(e),
                    },
                )
                # Continue processing other steps
                continue
        logger.info(
            "returning_lesson_steps",
            extra={
                "plan_id": plan_id,
                "count": len(step_responses),
                "is_list": isinstance(step_responses, list),
                "first_step_id": step_responses[0].id if step_responses else None,
            },
        )

        # Safety check: ensure we're returning a list, not plan data
        if not isinstance(step_responses, list):
            logger.error(
                "invalid_return_type",
                extra={
                    "plan_id": plan_id,
                    "return_type": str(type(step_responses)),
                    "return_value": str(step_responses)[:200],
                },
            )
            raise HTTPException(
                status_code=500,
                detail="Internal error: Invalid return type from get_lesson_steps",
            )

        return step_responses
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        import traceback

        traceback.print_exc()
        logger.error(
            "get_lesson_steps_failed_unhandled",
            extra={
                "plan_id": plan_id,
                "error": str(e),
                "traceback": traceback.format_exc(),
            },
        )
        # Return empty list on failure instead of 500
        return []


@app.post(
    "/api/lesson-steps/generate",
    response_model=List[LessonStepResponse],
    tags=["Lesson Steps"],
)
@rate_limit_auth
async def generate_lesson_steps(
    request: Request,
    plan_id: str,
    day: str,
    slot: int,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """Generate lesson steps from lesson plan phase_plan.

    Args:
        plan_id: Plan ID
        day: Day of week (monday, tuesday, etc.)
        slot: Slot number
        current_user_id: Current authenticated user ID

    Returns:
        List of generated LessonStepResponse objects
    """
    logger.info(
        "lesson_steps_generate_requested",
        extra={"plan_id": plan_id, "day": day, "slot": slot},
    )
    print(
        f"[DEBUG] generate_lesson_steps called: plan_id={plan_id}, day={day}, slot={slot}"
    )

    try:
        # Find the plan across projects (we only need to locate it)
        plan = None

        # Try to get plan using current_user_id's database first
        if current_user_id:
            db = get_db(user_id=current_user_id)
            plan = db.get_weekly_plan(plan_id)

        # [REGENERATION FIX] Delete existing steps for this specific plan/day/slot
        # to prevent stale data or duplicates when the user triggers regeneration.
        try:
            logger.info(
                "clearing_existing_steps_before_regeneration",
                extra={"plan_id": plan_id, "day": day, "slot": slot},
            )
            # Find the database again to ensure we have the right one for deletion
            db_to_clear = (
                get_db(user_id=current_user_id) if current_user_id else get_db()
            )
            db_to_clear.delete_lesson_steps(
                plan_id, day_of_week=day.lower(), slot_number=slot
            )
        except Exception as e:
            logger.warning(
                "failed_to_clear_steps_before_regeneration", extra={"error": str(e)}
            )

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
                        logger.info(
                            f"Plan {plan_id} found in project1 for step generation"
                        )
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
                        logger.info(
                            f"Plan {plan_id} found in project2 for step generation"
                        )
                except Exception as e:
                    logger.debug(f"Plan not found in project2: {e}")

        # Fallback to default database if still not found
        if not plan:
            db = get_db()
            plan = db.get_weekly_plan(plan_id)

        if not plan:
            raise HTTPException(status_code=404, detail=f"Plan not found: {plan_id}")

        verify_user_access(plan.user_id, current_user_id, allow_if_none=True)

        # Use the plan owner's database for all operations
        # This ensures we use the correct Supabase project (project1 or project2)
        db_for_plan = get_db(user_id=plan.user_id)
        logger.info(
            "using_plan_owner_database_for_generation",
            extra={
                "plan_id": plan_id,
                "plan_user_id": plan.user_id,
                "db_type": str(type(db_for_plan).__name__),
            },
        )

        # Get lesson JSON
        lesson_json = plan.lesson_json
        if isinstance(lesson_json, str):
            try:
                lesson_json = json.loads(lesson_json)
            except json.JSONDecodeError:
                logger.error(
                    "lesson_json_parse_failed",
                    extra={"plan_id": plan_id, "error": "Invalid JSON"},
                )
                lesson_json = {}

        if not lesson_json:
            logger.error(
                "lesson_json_missing",
                extra={
                    "plan_id": plan_id,
                    "has_lesson_json_field": hasattr(plan, "lesson_json"),
                },
            )
            raise HTTPException(status_code=400, detail="Plan has no lesson JSON data")

        logger.info(
            "lesson_json_loaded",
            extra={
                "plan_id": plan_id,
                "has_days": "days" in lesson_json,
                "days_keys": list(lesson_json.get("days", {}).keys())
                if "days" in lesson_json
                else [],
            },
        )

        # Extract day data
        days = lesson_json.get("days", {})
        logger.info(
            "extracting_day_data",
            extra={
                "plan_id": plan_id,
                "day": day,
                "available_days": list(days.keys()),
                "day_lower": day.lower(),
            },
        )
        day_data = days.get(day.lower())
        if not day_data:
            logger.error(
                "day_not_found_in_plan",
                extra={
                    "plan_id": plan_id,
                    "requested_day": day,
                    "available_days": list(days.keys()),
                },
            )
            raise HTTPException(status_code=404, detail=f"Day {day} not found in plan")

        # Locate the correct slot data for this day/slot. Newer weekly JSON
        # stores most instructional fields (tailored_instruction, vocabulary,
        # sentence_frames) under days[day]["slots"][*]. For backwards
        # compatibility, we fall back to day-level fields if slots are absent.

        slot_data = day_data
        slots_for_day = day_data.get("slots") or []

        if isinstance(slots_for_day, list) and slots_for_day:
            # Prefer the slot that matches the requested slot number.
            matching = None
            for s in slots_for_day:
                if not isinstance(s, dict):
                    continue
                s_num = s.get("slot_number", 0)
                print(
                    f"[DEBUG] Checking slot: {s_num} (type: {type(s_num)}) against requested: {slot} (type: {type(slot)})"
                )
                if int(s_num) == int(slot):
                    matching = s
                    print(f"[DEBUG] Found matching slot: {s_num}")
                    break
            if matching:
                slot_data = matching
                print(
                    f"[DEBUG] Using matched slot_data: slot_number={slot_data.get('slot_number')}"
                )
            else:
                # No matching slot found - return 404 error instead of silently using wrong slot
                available_slots = [
                    s.get("slot_number") for s in slots_for_day if isinstance(s, dict)
                ]
                logger.error(
                    "slot_not_found_in_plan",
                    extra={
                        "plan_id": plan_id,
                        "requested_slot": slot,
                        "requested_day": day,
                        "available_slots": available_slots,
                    },
                )
                raise HTTPException(
                    status_code=404,
                    detail=f"Slot {slot} not found in {day}. Available slots: {available_slots}",
                )

            print(
                f"[DEBUG] Final slot_data: slot_number={slot_data.get('slot_number')}, has_vocabulary_cognates={bool(slot_data.get('vocabulary_cognates'))}"
            )

            # [NO SCHOOL FIX] Skip generation if this is a "No School" slot
            unit_lesson = slot_data.get("unit_lesson", "")
            if unit_lesson and "no school" in unit_lesson.lower():
                logger.info(
                    "skipping_step_generation_for_no_school",
                    extra={
                        "plan_id": plan_id,
                        "day": day,
                        "slot": slot,
                        "unit_lesson": unit_lesson,
                    },
                )
                return []

            print(f"[DEBUG] slot_data keys (first 20): {list(slot_data.keys())[:20]}")

            # Check if vocabulary_cognates exists in slot_data
            if slot_data.get("vocabulary_cognates"):
                vocab_list = slot_data.get("vocabulary_cognates")
                print(
                    f"[DEBUG] vocabulary_cognates in slot_data: {len(vocab_list)} items"
                )
                if isinstance(vocab_list, list) and len(vocab_list) > 0:
                    print(f"[DEBUG] vocabulary_cognates sample: {vocab_list[0]}")
            else:
                # Check for any vocabulary-related keys
                vocab_keys = [k for k in slot_data.keys() if "vocab" in str(k).lower()]
                if vocab_keys:
                    print(
                        f"[DEBUG] WARNING: Found vocabulary-related keys but vocabulary_cognates missing: {vocab_keys}"
                    )
                else:
                    # Log as info instead of warning - this is expected for older plans
                    logger.info(
                        "vocabulary_cognates_not_found_in_slot",
                        extra={
                            "plan_id": plan_id,
                            "day": day,
                            "slot": slot,
                            "message": "vocabulary_cognates not found in slot_data. This may mean the plan was generated before vocabulary_cognates was added to the schema. Consider regenerating the plan to include vocabulary data.",
                        },
                    )
                    print(
                        "[DEBUG] INFO: vocabulary_cognates not found in slot_data. "
                        "This may mean the plan was generated before vocabulary_cognates was added to the schema. "
                        "Consider regenerating the plan to include vocabulary data."
                    )

            # Also check day_data as fallback
            if day_data.get("vocabulary_cognates"):
                print(
                    f"[DEBUG] vocabulary_cognates in day_data: {len(day_data.get('vocabulary_cognates'))} items"
                )
                # Use day_data vocabulary_cognates if slot_data doesn't have it
                if not slot_data.get("vocabulary_cognates"):
                    print("[DEBUG] Using vocabulary_cognates from day_data as fallback")
                    slot_data["vocabulary_cognates"] = day_data.get(
                        "vocabulary_cognates"
                    )

        # Extract phase_plan from tailored_instruction (slot-level when present)
        # Check multiple possible locations for phase_plan to handle different data structures
        slot_tailored_instruction = slot_data.get("tailored_instruction", {})
        day_tailored_instruction = day_data.get("tailored_instruction", {})

        # Use slot-level tailored_instruction if available, otherwise fall back to day-level
        # This ensures later code (like ell_support extraction) uses the best available data
        tailored_instruction = (
            slot_tailored_instruction
            if slot_tailored_instruction
            else day_tailored_instruction
        )

        logger.info(
            "tailored_instruction_extracted",
            extra={
                "plan_id": plan_id,
                "day": day,
                "slot": slot,
                "has_tailored_instruction": bool(tailored_instruction),
                "tailored_instruction_keys": list(tailored_instruction.keys())
                if tailored_instruction
                else [],
                "has_day_tailored_instruction": bool(day_tailored_instruction),
                "day_tailored_instruction_keys": list(day_tailored_instruction.keys())
                if day_tailored_instruction
                else [],
            },
        )

        # Try multiple locations for phase_plan:
        # 1. slot_data.tailored_instruction.co_teaching_model.phase_plan (preferred)
        # 2. slot_data.tailored_instruction.phase_plan (direct)
        # 3. day_data.tailored_instruction.co_teaching_model.phase_plan (day-level fallback)
        # 4. day_data.tailored_instruction.phase_plan (day-level direct)

        phase_plan = None
        co_teaching_model = slot_tailored_instruction.get("co_teaching_model", {})

        # Check slot-level: tailored_instruction.co_teaching_model.phase_plan
        if co_teaching_model:
            phase_plan = co_teaching_model.get("phase_plan")
            if phase_plan:
                logger.info(
                    "phase_plan_found_in_slot_co_teaching_model",
                    extra={
                        "plan_id": plan_id,
                        "day": day,
                        "slot": slot,
                        "location": "slot_data.tailored_instruction.co_teaching_model.phase_plan",
                        "phase_plan_count": len(phase_plan)
                        if isinstance(phase_plan, list)
                        else 0,
                    },
                )

        # Check slot-level: tailored_instruction.phase_plan (direct)
        if not phase_plan:
            phase_plan = slot_tailored_instruction.get("phase_plan")
            if phase_plan:
                logger.info(
                    "phase_plan_found_in_slot_direct",
                    extra={
                        "plan_id": plan_id,
                        "day": day,
                        "slot": slot,
                        "location": "slot_data.tailored_instruction.phase_plan",
                        "phase_plan_count": len(phase_plan)
                        if isinstance(phase_plan, list)
                        else 0,
                    },
                )

        # Check day-level: day_data.tailored_instruction.co_teaching_model.phase_plan
        if not phase_plan:
            day_co_teaching_model = day_tailored_instruction.get(
                "co_teaching_model", {}
            )
            if day_co_teaching_model:
                phase_plan = day_co_teaching_model.get("phase_plan")
                if phase_plan:
                    logger.info(
                        "phase_plan_found_in_day_co_teaching_model",
                        extra={
                            "plan_id": plan_id,
                            "day": day,
                            "slot": slot,
                            "location": "day_data.tailored_instruction.co_teaching_model.phase_plan",
                            "phase_plan_count": len(phase_plan)
                            if isinstance(phase_plan, list)
                            else 0,
                        },
                    )

        # Check day-level: day_data.tailored_instruction.phase_plan (direct)
        if not phase_plan:
            phase_plan = day_tailored_instruction.get("phase_plan")
            if phase_plan:
                logger.info(
                    "phase_plan_found_in_day_direct",
                    extra={
                        "plan_id": plan_id,
                        "day": day,
                        "slot": slot,
                        "location": "day_data.tailored_instruction.phase_plan",
                        "phase_plan_count": len(phase_plan)
                        if isinstance(phase_plan, list)
                        else 0,
                    },
                )

        # Normalize to empty list if None
        if phase_plan is None:
            phase_plan = []

        logger.info(
            "co_teaching_model_extracted",
            extra={
                "plan_id": plan_id,
                "has_co_teaching_model": bool(co_teaching_model),
                "co_teaching_model_keys": list(co_teaching_model.keys())
                if co_teaching_model
                else [],
            },
        )

        logger.info(
            "phase_plan_extracted",
            extra={
                "plan_id": plan_id,
                "day": day,
                "slot": slot,
                "phase_plan_count": len(phase_plan) if phase_plan else 0,
                "phase_plan_is_list": isinstance(phase_plan, list),
                "phase_plan_is_none": phase_plan is None,
            },
        )
        logger.info(
            "phase_plan_extracted",
            extra={
                "plan_id": plan_id,
                "day": day,
                "slot": slot,
                "phase_plan_count": len(phase_plan) if phase_plan else 0,
                "phase_plan_is_list": isinstance(phase_plan, list),
            },
        )

        # Delete existing steps for this lesson
        deleted_count = db_for_plan.delete_lesson_steps(
            plan_id, day_of_week=day, slot_number=slot
        )
        logger.info(
            "existing_steps_deleted",
            extra={
                "plan_id": plan_id,
                "day": day,
                "slot": slot,
                "deleted_count": deleted_count,
            },
        )

        # Generate steps from phase_plan or use default steps if phase_plan is missing
        import uuid
        from datetime import datetime

        from backend.schema import LessonStep

        start_time_offset = 0
        generated_steps = []  # Store steps in memory in case table doesn't exist
        print("[DEBUG] Initialized generated_steps list (empty)")

        if not phase_plan:
            # Generate default lesson steps when phase_plan is missing
            logger.warning(
                "phase_plan_missing_using_defaults",
                extra={
                    "plan_id": plan_id,
                    "day": day,
                    "slot": slot,
                },
            )
            print("[DEBUG] No phase_plan found, generating default lesson steps")

            # Create default 45-minute lesson structure: Warmup (5), Input (15), Practice (20), Closure (5)
            default_phases = [
                {
                    "phase_name": "Warmup",
                    "minutes": 5,
                    "content_type": "instruction",
                    "details": "Engage students with a brief activity to activate prior knowledge and prepare them for the lesson.",
                },
                {
                    "phase_name": "Input",
                    "minutes": 15,
                    "content_type": "instruction",
                    "details": "Present new content, concepts, or skills to students. This is the main teaching phase of the lesson.",
                },
                {
                    "phase_name": "Practice",
                    "minutes": 20,
                    "content_type": "instruction",
                    "details": "Students practice the new skills or concepts with teacher support and then independently.",
                },
                {
                    "phase_name": "Closure",
                    "minutes": 5,
                    "content_type": "assessment",
                    "details": "Wrap up the lesson by reviewing key concepts, checking for understanding, and preparing for the next lesson.",
                },
            ]
            phase_plan = default_phases
            print(f"[DEBUG] Using default phase_plan with {len(phase_plan)} phases")
        else:
            print(
                f"[DEBUG] Starting step generation, phase_plan has {len(phase_plan)} phases"
            )

        for idx, phase in enumerate(phase_plan, start=1):
            print(
                f"[DEBUG] Processing phase {idx}/{len(phase_plan)}: {phase.get('phase_name', 'unnamed')}"
            )
            step_id = str(uuid.uuid4())

            # Determine content type based on phase
            content_type = phase.get("content_type", "instruction")
            step_name = phase.get("phase_name", f"Step {idx}")
            # Schema uses "minutes", but allow both for compatibility
            # Ensure duration is never 0 - default to 5 minutes if missing or 0
            duration = phase.get("minutes", phase.get("duration_minutes", 5))
            if duration == 0 or duration is None:
                duration = 5
                logger.warning(
                    "lesson_step_zero_duration_fixed",
                    extra={
                        "plan_id": plan_id,
                        "day": day,
                        "slot": slot,
                        "step_name": step_name,
                    },
                )

            # Extract content from phase details
            # Schema has: bilingual_teacher_role, primary_teacher_role, details
            bilingual_role = phase.get("bilingual_teacher_role", "")
            primary_role = phase.get("primary_teacher_role", "")
            details = phase.get("details", "")

            # Combine roles and details for display content
            display_content_parts = []
            if bilingual_role:
                display_content_parts.append(f"Bilingual Teacher: {bilingual_role}")
            if primary_role:
                display_content_parts.append(f"Primary Teacher: {primary_role}")
            if details:
                display_content_parts.append(details)

            display_content = (
                "\n\n".join(display_content_parts) if display_content_parts else ""
            )

            # Allow sentence_frames and materials from phase if present, otherwise empty
            sentence_frames = phase.get("sentence_frames", [])
            materials = phase.get("materials", [])

            step_data = {
                "id": step_id,
                "lesson_plan_id": plan_id,
                "day_of_week": day.lower(),
                "slot_number": slot,
                "step_number": idx,
                "step_name": step_name,
                "duration_minutes": duration,
                "start_time_offset": start_time_offset,
                "content_type": content_type,
                "display_content": display_content,
                "hidden_content": [],
                "sentence_frames": sentence_frames,
                "materials_needed": materials,
            }

            try:
                created_id = db_for_plan.create_lesson_step(step_data)
                logger.debug(
                    "step_created_in_database",
                    extra={
                        "plan_id": plan_id,
                        "step_name": step_name,
                        "step_id": created_id,
                    },
                )
            except Exception as create_error:
                # Check if it's the specific LessonStepsTableMissingError from supabase_database
                error_type = type(create_error).__name__
                error_msg = str(create_error)

                # Check for the specific exception or the error message pattern
                is_table_missing = (
                    error_type == "LessonStepsTableMissingError"
                    or "lesson_steps table does not exist" in error_msg
                    or "PGRST205" in error_msg
                    or "Could not find the table" in error_msg
                    or "lesson_steps" in error_msg.lower()
                )

                if is_table_missing:
                    # Add timestamps for in-memory storage
                    step_data_with_timestamps = {
                        **step_data,
                        "created_at": datetime.utcnow(),
                        "updated_at": None,
                    }
                    # Create a LessonStep object from step_data for in-memory storage
                    generated_steps.append(LessonStep(**step_data_with_timestamps))
                    logger.info(
                        "step_stored_in_memory",
                        extra={
                            "plan_id": plan_id,
                            "step_name": step_name,
                            "reason": "table missing (exception caught)",
                            "generated_steps_count": len(generated_steps),
                        },
                    )
                    print(
                        f"[DEBUG] Step stored in memory (exception): {step_name}, total steps: {len(generated_steps)}"
                    )
                else:
                    # Re-raise other errors
                    logger.error(
                        "step_creation_failed",
                        extra={
                            "plan_id": plan_id,
                            "step_name": step_name,
                            "error": str(create_error),
                        },
                    )
                    raise
            start_time_offset += duration

        # ============================================================================
        # VOCABULARY/COGNATES AND SENTENCE FRAMES STEP GENERATION
        # ============================================================================
        #
        # CRITICAL: vocabulary_cognates and sentence_frames should be present in
        # lesson_json under days[day]["slots"][slot_number]. If these are missing
        # or empty arrays, vocabulary/frames steps will NOT be created.
        #
        # Expected structure in lesson_json:
        #   days[day]["slots"][slot_number]["vocabulary_cognates"] = [
        #     {"english": "...", "portuguese": "...", "is_cognate": bool, "relevance_note": "..."}
        #   ]
        #   days[day]["slots"][slot_number]["sentence_frames"] = [
        #     {"english": "...", "portuguese": "...", "proficiency_level": "...", ...}
        #   ]
        #
        # If vocabulary/frames are missing, check:
        #   1. The source JSON file during plan creation/import
        #   2. Whether the plan's lesson_json was properly populated
        #   3. Use update_plan_supabase.py script to fix missing data
        #
        # Fallback: We check both slot-level and day-level data for backwards
        # compatibility with legacy plans that stored vocabulary/frames at day level.
        # ============================================================================

        # Get vocabulary and sentence frames from slot-level (preferred) or day-level (fallback)
        vocabulary_cognates = (
            slot_data.get("vocabulary_cognates")
            or day_data.get("vocabulary_cognates")
            or []
        )
        day_sentence_frames = (
            slot_data.get("sentence_frames") or day_data.get("sentence_frames") or []
        )

        # Validate: Warn if vocabulary/frames are missing when they should be present
        # This helps catch cases where lesson_json was not properly populated
        if not vocabulary_cognates and not day_sentence_frames:
            logger.warning(
                "vocabulary_frames_missing",
                extra={
                    "plan_id": plan_id,
                    "day": day,
                    "slot": slot,
                    "warning": (
                        "No vocabulary_cognates or sentence_frames found in lesson_json. "
                        "Vocabulary/frames steps will not be created. "
                        "If this plan should have vocabulary/frames, check the source JSON "
                        "or use update_plan_supabase.py to fix the plan's lesson_json."
                    ),
                },
            )

        logger.info(
            f"DEBUG: Generating steps for slot {slot}. Vocab count: {len(vocabulary_cognates)}. Frames count: {len(day_sentence_frames)}"
        )
        print(
            f"[DEBUG] Vocabulary check: vocabulary_cognates exists={bool(vocabulary_cognates)}, type={type(vocabulary_cognates)}, length={len(vocabulary_cognates) if isinstance(vocabulary_cognates, list) else 'N/A'}"
        )
        logger.info(
            "vocabulary_cognates_check",
            extra={
                "plan_id": plan_id,
                "has_vocabulary_cognates": bool(vocabulary_cognates),
                "is_list": isinstance(vocabulary_cognates, list),
                "length": len(vocabulary_cognates)
                if isinstance(vocabulary_cognates, list)
                else 0,
            },
        )

        # Create Vocabulary / Cognate Awareness step if vocabulary_cognates exists
        # NOTE: This step is ONLY created if vocabulary_cognates is a non-empty list.
        # If vocabulary_cognates is None or [], no vocabulary step will be created.
        if vocabulary_cognates:
            # Build simple bullet-style lines from the six pairs.
            lines: list[str] = []
            for pair in vocabulary_cognates:
                if not isinstance(pair, dict):
                    continue
                english = str(pair.get("english", "")).strip()
                portuguese = str(pair.get("portuguese", "")).strip()
                if not english or not portuguese:
                    continue
                # Use a simple, plain-text arrow separator for the lesson browser
                lines.append(f"- {english} -> {portuguese}")

            if lines:
                vocab_step_id = str(uuid.uuid4())
                vocab_step_number = len(phase_plan) + 1

                # Extract implementation strategy for Cognate Awareness if available
                ell_support = tailored_instruction.get("ell_support") or []
                vocab_strategy_text = ""
                if isinstance(ell_support, list):
                    for s in ell_support:
                        if isinstance(s, dict):
                            strategy_id = s.get("strategy_id", "").lower()
                            strategy_name = str(s.get("strategy_name", "")).lower()
                            # Match by ID or name
                            if (
                                strategy_id == "cognate_awareness"
                                or "cognate" in strategy_name
                            ):
                                vocab_strategy_text = s.get(
                                    "implementation", ""
                                ) or s.get("implementation_steps", "")
                                if vocab_strategy_text:
                                    # If implementation_steps is a list, join it
                                    if isinstance(vocab_strategy_text, list):
                                        vocab_strategy_text = "\n".join(
                                            vocab_strategy_text
                                        )
                                    break

                display_content = "\n".join(lines)
                if vocab_strategy_text:
                    display_content = f"{vocab_strategy_text}\n\n{display_content}"

                vocab_step = {
                    "id": vocab_step_id,
                    "lesson_plan_id": plan_id,
                    "day_of_week": day.lower(),
                    "slot_number": slot,
                    "step_number": vocab_step_number,
                    "step_name": "Vocabulary / Cognate Awareness",
                    "duration_minutes": 5,
                    "start_time_offset": start_time_offset,
                    "content_type": "instruction",
                    "display_content": display_content,
                    "hidden_content": [],
                    "sentence_frames": [],
                    "materials_needed": [],
                    "vocabulary_cognates": json.dumps(vocabulary_cognates)
                    if settings.USE_SUPABASE
                    else vocabulary_cognates,  # Include structured data for frontend
                }

            # DEBUG: Log vocabulary_cognates before saving
            print(
                f"[DEBUG] vocab_step vocabulary_cognates: type={type(vocabulary_cognates)}, value={vocabulary_cognates}, length={len(vocabulary_cognates) if isinstance(vocabulary_cognates, list) else 'N/A'}"
            )
            logger.info(
                "vocab_step_before_save",
                extra={
                    "plan_id": plan_id,
                    "vocab_type": str(type(vocabulary_cognates)),
                    "vocab_is_list": isinstance(vocabulary_cognates, list),
                    "vocab_length": len(vocabulary_cognates)
                    if isinstance(vocabulary_cognates, list)
                    else 0,
                    "vocab_sample": vocabulary_cognates[0]
                    if isinstance(vocabulary_cognates, list)
                    and len(vocabulary_cognates) > 0
                    else None,
                },
            )

            try:
                created_id = db_for_plan.create_lesson_step(vocab_step)
                logger.debug(
                    "Vocab step created in database", extra={"step_id": created_id}
                )
            except Exception as create_error:
                error_type = type(create_error).__name__
                error_msg = str(create_error)
                is_table_missing = (
                    error_type == "LessonStepsTableMissingError"
                    or "lesson_steps table does not exist" in error_msg
                    or "PGRST205" in error_msg
                    or "Could not find the table" in error_msg
                    or "lesson_steps" in error_msg.lower()
                )
                if is_table_missing:
                    vocab_step_with_timestamps = {
                        **vocab_step,
                        "created_at": datetime.utcnow(),
                        "updated_at": None,
                    }
                    generated_steps.append(LessonStep(**vocab_step_with_timestamps))
                    logger.debug("Stored vocab step in memory (table missing)")
                    print(
                        f"[DEBUG] Vocab step stored in memory, total steps: {len(generated_steps)}"
                    )
                else:
                    raise
            start_time_offset += 5

        # Append a sentence-frames step sourced from slot-level
        # sentence_frames when available, falling back to any legacy
        # day-level sentence_frames.
        # NOTE: This step is ONLY created if sentence_frames is a non-empty list.
        # If sentence_frames is None or [], no sentence frames step will be created.
        if day_sentence_frames:
            import uuid

            frames_step_id = str(uuid.uuid4())
            # Place it after existing steps (phase_plan + optional vocab)
            existing_steps = db_for_plan.get_lesson_steps(
                plan_id, day_of_week=day, slot_number=slot
            )
            next_step_number = (
                (existing_steps[-1].step_number + 1)
                if existing_steps
                else (len(phase_plan) + 1)
            )

            # Extract implementation strategy for Sentence Frames if available
            ell_support = tailored_instruction.get("ell_support") or []
            frames_strategy_text = ""
            if isinstance(ell_support, list):
                for s in ell_support:
                    if isinstance(s, dict):
                        strategy_id = s.get("strategy_id", "").lower()
                        strategy_name = str(s.get("strategy_name", "")).lower()
                        # Match by ID or name
                        if (
                            strategy_id == "sentence_frames"
                            or "sentence frames" in strategy_name
                            or "sentence frame" in strategy_name
                        ):
                            frames_strategy_text = s.get("implementation", "") or s.get(
                                "implementation_steps", ""
                            )
                            if frames_strategy_text:
                                # If implementation_steps is a list, join it
                                if isinstance(frames_strategy_text, list):
                                    frames_strategy_text = "\n".join(
                                        frames_strategy_text
                                    )
                                break

            # Create display content for sentence frames
            # Combine strategy text with the actual frames for robust display
            frames_display_parts = []
            if frames_strategy_text:
                frames_display_parts.append(frames_strategy_text)

            if day_sentence_frames:
                frames_display_parts.append("\nReference Frames:")
                for frame in day_sentence_frames:
                    if isinstance(frame, dict):
                        english = frame.get("english", "")
                        if english:
                            frames_display_parts.append(f"- {english}")

            frames_display_content = (
                "\n\n".join(frames_display_parts)
                if frames_display_parts
                else frames_strategy_text
            )

            frames_step = {
                "id": frames_step_id,
                "lesson_plan_id": plan_id,
                "day_of_week": day.lower(),
                "slot_number": slot,
                "step_number": next_step_number,
                "step_name": "Sentence Frames / Stems / Questions",
                "duration_minutes": 5,
                "start_time_offset": start_time_offset,
                "content_type": "sentence_frames",
                "display_content": frames_display_content,
                "hidden_content": [],
                "sentence_frames": day_sentence_frames,
                "materials_needed": [],
            }

            try:
                created_id = db_for_plan.create_lesson_step(frames_step)
                logger.debug(
                    "Frames step created in database", extra={"step_id": created_id}
                )
            except Exception as create_error:
                error_type = type(create_error).__name__
                error_msg = str(create_error)
                is_table_missing = (
                    error_type == "LessonStepsTableMissingError"
                    or "lesson_steps table does not exist" in error_msg
                    or "PGRST205" in error_msg
                    or "Could not find the table" in error_msg
                    or "lesson_steps" in error_msg.lower()
                )
                if is_table_missing:
                    frames_step_with_timestamps = {
                        **frames_step,
                        "created_at": datetime.utcnow(),
                        "updated_at": None,
                    }
                    generated_steps.append(LessonStep(**frames_step_with_timestamps))
                    logger.debug("Stored frames step in memory (table missing)")
                    print(
                        f"[DEBUG] Frames step stored in memory, total steps: {len(generated_steps)}"
                    )
                else:
                    raise
            start_time_offset += 5

        # If we have in-memory steps (table doesn't exist), return those
        # Otherwise, fetch from database
        print(
            f"[DEBUG] Checking generated_steps: count={len(generated_steps)}, phase_plan_count={len(phase_plan)}"
        )
        print(
            f"[DEBUG] generated_steps type: {type(generated_steps)}, is_list: {isinstance(generated_steps, list)}"
        )
        if generated_steps:
            print(
                f"[DEBUG] generated_steps contents: {[s.step_name if hasattr(s, 'step_name') else str(s)[:50] for s in generated_steps]}"
            )

        logger.info(
            "checking_generated_steps",
            extra={
                "plan_id": plan_id,
                "in_memory_count": len(generated_steps),
                "phase_plan_count": len(phase_plan),
            },
        )

        if generated_steps:
            print(f"[DEBUG] Returning {len(generated_steps)} in-memory steps")
            logger.info(
                "lesson_steps_generated_in_memory",
                extra={
                    "count": len(generated_steps),
                    "details": "Table missing, returning in-memory steps",
                },
            )
            # Convert LessonStep objects to LessonStepResponse
            from datetime import datetime

            steps = [
                LessonStepResponse(
                    id=step.id,
                    lesson_plan_id=step.lesson_plan_id,
                    day_of_week=step.day_of_week,
                    slot_number=step.slot_number,
                    step_number=step.step_number,
                    step_name=step.step_name,
                    duration_minutes=step.duration_minutes,
                    start_time_offset=step.start_time_offset,
                    content_type=step.content_type,
                    display_content=step.display_content,
                    hidden_content=step.hidden_content or [],
                    sentence_frames=step.sentence_frames or [],
                    materials_needed=step.materials_needed or [],
                    vocabulary_cognates=step.vocabulary_cognates or [],
                    created_at=datetime.utcnow(),
                    updated_at=None,
                )
                for step in generated_steps
            ]
            logger.info("returning_in_memory_steps", extra={"count": len(steps)})
            return steps

        # Fetch from database
        steps = db_for_plan.get_lesson_steps(plan_id, day_of_week=day, slot_number=slot)
        logger.info(
            "lesson_steps_fetched_from_database",
            extra={
                "plan_id": plan_id,
                "count": len(steps),
                "steps_type": str(type(steps)) if steps else "empty",
            },
        )

        # Convert LessonStep objects to LessonStepResponse
        step_responses = [LessonStepResponse.model_validate(step) for step in steps]
        logger.info(
            "returning_generated_steps",
            extra={
                "plan_id": plan_id,
                "count": len(step_responses),
                "is_list": isinstance(step_responses, list),
                "first_step_id": step_responses[0].id if step_responses else None,
            },
        )

        # Safety check: ensure we're returning a list
        if not isinstance(step_responses, list):
            logger.error(
                "invalid_return_type_generate",
                extra={
                    "plan_id": plan_id,
                    "return_type": str(type(step_responses)),
                },
            )
            raise HTTPException(
                status_code=500,
                detail="Internal error: Invalid return type from generate_lesson_steps",
            )

        return step_responses

    except HTTPException:
        raise
    except Exception as e:
        logger.error("lesson_steps_generate_failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500, detail=f"Failed to generate steps: {str(e)}"
        )


# Lesson Mode Session endpoints
@app.post(
    "/api/lesson-mode/session",
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
            import uuid

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
            import uuid

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


@app.get(
    "/api/lesson-mode/session/active",
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


@app.get(
    "/api/lesson-mode/session/{session_id}",
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
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error("lesson_mode_session_get_failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")


@app.put(
    "/api/lesson-mode/session/{session_id}",
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


@app.post(
    "/api/lesson-mode/session/{session_id}/end",
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


@app.get(
    "/api/users/{user_id}/plans",
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


@app.get(
    "/api/plans/status/{user_id}/{week_of}",
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

        # Get existing plans for this week
        plans = db.get_user_plans(user_id, limit=20)
        plan = next((p for p in plans if p.week_of == week_of), None)

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


@app.post(
    "/api/process-week", response_model=BatchProcessResponse, tags=["Batch Processing"]
)
@rate_limit_batch
async def process_week(
    request: Request,
    batch_request: BatchProcessRequest,
    background_tasks: BackgroundTasks,
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """
    Process all class slots for a user's week.

    Args:
        batch_request: BatchProcessRequest with user_id and week_of
        background_tasks: FastAPI background tasks
        current_user_id: Current authenticated user ID (from X-Current-User-Id header)

    Returns:
        BatchProcessResponse with plan_id for progress tracking
    """
    logger.info(
        "batch_process_requested",
        extra={"user_id": batch_request.user_id, "week_of": batch_request.week_of},
    )

    try:
        # Verify user access
        verify_user_access(batch_request.user_id, current_user_id, allow_if_none=True)
        # Get LLM service
        try:
            llm_service = get_llm_service(provider=batch_request.provider)
            logger.info(
                "llm_service_initialized",
                extra={
                    "provider": batch_request.provider,
                    "service_type": "real",
                    "message": "Using real LLM service (OpenAI/Anthropic API)",
                },
            )
        except ValueError as e:
            # API key missing or invalid
            error_msg = str(e)
            logger.warning(
                "llm_service_failed_api_key",
                extra={
                    "provider": batch_request.provider,
                    "error": error_msg,
                    "reason": "API key missing or invalid",
                    "fallback": "MockLLMService",
                },
            )
            logger.warning(f"⚠️  LLM API Key Issue: {error_msg}")
            logger.warning(f"   Provider: {batch_request.provider}")
            logger.warning("   Falling back to MockLLMService (mock data)")
            logger.warning(
                f"   To use real LLM: Set {batch_request.provider.upper()}_API_KEY in .env file"
            )
            llm_service = get_mock_llm_service()
        except Exception as e:
            # Other initialization errors
            error_msg = str(e)
            error_type = type(e).__name__
            logger.error(
                "llm_service_failed_initialization",
                extra={
                    "provider": batch_request.provider,
                    "error_type": error_type,
                    "error": error_msg,
                    "reason": "LLM service initialization failed",
                    "fallback": "MockLLMService",
                },
                exc_info=True,
            )
            logger.error(
                f"❌ Failed to initialize LLM service: {error_type}: {error_msg}"
            )
            logger.error(f"   Provider: {batch_request.provider}")
            logger.error("   Falling back to MockLLMService (mock data)")
            logger.error("   Check your API key configuration and network connectivity")
            llm_service = get_mock_llm_service()

        # Create processor
        processor = BatchProcessor(llm_service)

        # Get database and create initial plan record
        db = get_db(user_id=batch_request.user_id)
        slots_raw = db.get_user_slots(batch_request.user_id)

        if not slots_raw:
            raise HTTPException(status_code=400, detail="No slots configured for user")

        # Convert ClassSlot objects to dictionaries for filtering
        slots = []
        for slot_obj in slots_raw:
            if hasattr(slot_obj, "model_dump"):
                slots.append(slot_obj.model_dump())
            elif hasattr(slot_obj, "dict"):
                slots.append(slot_obj.dict())
            else:
                slots.append(dict(slot_obj))

        # Filter slots if specific slot_ids provided
        if batch_request.slot_ids:
            slots = [slot for slot in slots if slot["id"] in batch_request.slot_ids]
            if not slots:
                raise HTTPException(
                    status_code=400,
                    detail="No matching slots found for provided slot_ids",
                )

        # If partial, check if we already have a plan for this week to reuse its ID
        plan_id = None
        if batch_request.partial or batch_request.missing_only:
            existing_plans = db.get_user_plans(batch_request.user_id, limit=10)
            existing_plan = next(
                (p for p in existing_plans if p.week_of == batch_request.week_of), None
            )
            if existing_plan:
                plan_id = existing_plan.id
                logger.info(
                    "reusing_existing_plan_id",
                    extra={"plan_id": plan_id, "week_of": batch_request.week_of},
                )

        if not plan_id:
            # Create plan record immediately
            is_consolidated = len(slots) > 1
            plan_id = db.create_weekly_plan(
                batch_request.user_id,
                batch_request.week_of,
                output_file="",
                week_folder_path="",
                consolidated=is_consolidated,
                total_slots=len(slots),
            )

        db.update_weekly_plan(plan_id, status="processing")

        # Initialize progress tracker with this plan_id
        from backend.progress import progress_tracker

        progress_tracker.tasks[plan_id] = {
            "progress": 0,
            "stage": "initialized",
            "message": "Processing started",
            "updates": [],
        }

        # Process in background
        async def process_in_background():
            try:
                logger.info("background_process_started", extra={"plan_id": plan_id})
                result = await processor.process_user_week(
                    batch_request.user_id,
                    batch_request.week_of,
                    batch_request.provider,
                    slot_ids=batch_request.slot_ids,
                    plan_id=plan_id,
                    partial=batch_request.partial,
                    missing_only=batch_request.missing_only,
                    force_slots=batch_request.force_slots or [],
                )

                # Note: BatchProcessor.process_user_week already updates the database status
                # to "completed" or "failed", so we don't need to update it here
                if result["success"]:
                    logger.info(
                        "batch_process_success",
                        extra={
                            "plan_id": result["plan_id"],
                            "processed_slots": result["processed_slots"],
                        },
                    )
                    # Update progress tracker with final result
                    progress_tracker.update(
                        plan_id,
                        "completed",
                        100,
                        f"Successfully processed {result['processed_slots']} slot(s)",
                        result={
                            "processed_slots": result["processed_slots"],
                            "failed_slots": result["failed_slots"],
                            "output_file": result.get("output_file", ""),
                            "errors": result.get("errors"),
                        },
                    )
                else:
                    # Extract error message(s) from result
                    errors = result.get("errors")
                    if errors is None:
                        # If errors is None, check for error field (singular)
                        error_msg = result.get("error")
                        if error_msg:
                            errors = [error_msg]
                        else:
                            # If no errors collected, create a generic message
                            errors = [
                                "Processing failed: No output file generated and no errors were collected. Check logs for details."
                            ]

                    # Ensure errors is a list
                    if not isinstance(errors, list):
                        errors = [str(errors)] if errors else ["Unknown error"]

                    logger.error(
                        "batch_process_failed",
                        extra={
                            "errors": errors,
                            "success": result.get("success"),
                            "output_file": result.get("output_file"),
                            "processed_slots": result.get("processed_slots", 0),
                        },
                    )
                    # Update progress tracker with error result
                    progress_tracker.update(
                        plan_id,
                        "failed",
                        0,
                        f"Processing failed: {errors}",
                        result={
                            "processed_slots": result.get("processed_slots", 0),
                            "failed_slots": result.get("failed_slots", 0),
                            "errors": errors,
                        },
                    )
            except Exception as e:
                import traceback

                error_details = {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "traceback": traceback.format_exc(),
                    "plan_id": plan_id,
                }
                logger.error("background_process_error", extra=error_details)
                print(
                    f"\n{'=' * 60}\nBACKGROUND PROCESS ERROR:\n{traceback.format_exc()}\n{'=' * 60}\n"
                )
                db.update_weekly_plan(plan_id, status="failed", error_message=str(e))
                # Update progress tracker with error
                progress_tracker.tasks[plan_id] = {
                    "progress": 0,
                    "stage": "failed",
                    "message": f"Error: {str(e)}",
                    "updates": [],
                }

        background_tasks.add_task(process_in_background)

        # Return immediately with plan_id
        return BatchProcessResponse(
            success=True,
            plan_id=plan_id,
            output_file="",
            processed_slots=0,
            failed_slots=0,
            errors=[],
        )

    except Exception as e:
        logger.error("batch_process_error", extra={"error": str(e)})
        raise HTTPException(
            status_code=500, detail=f"Batch processing failed: {str(e)}"
        )


@app.get("/api/analytics/summary", tags=["Analytics"])
async def get_analytics_summary(user_id: Optional[str] = None, days: int = 30):
    """
    Get aggregate analytics summary.

    Args:
        user_id: Optional user filter
        days: Number of days to look back (default: 30)

    Returns:
        Aggregate statistics including total plans, tokens, cost, and breakdowns
    """
    try:
        tracker = get_tracker()
        stats = tracker.get_aggregate_stats(days, user_id)

        logger.info(
            "analytics_summary_requested",
            extra={
                "user_id": user_id,
                "days": days,
                "total_plans": stats.get("total_plans", 0),
            },
        )

        return stats
    except Exception as e:
        logger.error("analytics_summary_error", extra={"error": str(e)})
        raise HTTPException(
            status_code=500, detail=f"Failed to get analytics summary: {str(e)}"
        )


@app.get("/api/analytics/daily", tags=["Analytics"])
async def get_daily_analytics(user_id: Optional[str] = None, days: int = 30):
    """
    Get daily breakdown of activity.

    Args:
        user_id: Optional user filter
        days: Number of days to look back (default: 30)

    Returns:
        List of daily statistics
    """
    try:
        tracker = get_tracker()
        daily_data = tracker.get_daily_breakdown(days, user_id)

        logger.info(
            "analytics_daily_requested",
            extra={"user_id": user_id, "days": days, "days_with_data": len(daily_data)},
        )

        return daily_data
    except Exception as e:
        logger.error("analytics_daily_error", extra={"error": str(e)})
        raise HTTPException(
            status_code=500, detail=f"Failed to get daily analytics: {str(e)}"
        )


@app.get("/api/analytics/sessions", tags=["Analytics"])
async def get_session_analytics(user_id: Optional[str] = None, days: int = 30):
    """
    Get session-by-session breakdown (each plan is a session).

    Args:
        user_id: Optional user filter
        days: Number of days to look back (default: 30)

    Returns:
        List of session statistics, ordered by most recent first
    """
    try:
        tracker = get_tracker()
        sessions = tracker.get_session_breakdown(days, user_id)

        logger.info(
            "analytics_sessions_requested",
            extra={"user_id": user_id, "days": days, "session_count": len(sessions)},
        )

        return sessions
    except Exception as e:
        logger.error("analytics_sessions_error", extra={"error": str(e)})
        raise HTTPException(
            status_code=500, detail=f"Failed to get session analytics: {str(e)}"
        )


@app.get("/api/analytics/export", tags=["Analytics"])
async def export_analytics(user_id: Optional[str] = None, days: int = 30):
    """
    Export analytics to CSV.

    Args:
        user_id: Optional user filter
        days: Number of days to look back (default: 30)

    Returns:
        CSV file with analytics data
    """
    try:
        tracker = get_tracker()
        csv_data = tracker.export_analytics_csv(days, user_id)

        if not csv_data:
            raise HTTPException(
                status_code=404,
                detail="No analytics data found for the specified period",
            )

        logger.info(
            "analytics_export_requested", extra={"user_id": user_id, "days": days}
        )

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analytics_{timestamp}.csv"

        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("analytics_export_error", extra={"error": str(e)})
        raise HTTPException(
            status_code=500, detail=f"Failed to export analytics: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    # Run with uvicorn
    uvicorn.run(
        "backend.api:app", host="127.0.0.1", port=8000, reload=True, log_level="info"
    )

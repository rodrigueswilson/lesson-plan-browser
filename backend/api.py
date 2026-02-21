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
from backend.progress import simulate_render_progress, stream_render_progress
from backend.rate_limiter import (
    rate_limit_auth,
    rate_limit_batch,
    rate_limit_general,
    setup_rate_limiting,
)
from backend.routers.analytics import router as analytics_router
from backend.routers.health import router as health_router
from backend.routers.settings import router as settings_router
from backend.routers.users import router as users_router
from backend.routers.plans import router as plans_router
from backend.routers.process_week import router as process_week_router
from backend.services.objectives_utils import normalize_objectives_in_lesson
from backend.services.sorting_utils import sort_slots
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

# Include routers (health uses full paths; others use prefix="/api")
app.include_router(health_router)
app.include_router(settings_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(plans_router, prefix="/api")
app.include_router(process_week_router, prefix="/api")
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

if __name__ == "__main__":
    import uvicorn

    # Run with uvicorn
    uvicorn.run(
        "backend.api:app", host="127.0.0.1", port=8000, reload=True, log_level="info"
    )

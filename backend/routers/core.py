"""
Core pipeline routes: validate, render, progress, transform, repair, tablet export.
"""
import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse

from backend.authorization import get_current_user_id, verify_user_access
from backend.config import settings
from backend.database import get_db
from backend.errors import RenderError, TemplateNotFoundError, ValidationError
from backend.llm_service import get_llm_service
from backend.models import (
    RenderRequest,
    RenderResponse,
    TabletExportDbCounts,
    TabletExportDbRequest,
    TabletExportDbResponse,
    TransformRequest,
    TransformResponse,
    ValidationRequest,
    ValidationResponse,
)
from backend.models import ValidationError as ValidationErrorModel
from backend.progress import simulate_render_progress, stream_render_progress
from backend.services.objectives_utils import normalize_objectives_in_lesson
from backend.tablet_db_export import TabletDbExportError, export_user_tablet_db
from backend.telemetry import logger
from backend.utils.lesson_times import enrich_lesson_json_with_times
from tools.docx_renderer import DOCXRenderer
from tools.json_repair import repair_json
from tools.validate_schema import load_schema
from tools.validate_schema import validate_json as validate_schema

SCHEMA_PATH = Path("schemas/lesson_output_schema.json")
SCHEMA = load_schema(SCHEMA_PATH)

router = APIRouter()


@router.post(
    "/tablet/export-db", response_model=TabletExportDbResponse, tags=["Tablet"]
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
    output_path = (Path(__file__).resolve().parents[2] / output_path).resolve()

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


@router.post("/validate", response_model=ValidationResponse, tags=["Validation"])
async def validate_json(request: ValidationRequest):
    """
    Validate lesson plan JSON against schema.
    """
    logger.info("validation_requested", extra={"has_data": bool(request.json_data)})

    try:
        is_valid, errors = validate_schema(request.json_data, SCHEMA)

        if is_valid:
            logger.info("validation_success")
            return ValidationResponse(valid=True, errors=None)
        else:
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


@router.post("/render", response_model=RenderResponse, tags=["Rendering"])
async def render_lesson_plan(request: RenderRequest, background_tasks: BackgroundTasks):
    """
    Render lesson plan JSON to DOCX format.
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
        is_valid, errors = validate_schema(request.json_data, SCHEMA)
        if not is_valid:
            logger.warning(
                "render_validation_failed", extra={"error_count": len(errors)}
            )
            raise ValidationError(errors)

        template_path = Path(request.template_path)
        if not template_path.exists():
            logger.error(
                "template_not_found", extra={"template_path": str(template_path)}
            )
            raise TemplateNotFoundError(str(template_path))

        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / request.output_filename

        logger.info("rendering_docx", extra={"output_path": str(output_path)})
        renderer = DOCXRenderer(str(template_path))
        success = renderer.render(request.json_data, str(output_path))

        if not success:
            logger.error("render_failed")
            raise RenderError("Failed to render DOCX file")

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


@router.get("/render/{filename}", tags=["Rendering"])
async def download_rendered_file(filename: str):
    """
    Download a rendered DOCX file.
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


@router.get("/progress", tags=["Progress"])
async def stream_progress():
    """
    Stream rendering progress via Server-Sent Events (SSE).
    """
    logger.info("progress_stream_requested")
    return EventSourceResponse(simulate_render_progress())


@router.get("/progress/{task_id}", tags=["Progress"])
async def stream_task_progress(task_id: str):
    """
    Stream progress for a specific task via SSE.
    """
    logger.info("task_progress_stream_requested", extra={"task_id": task_id})
    return EventSourceResponse(stream_render_progress(task_id))


@router.get("/progress/{task_id}/poll", tags=["Progress"])
async def poll_task_progress(task_id: str):
    """
    Poll progress for a specific task (Tauri-compatible alternative to SSE).
    """
    from backend.progress import progress_tracker

    print(f"DEBUG: Polling progress for task_id: {task_id}")
    print(f"DEBUG: Available task IDs: {list(progress_tracker.tasks.keys())[:5]}")

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


@router.post("/transform", response_model=TransformResponse, tags=["LLM"])
async def transform_lesson(request: TransformRequest):
    """
    Transform primary teacher content to bilingual lesson plan using LLM.
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
                enrich_lesson_json_with_times(
                    lesson_json,
                    getattr(request, "user_id", ""),
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


@router.post("/repair", tags=["Utilities"])
async def repair_json_endpoint(json_string: str):
    """
    Attempt to repair malformed JSON.
    """
    logger.info("json_repair_requested")

    try:
        repaired = repair_json(json_string)
        logger.info("json_repair_success")
        return {"success": True, "repaired_json": repaired}
    except Exception as e:
        logger.error("json_repair_failed", extra={"error": str(e)})
        raise HTTPException(status_code=400, detail=f"Repair failed: {str(e)}")

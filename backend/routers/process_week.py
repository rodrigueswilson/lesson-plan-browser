"""
Batch process-week API endpoint (POST /api/process-week).
"""
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request

from backend.authorization import get_current_user_id, verify_user_access
from backend.database import get_db
from backend.llm_service import get_llm_service
from backend.mock_llm_service import get_mock_llm_service
from backend.models import BatchProcessRequest, BatchProcessResponse
from backend.rate_limiter import rate_limit_batch
from backend.telemetry import logger
from tools.batch_processor import BatchProcessor

router = APIRouter()


@router.post(
    "/process-week", response_model=BatchProcessResponse, tags=["Batch Processing"]
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
    """
    logger.info(
        "batch_process_requested",
        extra={"user_id": batch_request.user_id, "week_of": batch_request.week_of},
    )

    try:
        verify_user_access(batch_request.user_id, current_user_id, allow_if_none=True)
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
            logger.warning(f"LLM API Key Issue: {error_msg}")
            logger.warning(f"   Provider: {batch_request.provider}")
            logger.warning("   Falling back to MockLLMService (mock data)")
            llm_service = get_mock_llm_service()
        except Exception as e:
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
            logger.error(f"Failed to initialize LLM service: {error_type}: {error_msg}")
            logger.error(f"   Provider: {batch_request.provider}")
            logger.error("   Falling back to MockLLMService (mock data)")
            llm_service = get_mock_llm_service()

        processor = BatchProcessor(llm_service)
        db = get_db(user_id=batch_request.user_id)
        slots_raw = db.get_user_slots(batch_request.user_id)

        if not slots_raw:
            raise HTTPException(status_code=400, detail="No slots configured for user")

        slots = []
        for slot_obj in slots_raw:
            if hasattr(slot_obj, "model_dump"):
                slots.append(slot_obj.model_dump())
            elif hasattr(slot_obj, "dict"):
                slots.append(slot_obj.dict())
            else:
                slots.append(dict(slot_obj))

        if batch_request.slot_ids:
            slot_ids_set = {str(x) for x in batch_request.slot_ids}
            slots = [slot for slot in slots if str(slot.get("id")) in slot_ids_set]
            if not slots:
                raise HTTPException(
                    status_code=400,
                    detail="No matching slots found for provided slot_ids",
                )

        plan_id = None
        if batch_request.partial or batch_request.missing_only:
            from backend.utils.date_formatter import normalize_week_of_for_match

            existing_plans = db.get_user_plans(batch_request.user_id, limit=10)
            canonical = normalize_week_of_for_match(batch_request.week_of)
            existing_plan = next(
                (
                    p
                    for p in existing_plans
                    if p.week_of == batch_request.week_of
                    or (canonical and normalize_week_of_for_match(p.week_of or "") == canonical)
                ),
                None,
            )
            if existing_plan:
                plan_id = existing_plan.id
                logger.info(
                    "reusing_existing_plan_id",
                    extra={"plan_id": plan_id, "week_of": batch_request.week_of},
                )

        if not plan_id:
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

        from backend.progress import progress_tracker

        progress_tracker.tasks[plan_id] = {
            "progress": 0,
            "stage": "initialized",
            "message": "Processing started",
            "updates": [],
        }

        week_folder_path = None
        if batch_request.week_folder:
            user = db.get_user(batch_request.user_id)
            if user and getattr(user, "base_path_override", None):
                week_folder_path = str(
                    Path(user.base_path_override) / batch_request.week_folder.strip()
                )
                logger.info(
                    "week_folder_path_from_request",
                    extra={"week_folder": batch_request.week_folder, "path": week_folder_path},
                )

        async def process_in_background():
            try:
                logger.info("background_process_started", extra={"plan_id": plan_id})
                result = await processor.process_user_week(
                    batch_request.user_id,
                    batch_request.week_of,
                    batch_request.provider,
                    week_folder_path=week_folder_path,
                    slot_ids=batch_request.slot_ids,
                    plan_id=plan_id,
                    partial=batch_request.partial,
                    missing_only=batch_request.missing_only,
                    force_slots=batch_request.force_slots or [],
                )

                if result["success"]:
                    logger.info(
                        "batch_process_success",
                        extra={
                            "plan_id": result["plan_id"],
                            "processed_slots": result["processed_slots"],
                        },
                    )
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
                    errors = result.get("errors")
                    if errors is None:
                        error_msg = result.get("error")
                        if error_msg:
                            errors = [error_msg]
                        else:
                            errors = [
                                "Processing failed: No output file generated and no errors were collected. Check logs for details."
                            ]
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
                progress_tracker.tasks[plan_id] = {
                    "progress": 0,
                    "stage": "failed",
                    "message": f"Error: {str(e)}",
                    "updates": [],
                }

        background_tasks.add_task(process_in_background)

        return BatchProcessResponse(
            success=True,
            plan_id=plan_id,
            output_file="",
            processed_slots=0,
            failed_slots=0,
            errors=[],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("batch_process_error", extra={"error": str(e)})
        raise HTTPException(
            status_code=500, detail=f"Batch processing failed: {str(e)}"
        )

"""
Run the full lesson transform loop: build prompt, retry (instructor + legacy), parse, validate, normalize.
"""

import json
from typing import Any, Callable, Dict, List, Optional, Tuple

from backend.config import settings
from backend.llm.post_process import normalize_sentence_frame_punctuation
from backend.llm.sanitize_lesson_json import sanitize_lesson_json_strings
from backend.llm.validation import (
    parse_llm_response,
    parse_validation_errors,
    validate_structure,
)
from backend.performance_tracker import get_tracker
from backend.telemetry import logger


def run_transform_lesson(
    service: Any,
    primary_content: str,
    grade: str,
    subject: str,
    week_of: str,
    teacher_name: Optional[str] = None,
    homeroom: Optional[str] = None,
    plan_id: Optional[str] = None,
    available_days: Optional[List[str]] = None,
    progress_callback: Optional[Callable[[str, int, str], None]] = None,
) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Run the full transform loop using the given service (LLMService or compatible).

    Uses service._build_prompt, service._build_retry_prompt, service._call_llm,
    service._call_instructor_chat_completion; reads/mutates service.max_completion_tokens.
    """
    logger.info(
        "llm_transform_started",
        extra={
            "grade": grade,
            "subject": subject,
            "week_of": week_of,
            "available_days": available_days,
        },
    )

    if progress_callback:
        progress_callback(
            "processing", 10, f"Preparing to transform {subject} lesson plan..."
        )

    tracker = get_tracker()
    original_max_tokens = service.max_completion_tokens

    try:
        if progress_callback:
            progress_callback(
                "processing", 15, "Building prompt for AI transformation..."
            )

        if plan_id:
            with tracker.track_operation(plan_id, "llm_build_prompt"):
                full_prompt = service._build_prompt(
                    primary_content,
                    grade,
                    subject,
                    week_of,
                    teacher_name,
                    homeroom,
                    available_days,
                )
        else:
            full_prompt = service._build_prompt(
                primary_content,
                grade,
                subject,
                week_of,
                teacher_name,
                homeroom,
                available_days,
            )

        if progress_callback:
            progress_callback(
                "processing", 20, "Prompt built. Sending to AI service..."
            )

        max_retries = settings.RATE_LIMIT_RETRY_ATTEMPTS
        retry_count = 0
        lesson_json = None
        validation_error = None
        error_analysis = None
        response_text = ""
        usage: Dict[str, int] = {}

        while retry_count <= max_retries:
            if progress_callback:
                if retry_count > 0:
                    progress_callback(
                        "processing",
                        25,
                        f"Retrying AI transformation (attempt {retry_count + 1})...",
                    )
                else:
                    progress_callback(
                        "processing",
                        25,
                        "Calling AI service to transform lesson plan...",
                    )

            if service.provider == "openai" and service.instructor_client:
                try:
                    if plan_id:
                        with tracker.track_operation(
                            plan_id, "llm_api_call_instructor"
                        ) as op:
                            lesson_json, usage = (
                                service._call_instructor_chat_completion(
                                    full_prompt, max_retries=max_retries
                                )
                            )
                            op["llm_model"] = service.model
                            op["llm_provider"] = "openai-instructor"
                    else:
                        lesson_json, usage = (
                            service._call_instructor_chat_completion(
                                full_prompt, max_retries=max_retries
                            )
                        )

                    is_valid = True
                    validation_error = None
                    response_text = json.dumps(lesson_json)
                    break

                except Exception as e:
                    logger.warning(
                        "llm_instructor_failed_falling_back",
                        extra={"error": str(e), "retry_count": retry_count},
                    )

            if plan_id:
                with tracker.track_operation(plan_id, "llm_api_call") as op:
                    if retry_count > 0:
                        feedback_prompt = service._build_retry_prompt(
                            full_prompt,
                            validation_error,
                            retry_count,
                            available_days,
                            error_analysis,
                        )
                        response_text, usage = service._call_llm(feedback_prompt)
                    else:
                        response_text, usage = service._call_llm(full_prompt)
                    op["tokens_input"] = usage.get("tokens_input", 0)
                    op["tokens_output"] = usage.get("tokens_output", 0)
                    op["llm_model"] = service.model
                    op["llm_provider"] = service.provider
                    op["retry_count"] = retry_count
            else:
                if retry_count > 0:
                    feedback_prompt = service._build_retry_prompt(
                        full_prompt,
                        validation_error,
                        retry_count,
                        None,
                        error_analysis,
                    )
                    response_text, usage = service._call_llm(feedback_prompt)
                else:
                    response_text, usage = service._call_llm(full_prompt)

            if progress_callback:
                progress_callback(
                    "processing", 60, "AI response received. Processing results..."
                )

            was_truncated = usage.get("tokens_output", 0) >= (
                service.max_completion_tokens * 0.95
            )
            if was_truncated:
                logger.warning(
                    "llm_response_near_limit",
                    extra={
                        "tokens_output": usage.get("tokens_output", 0),
                        "max_completion_tokens": service.max_completion_tokens,
                        "model": service.model,
                        "retry_count": retry_count,
                    },
                )
                if retry_count < max_retries:
                    new_max_tokens = min(
                        int(service.max_completion_tokens * 1.5),
                        settings.MAX_COMPLETION_TOKENS * 2,
                        32000,
                    )
                    if new_max_tokens > service.max_completion_tokens:
                        logger.info(
                            "increasing_max_tokens_for_retry",
                            extra={
                                "old_max": service.max_completion_tokens,
                                "new_max": new_max_tokens,
                                "retry_count": retry_count,
                            },
                        )
                        service.max_completion_tokens = new_max_tokens

            if progress_callback:
                progress_callback("processing", 70, "Parsing AI response...")

            try:
                if plan_id:
                    with tracker.track_operation(plan_id, "llm_parse_response"):
                        lesson_json = parse_llm_response(response_text)
                else:
                    lesson_json = parse_llm_response(response_text)
            except ValueError as json_error:
                json_error_msg = str(json_error)
                error_analysis = getattr(json_error, "error_analysis", None)

                logger.warning(
                    "json_parse_error_retry",
                    extra={
                        "retry_count": retry_count,
                        "max_retries": max_retries,
                        "error": json_error_msg,
                        "response_length": len(response_text)
                        if response_text
                        else 0,
                        "tokens_output": usage.get("tokens_output", 0),
                        "was_truncated": was_truncated,
                        "error_analysis": error_analysis,
                    },
                )
                if retry_count < max_retries:
                    retry_count += 1
                    validation_error = (
                        f"JSON parsing failed: {json_error_msg}. "
                        "Please ensure the response is complete, valid JSON without truncation."
                    )
                    error_analysis = getattr(
                        json_error, "error_analysis", None
                    )
                    continue
                else:
                    service.max_completion_tokens = original_max_tokens
                    return (
                        False,
                        None,
                        f"Failed to parse JSON after {max_retries + 1} attempts: {json_error_msg}",
                    )

            if progress_callback:
                progress_callback(
                    "processing", 80, "Validating lesson plan structure..."
                )

            if plan_id:
                with tracker.track_operation(plan_id, "llm_validate_structure"):
                    is_valid, validation_error = validate_structure(lesson_json)
            else:
                is_valid, validation_error = validate_structure(lesson_json)

            if progress_callback:
                if is_valid:
                    progress_callback(
                        "processing",
                        90,
                        "Validation passed. Finalizing lesson plan...",
                    )
                else:
                    progress_callback(
                        "processing", 75, "Validation issue detected. Retrying..."
                    )

            if is_valid:
                service.max_completion_tokens = original_max_tokens
                break

            parsed_validation_errors = None
            if validation_error:
                parsed_validation_errors = parse_validation_errors(
                    validation_error
                )
                if error_analysis is None:
                    error_analysis = {}
                error_analysis["validation_errors"] = parsed_validation_errors

            logger.warning(
                "llm_validation_failed_retry",
                extra={
                    "retry_count": retry_count,
                    "max_retries": max_retries,
                    "validation_error": validation_error,
                    "parsed_errors": parsed_validation_errors,
                },
            )

            if retry_count < max_retries:
                retry_count += 1
                logger.info(
                    "llm_retry_attempt",
                    extra={
                        "retry_count": retry_count,
                        "validation_error": validation_error,
                        "parsed_errors": parsed_validation_errors,
                    },
                )
            else:
                service.max_completion_tokens = original_max_tokens
                return (
                    False,
                    None,
                    validation_error
                    or "Generated JSON does not match required schema structure",
                )

        lesson_json["_usage"] = usage
        lesson_json["_model"] = service.model
        lesson_json["_provider"] = service.provider

        logger.info(
            "llm_transform_success",
            extra={
                "response_length": len(response_text),
                "tokens_total": usage.get("tokens_total", 0),
            },
        )

        lesson_json = normalize_sentence_frame_punctuation(lesson_json)
        lesson_json = sanitize_lesson_json_strings(lesson_json)

        if plan_id:
            tracker.update_plan_summary(plan_id)

        return True, lesson_json, None

    except Exception as e:
        service.max_completion_tokens = original_max_tokens
        error_msg = f"LLM transformation failed: {str(e)}"
        logger.error("llm_transform_error", extra={"error": str(e)})
        return False, None, error_msg

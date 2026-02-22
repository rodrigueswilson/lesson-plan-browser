"""
Provider adapters for LLM API calls: OpenAI (raw + instructor), Anthropic.
"""

import time
from enum import Enum
from typing import Any, Dict, Optional, Tuple

from openai import APIError, RateLimitError

from backend.config import settings
from backend.lesson_schema_models import BilingualLessonPlanOutputSchema
from backend.telemetry import logger


def extract_retry_after(error: Exception) -> Optional[float]:
    """Extract retry-after time in seconds from rate limit error, or None."""
    if hasattr(error, "response") and error.response:
        retry_after = error.response.headers.get("retry-after")
        if retry_after:
            try:
                return float(retry_after)
            except (ValueError, TypeError):
                pass
    return None


def convert_enums_to_strings(data: Any) -> Any:
    """Recursively convert enum objects to their string values."""
    if isinstance(data, Enum):
        return data.value
    if isinstance(data, dict):
        return {k: convert_enums_to_strings(v) for k, v in data.items()}
    if isinstance(data, list):
        return [convert_enums_to_strings(item) for item in data]
    if isinstance(data, tuple):
        return tuple(convert_enums_to_strings(item) for item in data)
    return data


def check_for_enums(data: Any) -> bool:
    """Return True if data contains any enum objects."""
    if isinstance(data, Enum):
        return True
    if isinstance(data, dict):
        return any(check_for_enums(v) for v in data.values())
    if isinstance(data, (list, tuple)):
        return any(check_for_enums(item) for item in data)
    return False


def call_openai_chat_completion(
    client: Any,
    model: str,
    max_completion_tokens: int,
    prompt: str,
    *,
    response_format: Optional[Dict[str, Any]] = None,
    max_retries: Optional[int] = None,
) -> Tuple[str, Dict[str, int]]:
    """
    Call OpenAI chat.completions.create with optional response_format and rate limit handling.
    Returns (content, usage_dict).
    """
    if max_retries is None:
        max_retries = settings.RATE_LIMIT_RETRY_ATTEMPTS
    backoff_multiplier = settings.RATE_LIMIT_BACKOFF_MULTIPLIER

    kwargs: Dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_completion_tokens": max_completion_tokens,
    }
    if response_format:
        kwargs["response_format"] = response_format

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason

            usage = {
                "tokens_input": response.usage.prompt_tokens if response.usage else 0,
                "tokens_output": response.usage.completion_tokens if response.usage else 0,
                "tokens_total": response.usage.total_tokens if response.usage else 0,
            }

            logger.debug(
                "llm_response_received",
                extra={
                    "finish_reason": finish_reason,
                    "content_length": len(content) if content else 0,
                    "tokens_output": usage.get("tokens_output", 0),
                    "max_completion_tokens": max_completion_tokens,
                },
            )

            if finish_reason == "length":
                logger.warning(
                    "llm_response_truncated_attempting_repair",
                    extra={
                        "model": model,
                        "tokens_output": usage.get("tokens_output", 0),
                        "max_completion_tokens": max_completion_tokens,
                        "content_length": len(content) if content else 0,
                        "response_preview": content[:500] if content else None,
                        "note": "Response truncated but will attempt JSON repair",
                    },
                )

            if not content:
                logger.error(
                    "openai_empty_response",
                    extra={"finish_reason": finish_reason, "model": model},
                )
                raise ValueError(
                    f"OpenAI returned empty response. Finish reason: {finish_reason}"
                )

            return content, usage

        except RateLimitError as e:
            last_error = e
            retry_after = extract_retry_after(e)
            wait_time = retry_after or (backoff_multiplier**attempt)
            logger.warning(
                "openai_rate_limit_retry",
                extra={
                    "attempt": attempt + 1,
                    "max_retries": max_retries,
                    "total_attempts": max_retries + 1,
                    "wait_time": wait_time,
                    "retry_after": retry_after,
                    "model": model,
                },
            )
            if attempt < max_retries:
                time.sleep(wait_time)
                continue
            logger.error(
                "openai_rate_limit_exceeded",
                extra={
                    "max_retries": max_retries,
                    "total_attempts": max_retries + 1,
                    "model": model,
                    "error": str(e),
                },
            )
            raise

        except APIError as e:
            error_str = str(e).lower()
            if "429" in str(e) or "rate limit" in error_str:
                last_error = e
                wait_time = backoff_multiplier**attempt
                logger.warning(
                    "openai_rate_limit_detected",
                    extra={
                        "attempt": attempt + 1,
                        "max_retries": max_retries,
                        "total_attempts": max_retries + 1,
                        "wait_time": wait_time,
                        "model": model,
                        "error": str(e),
                    },
                )
                if attempt < max_retries:
                    time.sleep(wait_time)
                    continue
                logger.error(
                    "openai_rate_limit_exceeded",
                    extra={
                        "max_retries": max_retries,
                        "total_attempts": max_retries + 1,
                        "model": model,
                        "error": str(e),
                    },
                )
                raise RateLimitError(
                    f"Rate limit exceeded after {max_retries + 1} attempts: {str(e)}"
                )
            raise

    if last_error:
        raise last_error
    raise RuntimeError("Unexpected error in call_openai_chat_completion")


def call_anthropic_messages(
    client: Any,
    model: str,
    max_tokens: int,
    prompt: str,
) -> Tuple[str, Dict[str, int]]:
    """Call Anthropic messages.create. Returns (content_text, usage_dict)."""
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    usage = {
        "tokens_input": response.usage.input_tokens if response.usage else 0,
        "tokens_output": response.usage.output_tokens if response.usage else 0,
        "tokens_total": (
            (response.usage.input_tokens + response.usage.output_tokens)
            if response.usage
            else 0
        ),
    }
    return response.content[0].text, usage


def call_instructor_chat_completion(
    instructor_client: Any,
    model: str,
    max_completion_tokens: int,
    prompt: str,
    *,
    max_retries: Optional[int] = None,
    provider: str = "openai",
) -> Tuple[Dict[str, Any], Dict[str, int]]:
    """
    Call instructor library for schema-compliant response.
    Returns (lesson_dict, usage_dict).
    """
    if max_retries is None:
        max_retries = settings.RATE_LIMIT_RETRY_ATTEMPTS

    logger.info("llm_instructor_call_started", extra={"model": model})

    try:
        logger.debug(
            "llm_instructor_calling_api",
            extra={"model": model, "provider": provider},
        )

        if provider == "openai":
            response, completion = (
                instructor_client.chat.completions.create_with_completion(
                    model=model,
                    response_model=BilingualLessonPlanOutputSchema,
                    messages=[{"role": "user", "content": prompt}],
                    max_completion_tokens=max_completion_tokens,
                    max_retries=max_retries,
                )
            )
            usage = {
                "tokens_input": completion.usage.prompt_tokens
                if completion.usage
                else 0,
                "tokens_output": completion.usage.completion_tokens
                if completion.usage
                else 0,
                "tokens_total": completion.usage.total_tokens
                if completion.usage
                else 0,
            }
        else:
            response = instructor_client.chat.completions.create(
                model=model,
                response_model=BilingualLessonPlanOutputSchema,
                messages=[{"role": "user", "content": prompt}],
                max_retries=max_retries,
            )
            usage = {"tokens_input": 0, "tokens_output": 0, "tokens_total": 0}

        logger.debug(
            "llm_instructor_api_success",
            extra={"response_type": type(response).__name__},
        )

        logger.debug(
            "llm_instructor_converting_to_dict",
            extra={"response_type": type(response).__name__},
        )
        try:
            lesson_dict = response.model_dump(mode="json", exclude_none=False)
            logger.debug(
                "llm_instructor_dict_conversion_success",
                extra={"has_enums": check_for_enums(lesson_dict)},
            )
        except (TypeError, ValueError) as dump_error:
            error_msg = str(dump_error)
            if "not JSON serializable" in error_msg or any(
                enum_name in error_msg
                for enum_name in ["ProficiencyLevel", "PatternId", "FrameType"]
            ):
                logger.warning(
                    "llm_instructor_enum_serialization_fallback",
                    extra={
                        "error": error_msg,
                        "fallback": "Using default model_dump + manual enum conversion",
                    },
                )
                lesson_dict = response.model_dump(exclude_none=False)
                lesson_dict = convert_enums_to_strings(lesson_dict)
                logger.debug(
                    "llm_instructor_enum_conversion_complete",
                    extra={"has_enums": check_for_enums(lesson_dict)},
                )
            else:
                raise

        return lesson_dict, usage

    except Exception as e:
        error_msg = str(e)
        logger.error(
            "llm_instructor_error",
            extra={
                "error": error_msg,
                "error_type": type(e).__name__,
                "is_serialization_error": "not JSON serializable" in error_msg
                or any(
                    enum_name in error_msg
                    for enum_name in ["ProficiencyLevel", "PatternId", "FrameType"]
                ),
            },
        )
        raise

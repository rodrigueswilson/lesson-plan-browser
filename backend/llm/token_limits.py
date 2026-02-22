"""
Max completion token resolution: env override, model-specific limits, config default.
"""

import os
from typing import Optional

from backend.config import settings
from backend.telemetry import logger


def get_model_token_limit(model: Optional[str]) -> Optional[int]:
    """
    Get the maximum completion token limit for the given model.

    Returns:
        Token limit if known, None otherwise.
    """
    # Order matters: more specific model names first (e.g. gpt-5-mini before gpt-5)
    limits = {
        "gpt-4-turbo-preview": 16384,
        "gpt-4-turbo": 16384,
        "gpt-4o-mini": 16384,
        "gpt-4o": 16384,
        "gpt-4": 16384,
        "gpt-3.5-turbo": 4096,
        "gpt-5-mini": 32768,
        "gpt-5-nano": 8192,
        "gpt-5": 16384,
        "o1-preview": 32768,
        "o1-mini": 65536,
        "claude-3-opus": 4096,
        "claude-3-sonnet": 4096,
        "claude-3-haiku": 4096,
    }

    model_name = (model or "").lower()

    for key, limit in limits.items():
        if key in model_name:
            logger.info(
                "model_token_limit_found",
                extra={"model": model, "limit": limit},
            )
            return limit

    logger.warning("model_token_limit_unknown", extra={"model": model})
    return None


def get_max_completion_tokens(
    provider: str,
    model: Optional[str],
) -> int:
    """
    Determine max completion tokens based on model limits and configuration.

    Priority:
    1. LLM_MAX_COMPLETION_TOKENS environment variable
    2. Model-specific limit (if known)
    3. settings.MAX_COMPLETION_TOKENS

    Returns:
        Maximum completion tokens to request.
    """
    env_value = os.getenv("LLM_MAX_COMPLETION_TOKENS")
    if env_value:
        try:
            override = int(env_value)
            logger.info("using_env_max_tokens", extra={"value": override})
            return override
        except ValueError:
            logger.warning(
                "invalid_max_completion_tokens_env",
                extra={"value": env_value},
            )

    model_limit = get_model_token_limit(model)
    if model_limit is not None:
        return model_limit

    return settings.MAX_COMPLETION_TOKENS

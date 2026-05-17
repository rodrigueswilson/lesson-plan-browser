"""
WIDA ELD code format validation and normalization for wida_objective strings.

Single source of truth for ELD code regex and Function/Domain slash repair
(ELD-XX.#-#.Explain/Speaking -> ELD-XX.#-#.Explain.Speaking).
"""

from __future__ import annotations

import re

NO_SCHOOL_VALUES = frozenset(
    {"no school", "holiday", "teacher workday", "testing"}
)

WIDA_ELD_CODE_RE = re.compile(
    r"ELD-[A-Z]{2}\.[0-9K-]+\.[A-Za-z]+\.(?:Listening|Reading|Speaking|Writing)"
    r"(?:/(?:Listening|Reading|Speaking|Writing))*"
)

# Pydantic Field(pattern=...) for lesson_schema_models.Objective.wida_objective
WIDA_OBJECTIVE_FIELD_PATTERN = (
    r".*ELD-[A-Z]{2}\.[0-9K-]+\.[A-Za-z]+\."
    r"(?:Listening|Reading|Speaking|Writing)"
    r"(?:/(?:Listening|Reading|Speaking|Writing))*.*"
)

_FUNCTION_DOMAIN_SLASH_RE = re.compile(
    r"(ELD-[A-Z]{2}\.[0-9K-]+\.[A-Za-z]+)/(Listening|Reading|Speaking|Writing)"
)

WIDA_OBJECTIVE_MIN_LENGTH = 50

_INVALID_ELD_MESSAGE = (
    "wida_objective must include an ELD code with domain(s) "
    "(e.g., ELD-SS.6-8.Explain.Writing or ELD-SS.6-8.Explain.Listening/Speaking "
    "or ELD-SS.6-8.Explain.Listening/Reading/Speaking/Writing)"
)


def is_no_school_wida_objective(value: str) -> bool:
    if not isinstance(value, str):
        try:
            value = str(value)
        except (TypeError, ValueError):
            return False
    return value.strip().lower() in NO_SCHOOL_VALUES


def normalize_eld_function_domain_slash(text: str) -> str:
    """Fix ELD-XX.#-#.Function/Domain -> ELD-XX.#-#.Function.Domain (idempotent)."""
    return _FUNCTION_DOMAIN_SLASH_RE.sub(r"\1.\2", text)


def validate_and_normalize_wida_objective(
    value: str,
    *,
    min_length: int = WIDA_OBJECTIVE_MIN_LENGTH,
    log_normalization: bool = True,
) -> str:
    """
    Validate wida_objective and return normalized text when ELD slash format was repaired.

    Raises ValueError on invalid input (same contract as ObjectiveData validator).
    """
    if is_no_school_wida_objective(value):
        return value
    if len(value.strip()) < min_length:
        raise ValueError(
            "wida_objective must be at least 50 characters unless 'No School'"
        )

    normalized_value = normalize_eld_function_domain_slash(value)

    if log_normalization and normalized_value != value:
        from backend.telemetry import logger

        logger.debug(
            "eld_code_normalized",
            extra={
                "original": value[:100] if len(value) > 100 else value,
                "normalized": normalized_value[:100]
                if len(normalized_value) > 100
                else normalized_value,
            },
        )

    if not WIDA_ELD_CODE_RE.search(normalized_value):
        raise ValueError(_INVALID_ELD_MESSAGE)

    return normalized_value if normalized_value != value else value

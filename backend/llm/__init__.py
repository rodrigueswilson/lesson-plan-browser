"""
LLM package: prompt building, validation/retry logic, schema, post-process, and provider adapters.
Used by backend.llm_service.LLMService.
"""

from backend.llm.domain_analysis import analyze_domains_from_activities
from backend.llm.post_process import normalize_sentence_frame_punctuation
from backend.llm.schema import (
    build_openai_structured_schema,
    load_schema,
    model_supports_json_mode,
    model_supports_structured_outputs,
    structured_response_format,
)
from backend.llm.validation import (
    analyze_json_error,
    detect_truncation,
    parse_llm_response,
    parse_validation_errors,
    pre_validate_json,
    validate_structure,
)

__all__ = [
    "analyze_domains_from_activities",
    "analyze_json_error",
    "build_openai_structured_schema",
    "detect_truncation",
    "load_schema",
    "model_supports_json_mode",
    "model_supports_structured_outputs",
    "normalize_sentence_frame_punctuation",
    "parse_llm_response",
    "parse_validation_errors",
    "pre_validate_json",
    "structured_response_format",
    "validate_structure",
]

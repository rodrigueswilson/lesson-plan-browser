"""
Integration tests for JSON error prevention and correction.
Tests pre-validation, error analysis, repair, and retry prompt wiring.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.llm.prompt_builder import build_retry_prompt
from backend.llm.validation import analyze_json_error, parse_llm_response


def test_pre_validation_catches_before_parse():
    """Pre-validation / repair path can recover common issues before parse."""
    mock_response = '{"days": {monday: {"key": "value"}}}'
    result = parse_llm_response(mock_response)
    assert result is not None
    assert "days" in result


def test_error_analysis_feeds_into_retry_prompt():
    """Error analysis fields appear in retry prompt text."""
    error_analysis = {
        "error_type": "unquoted_property_name",
        "error_position": 100,
        "problematic_snippet": '{key: "value"}',
        "day_being_generated": "wednesday",
        "field_being_generated": "unit_lesson",
    }

    retry_prompt = build_retry_prompt(
        original_prompt="Generate lesson plan",
        validation_error="JSON parsing failed",
        retry_count=1,
        available_days=None,
        error_analysis=error_analysis,
    )

    assert "unquoted" in retry_prompt.lower() or "property name" in retry_prompt.lower()
    assert "wednesday" in retry_prompt
    assert error_analysis["problematic_snippet"] in retry_prompt


def test_position_aware_repair_focuses_on_error():
    """Repair uses error position when provided."""
    from tools.json_repair import repair_json

    json_str = '{"monday": {"a": 1, key: "value"}, "tuesday": {"b": 2}}'
    error_pos = json_str.find("key:")
    error_analysis = {"error_position": error_pos, "error_type": "unquoted_property_name"}

    success, repaired, msg = repair_json(json_str, error_pos, error_analysis)
    assert success, f"Repair failed: {msg}"
    assert "monday" in repaired or "tuesday" in repaired, "Should preserve day structures"


def test_full_parse_with_pre_validation():
    """Trailing comma fixed via pre-validation inside parse_llm_response."""
    json_str = '{"key": "value",}'
    result = parse_llm_response(json_str)
    assert result is not None
    assert result["key"] == "value"


def test_error_analysis_completeness():
    """Error analysis dict includes fields used by retry/logging."""
    json_str = '{"days": {"monday": {"key": "value"'
    try:
        json.loads(json_str)
    except json.JSONDecodeError as e:
        analysis = analyze_json_error(json_str, e)

        required_fields = [
            "error_type",
            "error_position",
            "error_position_percent",
            "context_before",
            "context_after",
            "problematic_snippet",
            "day_being_generated",
            "field_being_generated",
            "response_length",
            "was_truncated",
            "complete_days_before_error",
            "character_analysis",
        ]

        for field in required_fields:
            assert field in analysis, f"Missing field: {field}"


def main():
    import pytest

    raise SystemExit(pytest.main([__file__, "-v"]))


if __name__ == "__main__":
    main()

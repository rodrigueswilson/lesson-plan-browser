"""
Unit tests for JSON error prevention and correction features.
Targets backend.llm modules (logic moved off LLMService).
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.llm.error_analysis import (
    detect_error_type,
    identify_day_at_position,
    identify_field_at_position,
)
from backend.llm.json_pre_validation import pre_validate_json
from backend.llm.validation import analyze_json_error

pytestmark = pytest.mark.unit


def test_pre_validate_unquoted_property():
    """Test detection of unquoted property names"""
    json_str = '{key: "value"}'
    is_valid, error_msg, fixes = pre_validate_json(json_str)

    assert not is_valid, "Should detect unquoted property"
    assert error_msg and (
        "unquoted" in error_msg.lower() or "property" in error_msg.lower()
    )


def test_pre_validate_unmatched_quotes():
    """Test detection of unmatched quotes"""
    json_str = '{"key": "value}'
    is_valid, error_msg, fixes = pre_validate_json(json_str)

    assert not is_valid, "Should detect unmatched quotes"
    assert error_msg and (
        "unmatched" in error_msg.lower() or "quote" in error_msg.lower()
    )


def test_pre_validate_trailing_comma():
    """Test detection of trailing commas"""
    json_str = '{"key": "value",}'
    is_valid, error_msg, fixes = pre_validate_json(json_str)

    assert not is_valid, "Should detect trailing comma"
    assert error_msg and (
        "trailing" in error_msg.lower() or "comma" in error_msg.lower()
    )


def test_pre_validate_valid_json():
    """Test that valid JSON passes pre-validation"""
    json_str = '{"key": "value"}'
    is_valid, error_msg, fixes = pre_validate_json(json_str)

    assert is_valid, "Valid JSON should pass pre-validation"
    assert error_msg is None


def test_analyze_error_extracts_position():
    """Test error position extraction"""
    json_str = '{"key": "value"'
    try:
        json.loads(json_str)
    except json.JSONDecodeError as e:
        analysis = analyze_json_error(json_str, e)
        assert "error_position" in analysis
        assert analysis["error_position"] > 0


def test_analyze_error_identifies_day():
    """Test day identification at error position"""
    json_str = '{"days": {"monday": {"key": "value"'
    try:
        json.loads(json_str)
    except json.JSONDecodeError as e:
        analysis = analyze_json_error(json_str, e)
        assert analysis["day_being_generated"] == "monday"


def test_analyze_error_extracts_context():
    """Test context extraction around error"""
    json_str = '{"key": "value"'
    try:
        json.loads(json_str)
    except json.JSONDecodeError as e:
        analysis = analyze_json_error(json_str, e)
        assert "context_before" in analysis
        assert "context_after" in analysis
        assert len(analysis["context_before"]) > 0


def test_identify_day_at_position():
    """Test day identification helper"""
    json_str = '{"days": {"monday": {"a": 1}, "tuesday": {"b": 2'
    pos = json_str.find('"b": 2')
    day = identify_day_at_position(json_str, pos)
    assert day == "tuesday"


def test_identify_field_at_position():
    """Test field identification helper"""
    json_str = '{"days": {"monday": {"unit_lesson": "Test", "objective": {"content'
    pos = json_str.find('"content')
    field = identify_field_at_position(json_str, pos)
    assert field in ["objective", "content_objective"]


def test_detect_error_type():
    """Test error type detection"""
    json_str = '{key: "value"}'
    try:
        json.loads(json_str)
    except json.JSONDecodeError as e:
        error_pos = getattr(e, "pos", 0)
        error_type = detect_error_type(e, json_str, error_pos)
        assert error_type == "unquoted_property_name"


def main():
    """Run all tests (script mode)."""
    import pytest

    raise SystemExit(pytest.main([__file__, "-v"]))


if __name__ == "__main__":
    main()

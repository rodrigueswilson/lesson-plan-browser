"""
Unit tests for JSON error prevention and correction features.
Tests the new helper methods and pre-validation logic.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.llm_service import LLMService


def test_pre_validate_unquoted_property():
    """Test detection of unquoted property names"""
    print("Test 1: Pre-validate unquoted property")
    service = LLMService(provider="openai")
    json_str = '{key: "value"}'
    is_valid, error_msg, fixes = service._pre_validate_json(json_str)
    
    assert not is_valid, "Should detect unquoted property"
    assert "unquoted" in error_msg.lower() or "property" in error_msg.lower()
    print(f"  OK Detected: {error_msg}")


def test_pre_validate_unmatched_quotes():
    """Test detection of unmatched quotes"""
    print("\nTest 2: Pre-validate unmatched quotes")
    service = LLMService(provider="openai")
    json_str = '{"key": "value}'
    is_valid, error_msg, fixes = service._pre_validate_json(json_str)
    
    assert not is_valid, "Should detect unmatched quotes"
    assert "unmatched" in error_msg.lower() or "quote" in error_msg.lower()
    print(f"  OK Detected: {error_msg}")


def test_pre_validate_trailing_comma():
    """Test detection of trailing commas"""
    print("\nTest 3: Pre-validate trailing comma")
    service = LLMService(provider="openai")
    json_str = '{"key": "value",}'
    is_valid, error_msg, fixes = service._pre_validate_json(json_str)
    
    assert not is_valid, "Should detect trailing comma"
    assert "trailing" in error_msg.lower() or "comma" in error_msg.lower()
    print(f"  OK Detected: {error_msg}")


def test_pre_validate_valid_json():
    """Test that valid JSON passes pre-validation"""
    print("\nTest 4: Pre-validate valid JSON")
    service = LLMService(provider="openai")
    json_str = '{"key": "value"}'
    is_valid, error_msg, fixes = service._pre_validate_json(json_str)
    
    assert is_valid, "Valid JSON should pass pre-validation"
    assert error_msg is None
    print("  OK Valid JSON passed")


def test_analyze_error_extracts_position():
    """Test error position extraction"""
    print("\nTest 5: Analyze error extracts position")
    service = LLMService(provider="openai")
    json_str = '{"key": "value"'
    try:
        json.loads(json_str)
    except json.JSONDecodeError as e:
        analysis = service._analyze_json_error(json_str, e)
        assert "error_position" in analysis
        assert analysis["error_position"] > 0
        print(f"  OK Extracted position: {analysis['error_position']}")


def test_analyze_error_identifies_day():
    """Test day identification at error position"""
    print("\nTest 6: Analyze error identifies day")
    service = LLMService(provider="openai")
    json_str = '{"days": {"monday": {"key": "value"'
    try:
        json.loads(json_str)
    except json.JSONDecodeError as e:
        analysis = service._analyze_json_error(json_str, e)
        assert analysis["day_being_generated"] == "monday"
        print(f"  OK Identified day: {analysis['day_being_generated']}")


def test_analyze_error_extracts_context():
    """Test context extraction around error"""
    print("\nTest 7: Analyze error extracts context")
    service = LLMService(provider="openai")
    json_str = '{"key": "value"'
    try:
        json.loads(json_str)
    except json.JSONDecodeError as e:
        analysis = service._analyze_json_error(json_str, e)
        assert "context_before" in analysis
        assert "context_after" in analysis
        assert len(analysis["context_before"]) > 0
        print(f"  OK Extracted context (before: {len(analysis['context_before'])} chars)")


def test_identify_day_at_position():
    """Test day identification helper"""
    print("\nTest 8: Identify day at position")
    service = LLMService(provider="openai")
    json_str = '{"days": {"monday": {"a": 1}, "tuesday": {"b": 2'
    pos = json_str.find('"b": 2')
    day = service._identify_day_at_position(json_str, pos)
    assert day == "tuesday"
    print(f"  OK Identified day: {day}")


def test_identify_field_at_position():
    """Test field identification helper"""
    print("\nTest 9: Identify field at position")
    service = LLMService(provider="openai")
    json_str = '{"days": {"monday": {"unit_lesson": "Test", "objective": {"content'
    pos = json_str.find('"content')
    field = service._identify_field_at_position(json_str, pos)
    assert field in ["objective", "content_objective"]
    print(f"  OK Identified field: {field}")


def test_detect_error_type():
    """Test error type detection"""
    print("\nTest 10: Detect error type")
    service = LLMService(provider="openai")
    json_str = '{key: "value"}'
    try:
        json.loads(json_str)
    except json.JSONDecodeError as e:
        error_type = service._detect_error_type(e, json_str, getattr(e, "pos", 0))
        assert error_type == "unquoted_property_name"
        print(f"  OK Detected type: {error_type}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("JSON Error Prevention Unit Tests")
    print("=" * 60 + "\n")
    
    tests = [
        test_pre_validate_unquoted_property,
        test_pre_validate_unmatched_quotes,
        test_pre_validate_trailing_comma,
        test_pre_validate_valid_json,
        test_analyze_error_extracts_position,
        test_analyze_error_identifies_day,
        test_analyze_error_extracts_context,
        test_identify_day_at_position,
        test_identify_field_at_position,
        test_detect_error_type,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  X FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  X ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

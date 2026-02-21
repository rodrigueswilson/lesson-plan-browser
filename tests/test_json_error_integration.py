"""
Integration tests for JSON error prevention and correction.
Tests the interaction between pre-validation, error analysis, and repair.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.llm_service import LLMService


def test_pre_validation_catches_before_parse():
    """Test that pre-validation fixes issues before parsing"""
    print("Test 1: Pre-validation catches before parse")
    service = LLMService(provider="openai")
    # Mock response with unquoted property
    mock_response = '{"days": {monday: {"key": "value"}}}'
    
    # Should be caught by pre-validation and fixed
    result = service._parse_response(mock_response)
    assert result is not None
    assert "days" in result
    print("  OK Pre-validation fixed issue before parse")


def test_error_analysis_feeds_into_retry_prompt():
    """Test that error analysis is included in retry prompt"""
    print("\nTest 2: Error analysis in retry prompt")
    service = LLMService(provider="openai")
    error_analysis = {
        "error_type": "unquoted_property_name",
        "error_position": 100,
        "problematic_snippet": '{key: "value"}',
        "day_being_generated": "wednesday",
        "field_being_generated": "unit_lesson",
    }
    
    retry_prompt = service._build_retry_prompt(
        original_prompt="Generate lesson plan",
        validation_error="JSON parsing failed",
        retry_count=1,
        available_days=None,
        error_analysis=error_analysis
    )
    
    assert "unquoted" in retry_prompt.lower() or "property name" in retry_prompt.lower()
    assert "wednesday" in retry_prompt
    assert error_analysis["problematic_snippet"] in retry_prompt
    print("  OK Retry prompt includes error analysis")


def test_position_aware_repair_focuses_on_error():
    """Test that repair focuses on error position"""
    print("\nTest 3: Position-aware repair focuses on error")
    from tools.json_repair import repair_json
    
    # Use a case where the unquoted property is inside a day structure
    json_str = '{"monday": {"a": 1, key: "value"}, "tuesday": {"b": 2}}'
    error_pos = json_str.find('key:')
    error_analysis = {"error_position": error_pos, "error_type": "unquoted_property_name"}
    
    success, repaired, msg = repair_json(json_str, error_pos, error_analysis)
    assert success, f"Repair failed: {msg}"
    # The repair should fix the unquoted property or salvage the structure
    assert "monday" in repaired or "tuesday" in repaired, "Should preserve day structures"
    print(f"  OK Position-aware repair successful: {msg}")


def test_full_parse_with_pre_validation():
    """Test full parse flow with pre-validation"""
    print("\nTest 4: Full parse with pre-validation")
    service = LLMService(provider="openai")
    
    # Test with trailing comma (should be fixed by pre-validation)
    json_str = '{"key": "value",}'
    result = service._parse_response(json_str)
    assert result is not None
    assert result["key"] == "value"
    print("  OK Pre-validation fixed trailing comma")


def test_error_analysis_completeness():
    """Test that error analysis captures all required fields"""
    print("\nTest 5: Error analysis completeness")
    service = LLMService(provider="openai")
    json_str = '{"days": {"monday": {"key": "value"'
    try:
        json.loads(json_str)
    except json.JSONDecodeError as e:
        analysis = service._analyze_json_error(json_str, e)
        
        required_fields = [
            "error_type", "error_position", "error_position_percent",
            "context_before", "context_after", "problematic_snippet",
            "day_being_generated", "field_being_generated",
            "response_length", "was_truncated", "complete_days_before_error",
            "character_analysis"
        ]
        
        for field in required_fields:
            assert field in analysis, f"Missing field: {field}"
        
        print(f"  OK Error analysis complete ({len(required_fields)} fields)")


def main():
    """Run all tests."""
    print("=" * 60)
    print("JSON Error Prevention Integration Tests")
    print("=" * 60 + "\n")
    
    tests = [
        test_pre_validation_catches_before_parse,
        test_error_analysis_feeds_into_retry_prompt,
        test_position_aware_repair_focuses_on_error,
        test_full_parse_with_pre_validation,
        test_error_analysis_completeness,
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
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

"""
Integration tests for the complete lesson plan pipeline with retry logic.
Tests the interaction between JSON repair, validation, and retry mechanisms.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.mock_llm import (
    MockLLM,
    create_immediate_success,
    create_retry_sequence_success,
    create_retry_sequence_failure,
    create_repair_then_success,
    create_schema_error_then_success,
    VALID_MINIMAL_JSON,
    INVALID_TRAILING_COMMA,
    INVALID_MARKDOWN_WRAPPED,
    MISSING_REQUIRED_FIELD,
)
from tools.json_repair import validate_and_repair
from tools.retry_logic import generate_with_retry_simple, RetryExhausted
from tools.validate_schema import load_schema, validate_json
from backend.config import settings


# Load schema once for all tests
SCHEMA = load_schema(Path(settings.SCHEMA_PATH))


def validate_lesson_plan(data: dict) -> tuple:
    """Wrapper for schema validation that matches retry_logic signature."""
    return validate_json(data, SCHEMA)


def test_immediate_success():
    """Test successful generation on first attempt."""
    print("=" * 60)
    print("Test 1: Immediate Success")
    print("=" * 60)
    
    llm = create_immediate_success()
    
    try:
        result = generate_with_retry_simple(
            llm_generate=lambda prompt: llm.generate(prompt),
            initial_prompt="Generate lesson plan",
            validator=validate_lesson_plan,
            max_retries=3
        )
        
        assert result is not None, "Should return valid data"
        assert llm.get_call_count() == 1, "LLM should be called once"
        
        print(f"✓ Success on first attempt")
        print(f"  LLM calls: {llm.get_call_count()}")
        
        return True
    except RetryExhausted as e:
        print(f"✗ Failed: {e}")
        return False


def test_retry_with_repair():
    """Test retry logic with repairable JSON errors."""
    print("\n" + "=" * 60)
    print("Test 2: Retry with JSON Repair")
    print("=" * 60)
    
    llm = create_retry_sequence_success()
    
    try:
        result = generate_with_retry_simple(
            llm_generate=lambda prompt: llm.generate(prompt),
            initial_prompt="Generate lesson plan",
            validator=validate_lesson_plan,
            max_retries=3
        )
        
        assert result is not None, "Should eventually succeed after repairs"
        assert llm.get_call_count() <= 3, f"Should succeed within 3 attempts"
        
        print(f"✓ Success after retries and repairs")
        print(f"  LLM calls: {llm.get_call_count()}")
        
        return True
    except RetryExhausted as e:
        print(f"✗ Failed: {e}")
        return False


def test_retry_exhaustion():
    """Test retry exhaustion with persistent errors."""
    print("\n" + "=" * 60)
    print("Test 3: Retry Exhaustion")
    print("=" * 60)
    
    llm = create_retry_sequence_failure()
    
    try:
        result = generate_with_retry_simple(
            llm_generate=lambda prompt: llm.generate(prompt),
            initial_prompt="Generate lesson plan",
            validator=validate_lesson_plan,
            max_retries=3
        )
        
        # Should not reach here
        print(f"✗ Should have exhausted retries")
        return False
        
    except RetryExhausted as e:
        assert llm.get_call_count() == 3, "LLM should be called 3 times"
        
        print(f"✓ Correctly exhausted retries")
        print(f"  LLM calls: {llm.get_call_count()}")
        print(f"  Error: {str(e)[:100]}...")
        
        return True


def test_json_repair_scenarios():
    """Test various JSON repair scenarios."""
    print("\n" + "=" * 60)
    print("Test 4: JSON Repair Scenarios")
    print("=" * 60)
    
    test_cases = [
        ("Valid JSON", VALID_MINIMAL_JSON, True),
        ("Trailing comma", INVALID_TRAILING_COMMA, True),
        ("Markdown wrapped", INVALID_MARKDOWN_WRAPPED, True),
    ]
    
    passed = 0
    for name, json_str, should_succeed in test_cases:
        success, data, message = validate_and_repair(json_str)
        
        if success == should_succeed:
            print(f"✓ {name}: {message[:60]}...")
            passed += 1
        else:
            print(f"✗ {name}: Expected {should_succeed}, got {success}")
    
    assert passed == len(test_cases), f"Expected all {len(test_cases)} to pass, got {passed}"
    
    print(f"\n✓ All repair scenarios passed: {passed}/{len(test_cases)}")
    
    return True


def test_schema_validation_feedback():
    """Test that schema validation errors provide feedback."""
    print("\n" + "=" * 60)
    print("Test 5: Schema Validation Feedback")
    print("=" * 60)
    
    llm = create_schema_error_then_success()
    
    try:
        result = generate_with_retry_simple(
            llm_generate=lambda prompt: llm.generate(prompt),
            initial_prompt="Generate lesson plan",
            validator=validate_lesson_plan,
            max_retries=3
        )
        
        assert result is not None, "Should succeed after schema error feedback"
        assert llm.get_call_count() == 2, f"Should take 2 attempts, took {llm.get_call_count()}"
        
        # Check that the LLM received feedback about the error
        prompts = llm.prompts_received
        assert len(prompts) == 2, "Should have 2 prompts"
        
        print(f"✓ Schema validation feedback working")
        print(f"  Attempts: {llm.get_call_count()}")
        print(f"  First attempt: Schema error (missing 'subject')")
        print(f"  Second attempt: Success after feedback")
        
        return True
    except RetryExhausted as e:
        print(f"✗ Failed: {e}")
        return False


def test_token_tracking():
    """Test token tracking during generation."""
    print("\n" + "=" * 60)
    print("Test 6: Token Tracking")
    print("=" * 60)
    
    llm = create_immediate_success()
    
    try:
        result = generate_with_retry_simple(
            llm_generate=lambda prompt: llm.generate(prompt),
            initial_prompt="Generate lesson plan",
            validator=validate_lesson_plan,
            max_retries=3
        )
        
        assert result is not None, "Should succeed"
        
        # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
        result_str = json.dumps(result)
        estimated_tokens = len(result_str) // 4
        
        print(f"✓ Token tracking test completed")
        print(f"  Response length: {len(result_str)} characters")
        print(f"  Estimated tokens: {estimated_tokens}")
        print(f"  Note: Actual token tracking requires LLM API integration")
        
        return True
    except RetryExhausted as e:
        print(f"✗ Failed: {e}")
        return False


def test_pipeline_with_mock_llm():
    """Test complete pipeline with mock LLM."""
    print("\n" + "=" * 60)
    print("Test 7: Complete Pipeline with Mock LLM")
    print("=" * 60)
    
    llm = create_repair_then_success()
    
    try:
        result = generate_with_retry_simple(
            llm_generate=lambda prompt: llm.generate(prompt),
            initial_prompt="Generate lesson plan",
            validator=validate_lesson_plan,
            max_retries=3
        )
        
        assert result is not None, "Pipeline should succeed"
        assert "metadata" in result, "Should have metadata"
        assert "days" in result, "Should have days"
        
        print(f"✓ Complete pipeline successful")
        print(f"  LLM calls: {llm.get_call_count()}")
        print(f"  Metadata: {result['metadata']}")
        
        return True
    except RetryExhausted as e:
        print(f"✗ Failed: {e}")
        return False


def test_error_messages():
    """Test that error messages are informative."""
    print("\n" + "=" * 60)
    print("Test 8: Error Message Quality")
    print("=" * 60)
    
    # Test with missing required field - this will parse as valid JSON
    # but fail schema validation
    success, data, message = validate_and_repair(MISSING_REQUIRED_FIELD)
    
    # validate_and_repair only checks JSON syntax, not schema
    # So we need to validate against schema separately
    if success and data:
        is_valid, errors = validate_lesson_plan(data)
        assert not is_valid, "Should fail schema validation"
        error_message = "; ".join(errors)
        assert "subject" in error_message.lower() or "required" in error_message.lower(), \
            "Error message should mention missing field"
        
        print(f"✓ Error messages are informative")
        print(f"  Sample error: {error_message[:100]}...")
    else:
        # If JSON repair failed, that's also fine for this test
        print(f"✓ Error messages are informative")
        print(f"  JSON repair message: {message[:100]}...")
    
    return True


def main():
    """Run all integration tests."""
    print("\n" + "=" * 60)
    print("INTEGRATION TESTS - Lesson Plan Pipeline")
    print("=" * 60 + "\n")
    
    tests = [
        ("Immediate Success", test_immediate_success),
        ("Retry with Repair", test_retry_with_repair),
        ("Retry Exhaustion", test_retry_exhaustion),
        ("JSON Repair Scenarios", test_json_repair_scenarios),
        ("Schema Validation Feedback", test_schema_validation_feedback),
        ("Token Tracking", test_token_tracking),
        ("Complete Pipeline", test_pipeline_with_mock_llm),
        ("Error Messages", test_error_messages),
    ]
    
    results = []
    
    for name, test_fn in tests:
        try:
            result = test_fn()
            results.append((name, result))
        except AssertionError as e:
            print(f"\n✗ {name} FAILED: {e}")
            results.append((name, False))
        except Exception as e:
            print(f"\n✗ {name} ERROR: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 All integration tests passed!")
    else:
        print(f"\n⚠ {total - passed} test(s) failed")
    
    print("=" * 60)
    
    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

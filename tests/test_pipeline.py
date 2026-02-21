"""
Test the complete lesson plan pipeline (and JSON repair when pipeline is in archive).
"""
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.json_repair import validate_and_repair

try:
    from tools.lesson_plan_pipeline import create_pipeline
except ImportError:
    create_pipeline = None


def test_pipeline_with_valid_json():
    """Test pipeline with valid JSON fixture (skips if lesson_plan_pipeline not installed)."""
    import pytest
    if create_pipeline is None:
        pytest.skip("tools.lesson_plan_pipeline not available (may be in archive)")
    fixture_path = Path(__file__).parent / "fixtures" / "valid_lesson_minimal.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)
    pipeline = create_pipeline()
    success, output, error = pipeline.process_from_json(
        json_data=json_data,
        lesson_id="test-001",
        output_path=Path("output/test_pipeline.md"),
    )
    assert success, error


def test_json_repair():
    """Test JSON repair functionality."""
    test_cases = [
        ("Valid JSON", '{"key": "value"}', True),
        ("Trailing comma", '{"key": "value",}', True),
        ("Markdown block", '```json\n{"key": "value"}\n```', True),
        ("Missing brace", '{"key": "value"', True),
        ("Comments", '{"key": "value" /* comment */}', True),
    ]
    for name, json_str, should_pass in test_cases:
        success, data, message = validate_and_repair(json_str)
        assert success == should_pass, f"{name}: expected {should_pass}, got {success}"


def test_validation_errors():
    """Test validation error handling (skips if pipeline not available)."""
    import pytest
    if create_pipeline is None:
        pytest.skip("tools.lesson_plan_pipeline not available")
    fixture_path = Path(__file__).parent / "fixtures" / "invalid_missing_required.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)
    pipeline = create_pipeline()
    success, output, error = pipeline.process_from_json(
        json_data=json_data, lesson_id="test-002"
    )
    assert not success, "Validation should have failed"


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Lesson Plan Pipeline Tests")
    print("=" * 60 + "\n")
    
    results = []
    
    # Test 1: Valid JSON
    try:
        results.append(("Valid JSON", test_pipeline_with_valid_json()))
    except Exception as e:
        print(f"✗ Test failed with exception: {e}")
        results.append(("Valid JSON", False))
    
    # Test 2: JSON Repair
    try:
        results.append(("JSON Repair", test_json_repair()))
    except Exception as e:
        print(f"✗ Test failed with exception: {e}")
        results.append(("JSON Repair", False))
    
    # Test 3: Validation Errors
    try:
        results.append(("Validation Errors", test_validation_errors()))
    except Exception as e:
        print(f"✗ Test failed with exception: {e}")
        results.append(("Validation Errors", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} passed")
    print("=" * 60)
    
    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

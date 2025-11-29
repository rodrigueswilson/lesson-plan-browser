"""
Test the complete lesson plan pipeline.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lesson_plan_pipeline import create_pipeline
from tools.json_repair import validate_and_repair


def test_pipeline_with_valid_json():
    """Test pipeline with valid JSON fixture."""
    print("=" * 60)
    print("Test 1: Pipeline with Valid JSON")
    print("=" * 60)
    
    # Load valid fixture
    fixture_path = Path('tests/fixtures/valid_lesson_minimal.json')
    with open(fixture_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    # Create pipeline
    pipeline = create_pipeline()
    
    # Process
    success, output, error = pipeline.process_from_json(
        json_data=json_data,
        lesson_id="test-001",
        output_path=Path('output/test_pipeline.md')
    )
    
    if success:
        print(f"✓ Pipeline succeeded")
        print(f"  Output size: {len(output)} characters")
        print(f"  Saved to: output/test_pipeline.md")
    else:
        print(f"✗ Pipeline failed: {error}")
    
    return success


def test_json_repair():
    """Test JSON repair functionality."""
    print("\n" + "=" * 60)
    print("Test 2: JSON Repair")
    print("=" * 60)
    
    test_cases = [
        ('Valid JSON', '{"key": "value"}', True),
        ('Trailing comma', '{"key": "value",}', True),
        ('Markdown block', '```json\n{"key": "value"}\n```', True),
        ('Missing brace', '{"key": "value"', True),
        ('Comments', '{"key": "value" /* comment */}', True),
    ]
    
    passed = 0
    for name, json_str, should_pass in test_cases:
        success, data, message = validate_and_repair(json_str)
        
        if success == should_pass:
            print(f"✓ {name}: {message}")
            passed += 1
        else:
            print(f"✗ {name}: Expected {should_pass}, got {success}")
    
    print(f"\nPassed: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def test_validation_errors():
    """Test validation error handling."""
    print("\n" + "=" * 60)
    print("Test 3: Validation Errors")
    print("=" * 60)
    
    # Load invalid fixture
    fixture_path = Path('tests/fixtures/invalid_missing_required.json')
    with open(fixture_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    # Create pipeline
    pipeline = create_pipeline()
    
    # Process (should fail validation)
    success, output, error = pipeline.process_from_json(
        json_data=json_data,
        lesson_id="test-002"
    )
    
    if not success:
        print(f"✓ Validation correctly failed")
        print(f"  Error: {error[:100]}...")
        return True
    else:
        print(f"✗ Validation should have failed but passed")
        return False


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

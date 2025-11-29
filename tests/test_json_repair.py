"""
Test JSON repair functionality (no external dependencies).
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.json_repair import validate_and_repair, repair_json, extract_json_from_text


def test_valid_json():
    """Test with valid JSON."""
    print("Test 1: Valid JSON")
    json_str = '{"key": "value"}'
    success, data, message = validate_and_repair(json_str)
    
    assert success, "Should succeed with valid JSON"
    assert data == {"key": "value"}
    print(f"  ✓ {message}")


def test_trailing_comma():
    """Test trailing comma removal."""
    print("\nTest 2: Trailing Comma")
    json_str = '{"key": "value",}'
    success, data, message = validate_and_repair(json_str)
    
    assert success, "Should repair trailing comma"
    assert data == {"key": "value"}
    print(f"  ✓ {message}")


def test_markdown_block():
    """Test markdown code block removal."""
    print("\nTest 3: Markdown Code Block")
    json_str = '```json\n{"key": "value"}\n```'
    success, data, message = validate_and_repair(json_str)
    
    assert success, "Should remove markdown blocks"
    assert data == {"key": "value"}
    print(f"  ✓ {message}")


def test_missing_brace():
    """Test missing closing brace."""
    print("\nTest 4: Missing Closing Brace")
    json_str = '{"key": "value"'
    success, data, message = validate_and_repair(json_str)
    
    assert success, "Should add missing brace"
    assert data == {"key": "value"}
    print(f"  ✓ {message}")


def test_comments():
    """Test comment removal."""
    print("\nTest 5: Comments")
    json_str = '{"key": "value" /* comment */}'
    success, data, message = validate_and_repair(json_str)
    
    assert success, "Should remove comments"
    assert data == {"key": "value"}
    print(f"  ✓ {message}")


def test_extract_json():
    """Test JSON extraction from text."""
    print("\nTest 6: Extract JSON from Text")
    text = 'Here is some JSON: {"key": "value"} and more text'
    extracted = extract_json_from_text(text)
    
    assert extracted == '{"key": "value"}'
    print(f"  ✓ Extracted JSON from surrounding text")


def test_complex_json():
    """Test with complex nested JSON."""
    print("\nTest 7: Complex Nested JSON")
    json_str = '''
    {
        "metadata": {
            "week_of": "10/6-10/10",
            "grade": "7"
        },
        "days": {
            "monday": {
                "unit_lesson": "Unit One"
            }
        }
    }
    '''
    success, data, message = validate_and_repair(json_str)
    
    assert success, "Should handle complex JSON"
    assert "metadata" in data
    assert "days" in data
    print(f"  ✓ {message}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("JSON Repair Tests")
    print("=" * 60 + "\n")
    
    tests = [
        test_valid_json,
        test_trailing_comma,
        test_markdown_block,
        test_missing_brace,
        test_comments,
        test_extract_json,
        test_complex_json,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

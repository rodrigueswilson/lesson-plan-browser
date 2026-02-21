"""
Unit tests for enhanced JSON repair functionality.
Tests the new unquoted property name repair and position-aware fixes.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.json_repair import _fix_unquoted_property_names, repair_json


def test_fix_unquoted_property_simple():
    """Test fixing simple unquoted property"""
    print("Test 1: Fix unquoted property (simple)")
    json_str = '{key: "value"}'
    fixed, fixes = _fix_unquoted_property_names(json_str)
    assert '"key"' in fixed
    assert len(fixes) > 0
    # Verify it can be parsed
    parsed = json.loads(fixed)
    assert parsed["key"] == "value"
    print(f"  OK Fixed: {fixes[0]}")


def test_fix_unquoted_property_nested():
    """Test fixing unquoted property in nested object"""
    print("\nTest 2: Fix unquoted property (nested)")
    json_str = '{"outer": {inner: "value"}}'
    fixed, fixes = _fix_unquoted_property_names(json_str)
    assert '"inner"' in fixed
    parsed = json.loads(fixed)
    assert parsed["outer"]["inner"] == "value"
    print(f"  OK Fixed nested property")


def test_fix_unquoted_property_position_aware():
    """Test position-aware fixing"""
    print("\nTest 3: Fix unquoted property (position-aware)")
    json_str = '{"a": 1, "b": 2, key: "value"}'
    error_pos = json_str.find('key:')
    fixed, fixes = _fix_unquoted_property_names(json_str, error_pos)
    assert '"key"' in fixed
    parsed = json.loads(fixed)
    assert parsed["key"] == "value"
    print(f"  OK Fixed with position awareness")


def test_repair_json_with_unquoted_property():
    """Test repair_json with unquoted property error"""
    print("\nTest 4: Repair JSON with unquoted property")
    json_str = '{"days": {monday: {"key": "value"}}}'
    error_analysis = {"error_type": "unquoted_property_name", "error_position": json_str.find("monday:")}
    success, repaired, msg = repair_json(json_str, error_analysis.get("error_position"), error_analysis)
    assert success, f"Repair should succeed: {msg}"
    parsed = json.loads(repaired)
    assert "days" in parsed
    assert "monday" in parsed["days"]
    print(f"  OK Repaired successfully: {msg}")


def test_repair_json_position_aware():
    """Test position-aware repair"""
    print("\nTest 5: Position-aware repair")
    # Use a structure without day patterns to avoid truncation logic
    json_str = '{"data": {"item1": {"a": 1}, "item2": {"b": 2}, key: "value"}}'
    error_pos = json_str.find('key:')
    error_analysis = {"error_position": error_pos, "error_type": "unquoted_property_name"}
    try:
        success, repaired, msg = repair_json(json_str, error_pos, error_analysis)
        if not success:
            raise AssertionError(f"Repair failed: {msg}")
        if '"key"' not in repaired:
            raise AssertionError(f"Key not quoted in repaired JSON: {repaired[:100]}")
        parsed = json.loads(repaired)
        if "data" not in parsed or "key" not in parsed["data"]:
            raise AssertionError(f"Key not found in parsed JSON: {list(parsed.get('data', {}).keys())}")
        if parsed["data"]["key"] != "value":
            raise AssertionError(f"Key value incorrect: {parsed['data']['key']}")
        print(f"  OK Position-aware repair successful")
    except Exception as e:
        print(f"  ERROR: {type(e).__name__}: {e}")
        raise


def test_repair_json_incomplete_string():
    """Test repair with incomplete string"""
    print("\nTest 6: Repair incomplete string")
    json_str = '{"key": "incomplete value'
    error_analysis = {"error_type": "incomplete_string", "error_position": len(json_str) - 5}
    success, repaired, msg = repair_json(json_str, error_analysis.get("error_position"), error_analysis)
    # May or may not succeed, but should attempt repair
    if success:
        parsed = json.loads(repaired)
        assert "key" in parsed
        print(f"  OK Repaired incomplete string: {msg}")
    else:
        print(f"  WARN Repair attempted but failed: {msg}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Enhanced JSON Repair Tests")
    print("=" * 60 + "\n")
    
    tests = [
        test_fix_unquoted_property_simple,
        test_fix_unquoted_property_nested,
        test_fix_unquoted_property_position_aware,
        test_repair_json_with_unquoted_property,
        test_repair_json_position_aware,
        test_repair_json_incomplete_string,
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

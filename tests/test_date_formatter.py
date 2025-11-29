"""
Unit tests for date formatter utility.

Run with: python test_date_formatter.py
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.utils.date_formatter import format_week_dates, validate_week_format, parse_week_dates


def test_format_week_dates():
    """Test various input formats are normalized correctly."""
    
    print("Testing format_week_dates()...")
    
    test_cases = [
        # (input, expected_output, description)
        ("10-27-10-31", "10/27-10/31", "Hyphen format"),
        ("10/27-10/31", "10/27-10/31", "Already correct"),
        ("10-27 to 10-31", "10/27-10/31", "With 'to' separator"),
        ("Week of 10/27-10/31", "10/27-10/31", "With 'Week of' prefix"),
        ("week of 10-27-10-31", "10/27-10/31", "Lowercase prefix"),
        ("10/27/2025-10/31/2025", "10/27-10/31", "With years"),
        ("10-27-2025 to 10-31-2025", "10/27-10/31", "Years with 'to'"),
        ("  10/27-10/31  ", "10/27-10/31", "Extra whitespace"),
        ("10 / 27 - 10 / 31", "10/27-10/31", "Spaces in dates"),
        ("9/15-9/19", "9/15-9/19", "Single digit months/days"),
        ("", "", "Empty string"),
        ("invalid", "invalid", "Unparseable - return as-is"),
    ]
    
    passed = 0
    failed = 0
    
    for input_str, expected, description in test_cases:
        result = format_week_dates(input_str)
        if result == expected:
            print(f"  ✓ {description}: '{input_str}' → '{result}'")
            passed += 1
        else:
            print(f"  ✗ {description}: '{input_str}' → '{result}' (expected '{expected}')")
            failed += 1
    
    print(f"\nformat_week_dates: {passed} passed, {failed} failed\n")
    return failed == 0


def test_validate_week_format():
    """Test week format validation."""
    
    print("Testing validate_week_format()...")
    
    test_cases = [
        # (input, expected_valid, description)
        ("10/27-10/31", True, "Valid format"),
        ("9/15-9/19", True, "Single digit valid"),
        ("12/1-12/5", True, "Mixed digits valid"),
        ("10-27-10-31", False, "Hyphens instead of slashes"),
        ("10/27/2025-10/31/2025", False, "With years"),
        ("Week of 10/27-10/31", False, "With prefix"),
        ("10/27", False, "Missing end date"),
        ("invalid", False, "Not a date"),
        ("", False, "Empty string"),
        ("10/27-10/31/2025", False, "Year on end only"),
    ]
    
    passed = 0
    failed = 0
    
    for input_str, expected_valid, description in test_cases:
        result = validate_week_format(input_str)
        if result == expected_valid:
            print(f"  ✓ {description}: '{input_str}' → {result}")
            passed += 1
        else:
            print(f"  ✗ {description}: '{input_str}' → {result} (expected {expected_valid})")
            failed += 1
    
    print(f"\nvalidate_week_format: {passed} passed, {failed} failed\n")
    return failed == 0


def test_parse_week_dates():
    """Test parsing week dates into components."""
    
    print("Testing parse_week_dates()...")
    
    test_cases = [
        # (input, expected_output, description)
        ("10/27-10/31", ("10", "27", "10", "31"), "Valid format"),
        ("9/15-9/19", ("9", "15", "9", "19"), "Single digits"),
        ("12/1-12/5", ("12", "1", "12", "5"), "Mixed digits"),
        ("10-27-10-31", None, "Invalid format"),
        ("invalid", None, "Not a date"),
        ("", None, "Empty string"),
    ]
    
    passed = 0
    failed = 0
    
    for input_str, expected, description in test_cases:
        result = parse_week_dates(input_str)
        if result == expected:
            print(f"  ✓ {description}: '{input_str}' → {result}")
            passed += 1
        else:
            print(f"  ✗ {description}: '{input_str}' → {result} (expected {expected})")
            failed += 1
    
    print(f"\nparse_week_dates: {passed} passed, {failed} failed\n")
    return failed == 0


def test_edge_cases():
    """Test edge cases and special scenarios."""
    
    print("Testing edge cases...")
    
    test_cases = [
        # Single date with 5-day assumption
        ("10/27", "10/27-10/31", "Single date → 5-day week"),
        ("Week of 10/27", "10/27-10/31", "Single date with prefix"),
        
        # Month boundaries (simplified - doesn't handle correctly yet)
        # Note: Current implementation doesn't handle month boundaries properly
        # This is documented as a known limitation
        
        # Multiple spaces and mixed case
        ("WEEK OF 10/27-10/31", "10/27-10/31", "Uppercase prefix"),
        ("   Week   of   10/27-10/31   ", "10/27-10/31", "Multiple spaces"),
        
        # Different separators
        ("10-27TO10-31", "10/27-10/31", "TO separator"),
        ("10/27TO10/31", "10/27-10/31", "TO with slashes"),
    ]
    
    passed = 0
    failed = 0
    
    for input_str, expected, description in test_cases:
        result = format_week_dates(input_str)
        if result == expected:
            print(f"  ✓ {description}: '{input_str}' → '{result}'")
            passed += 1
        else:
            print(f"  ✗ {description}: '{input_str}' → '{result}' (expected '{expected}')")
            failed += 1
    
    print(f"\nEdge cases: {passed} passed, {failed} failed\n")
    return failed == 0


def test_real_world_examples():
    """Test with real examples from the codebase."""
    
    print("Testing real-world examples...")
    
    test_cases = [
        ("10-27-10-31", "10/27-10/31", "Example from requirements"),
        ("10/27-10/31", "10/27-10/31", "Example from requirements"),
        ("9/15-9/19", "9/15-9/19", "Example from test files"),
        ("10/06-10/10", "10/06-10/10", "Example from test files"),
    ]
    
    passed = 0
    failed = 0
    
    for input_str, expected, description in test_cases:
        result = format_week_dates(input_str)
        if result == expected:
            print(f"  ✓ {description}: '{input_str}' → '{result}'")
            passed += 1
        else:
            print(f"  ✗ {description}: '{input_str}' → '{result}' (expected '{expected}')")
            failed += 1
    
    print(f"\nReal-world examples: {passed} passed, {failed} failed\n")
    return failed == 0


def main():
    """Run all tests."""
    print("=" * 80)
    print("DATE FORMATTER UTILITY TESTS")
    print("=" * 80)
    print()
    
    all_passed = True
    
    all_passed &= test_format_week_dates()
    all_passed &= test_validate_week_format()
    all_passed &= test_parse_week_dates()
    all_passed &= test_edge_cases()
    all_passed &= test_real_world_examples()
    
    print("=" * 80)
    if all_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 80)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

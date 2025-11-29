"""
Regression test for _build_teacher_name with NULL/None values.

Tests the fix for None.strip() crash when database fields are NULL.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tools.batch_processor import BatchProcessor
from backend.llm_service import get_llm_service

print("="*80)
print("TEACHER NAME BUILDER REGRESSION TESTS")
print("="*80)

# Create processor instance
llm_service = get_llm_service()
processor = BatchProcessor(llm_service)

# Test 1: All fields populated (ideal case)
print("\n1. Testing with all structured fields populated...")
user = {
    "first_name": "Daniela",
    "last_name": "Silva"
}
slot = {
    "primary_teacher_first_name": "Sarah",
    "primary_teacher_last_name": "Lang"
}
result = processor._build_teacher_name(user, slot)
expected = "Sarah Lang / Daniela Silva"
status = "✓" if result == expected else "✗"
print(f"  {status} Result: '{result}' (expected '{expected}')")
assert result == expected, f"Expected '{expected}', got '{result}'"

# Test 2: NULL/None in structured fields (common after migration)
print("\n2. Testing with NULL/None in structured fields...")
user = {
    "first_name": None,  # NULL from database
    "last_name": None,
    "name": "Daniela Silva"  # Legacy field
}
slot = {
    "primary_teacher_first_name": None,  # NULL from database
    "primary_teacher_last_name": None,
    "primary_teacher_name": "Lang"  # Legacy field
}
result = processor._build_teacher_name(user, slot)
expected = "Lang / Daniela Silva"
status = "✓" if result == expected else "✗"
print(f"  {status} Result: '{result}' (expected '{expected}')")
assert result == expected, f"Expected '{expected}', got '{result}'"

# Test 3: Mixed - some NULL, some populated
print("\n3. Testing with mixed NULL and populated fields...")
user = {
    "first_name": "Daniela",
    "last_name": "Silva"
}
slot = {
    "primary_teacher_first_name": None,  # NULL
    "primary_teacher_last_name": None,
    "primary_teacher_name": "Lang"
}
result = processor._build_teacher_name(user, slot)
expected = "Lang / Daniela Silva"
status = "✓" if result == expected else "✗"
print(f"  {status} Result: '{result}' (expected '{expected}')")
assert result == expected, f"Expected '{expected}', got '{result}'"

# Test 4: Only first name populated (partial data)
print("\n4. Testing with only first names...")
user = {
    "first_name": "Daniela",
    "last_name": None
}
slot = {
    "primary_teacher_first_name": "Sarah",
    "primary_teacher_last_name": None
}
result = processor._build_teacher_name(user, slot)
expected = "Sarah / Daniela"
status = "✓" if result == expected else "✗"
print(f"  {status} Result: '{result}' (expected '{expected}')")
assert result == expected, f"Expected '{expected}', got '{result}'"

# Test 5: Only last name populated (partial data)
print("\n5. Testing with only last names...")
user = {
    "first_name": None,
    "last_name": "Silva"
}
slot = {
    "primary_teacher_first_name": None,
    "primary_teacher_last_name": "Lang"
}
result = processor._build_teacher_name(user, slot)
expected = "Lang / Silva"
status = "✓" if result == expected else "✗"
print(f"  {status} Result: '{result}' (expected '{expected}')")
assert result == expected, f"Expected '{expected}', got '{result}'"

# Test 6: All fields NULL/None (worst case)
print("\n6. Testing with all fields NULL/None...")
user = {
    "first_name": None,
    "last_name": None,
    "name": None
}
slot = {
    "primary_teacher_first_name": None,
    "primary_teacher_last_name": None,
    "primary_teacher_name": None
}
result = processor._build_teacher_name(user, slot)
expected = "Unknown"
status = "✓" if result == expected else "✗"
print(f"  {status} Result: '{result}' (expected '{expected}')")
assert result == expected, f"Expected '{expected}', got '{result}'"

# Test 7: Empty strings (different from NULL)
print("\n7. Testing with empty strings...")
user = {
    "first_name": "",
    "last_name": "",
    "name": "Daniela Silva"
}
slot = {
    "primary_teacher_first_name": "",
    "primary_teacher_last_name": "",
    "primary_teacher_name": "Lang"
}
result = processor._build_teacher_name(user, slot)
expected = "Lang / Daniela Silva"
status = "✓" if result == expected else "✗"
print(f"  {status} Result: '{result}' (expected '{expected}')")
assert result == expected, f"Expected '{expected}', got '{result}'"

# Test 8: Whitespace-only strings
print("\n8. Testing with whitespace-only strings...")
user = {
    "first_name": "   ",
    "last_name": "   ",
    "name": "Daniela Silva"
}
slot = {
    "primary_teacher_first_name": "  ",
    "primary_teacher_last_name": "  ",
    "primary_teacher_name": "Lang"
}
result = processor._build_teacher_name(user, slot)
expected = "Lang / Daniela Silva"
status = "✓" if result == expected else "✗"
print(f"  {status} Result: '{result}' (expected '{expected}')")
assert result == expected, f"Expected '{expected}', got '{result}'"

# Test 9: Real migrated data (only last name in slot)
print("\n9. Testing with real migrated data (only last name)...")
user = {
    "first_name": "Daniela",
    "last_name": "Silva",
    "name": "Daniela Silva"
}
slot = {
    "primary_teacher_first_name": None,
    "primary_teacher_last_name": "Lang",  # Migrated from single-word name
    "primary_teacher_name": "Lang"
}
result = processor._build_teacher_name(user, slot)
expected = "Lang / Daniela Silva"
status = "✓" if result == expected else "✗"
print(f"  {status} Result: '{result}' (expected '{expected}')")
assert result == expected, f"Expected '{expected}', got '{result}'"

# Test 10: Missing keys entirely (dict doesn't have the key)
print("\n10. Testing with missing dictionary keys...")
user = {}  # No keys at all
slot = {}  # No keys at all
result = processor._build_teacher_name(user, slot)
expected = "Unknown"
status = "✓" if result == expected else "✗"
print(f"  {status} Result: '{result}' (expected '{expected}')")
assert result == expected, f"Expected '{expected}', got '{result}'"

print("\n" + "="*80)
print("✅ ALL REGRESSION TESTS PASSED")
print("="*80)
print("\nThe None.strip() crash has been fixed!")
print("The function now safely handles:")
print("  - NULL/None values from database")
print("  - Empty strings")
print("  - Whitespace-only strings")
print("  - Missing dictionary keys")
print("  - Partial data (only first or only last name)")
print("  - Mixed scenarios")

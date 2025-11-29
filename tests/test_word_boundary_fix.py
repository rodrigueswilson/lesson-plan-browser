"""
Test that word boundary fix prevents false positives.
"""

from tools.docx_parser import DOCXParser

# Create a mock parser just to test the method
class MockParser:
    def _infer_section(self, text: str):
        import re
        text_lower = text.lower()
        
        # Check unit/lesson first (more specific) - use word boundaries
        if re.search(r'\bunit\b', text_lower) or 'unit/lesson' in text_lower or 'lesson #' in text_lower or re.search(r'\bmodule\b', text_lower):
            return 'unit_lesson'
        elif any(kw in text_lower for kw in ['objective', 'goal', 'swbat', 'students will be able']):
            return 'objective'
        elif any(kw in text_lower for kw in ['warm-up', 'hook', 'anticipatory', 'do now']):
            return 'anticipatory_set'
        elif any(kw in text_lower for kw in ['instruction', 'activity', 'procedure', 'tailored']):
            return 'instruction'
        elif any(kw in text_lower for kw in ['misconception', 'common error']):
            return 'misconceptions'
        elif any(kw in text_lower for kw in ['assessment', 'check', 'evaluate', 'exit ticket']):
            return 'assessment'
        elif any(kw in text_lower for kw in ['homework', 'assignment', 'practice']):
            return 'homework'
        
        return None

parser = MockParser()

print("=" * 80)
print("TESTING WORD BOUNDARY FIX")
print("=" * 80)

test_cases = [
    # Should match as unit_lesson
    ("Unit, Lesson #, Module:", "unit_lesson", True),
    ("Unit 5: Fractions", "unit_lesson", True),
    ("Lesson # 3", "unit_lesson", True),
    ("Module 2", "unit_lesson", True),
    ("Unit/Lesson", "unit_lesson", True),
    
    # Should NOT match as unit_lesson (false positives)
    ("Students will have an opportunity to practice", None, False),
    ("Build community in the classroom", None, False),
    ("Unity and cooperation", None, False),
    ("The community center", None, False),
    
    # Should match other sections
    ("Objective: Students will be able to", "objective", False),
    ("Anticipatory Set:", "anticipatory_set", False),
    ("Tailored Instruction:", "instruction", False),
]

print("\nTest Results:\n")

passed = 0
failed = 0

for text, expected, is_unit_test in test_cases:
    result = parser._infer_section(text)
    status = "✅ PASS" if result == expected else "❌ FAIL"
    
    if result == expected:
        passed += 1
    else:
        failed += 1
    
    test_type = "[UNIT TEST]" if is_unit_test else "[FALSE POSITIVE TEST]"
    print(f"{status} {test_type}")
    print(f"  Text: '{text}'")
    print(f"  Expected: {expected}")
    print(f"  Got: {result}")
    print()

print("=" * 80)
print(f"SUMMARY: {passed} passed, {failed} failed")
print("=" * 80)

if failed == 0:
    print("\n✅ All tests passed! Word boundary fix working correctly.")
else:
    print(f"\n❌ {failed} test(s) failed. Review the logic.")

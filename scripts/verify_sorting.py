"""
Script to verify that sort_slots correctly handles various chronological and numerical ordering scenarios.
"""
from backend.services.sorting_utils import sort_slots

def test_sorting():
    print("Running sort_slots verification tests...\n")
    
    # Test 1: Standard chronological order (HH:MM format)
    slots_1 = [
        {"slot_number": 2, "start_time": "12:30", "unit_lesson": "Math"},
        {"slot_number": 1, "start_time": "11:42", "unit_lesson": "Science"},
        {"slot_number": 3, "start_time": "13:15", "unit_lesson": "ELA"},
    ]
    sorted_1 = sort_slots(slots_1)
    print(f"Test 1 (Standard HH:MM): Expected [Science, Math, ELA]")
    print(f"  Result: {[s['unit_lesson'] for s in sorted_1]}")
    assert [s['unit_lesson'] for s in sorted_1] == ["Science", "Math", "ELA"]

    # Test 2: ISO format times
    slots_2 = [
        {"slot_number": 5, "start_time": "2023-10-27T14:00:00", "unit_lesson": "Social Studies"},
        {"slot_number": 4, "start_time": "2023-10-27T10:00:00", "unit_lesson": "Morning Meeting"},
    ]
    sorted_2 = sort_slots(slots_2)
    print(f"\nTest 2 (ISO Format): Expected [Morning Meeting, Social Studies]")
    print(f"  Result: {[s['unit_lesson'] for s in sorted_2]}")
    assert [s['unit_lesson'] for s in sorted_2] == ["Morning Meeting", "Social Studies"]

    # Test 3: Mismatched slot_number but correct start_time
    slots_3 = [
        {"slot_number": 1, "start_time": "12:00", "unit_lesson": "Lunch"},
        {"slot_number": 99, "start_time": "08:00", "unit_lesson": "Arrival"},
    ]
    sorted_3 = sort_slots(slots_3)
    print(f"\nTest 3 (Mismatched slot_number): Expected [Arrival, Lunch]")
    print(f"  Result: {[s['unit_lesson'] for s in sorted_3]}")
    assert [s['unit_lesson'] for s in sorted_3] == ["Arrival", "Lunch"]

    # Test 4: Missing start_time (fallback to slot_number)
    slots_4 = [
        {"slot_number": 2, "unit_lesson": "Second"},
        {"slot_number": 1, "unit_lesson": "First"},
    ]
    sorted_4 = sort_slots(slots_4)
    print(f"\nTest 4 (No start_time, fallback to slot_num): Expected [First, Second]")
    print(f"  Result: {[s['unit_lesson'] for s in sorted_4]}")
    assert [s['unit_lesson'] for s in sorted_4] == ["First", "Second"]

    # Test 5: Same start_time (tie-break by slot_number)
    slots_5 = [
        {"slot_number": 2, "start_time": "09:00", "unit_lesson": "Subject B"},
        {"slot_number": 1, "start_time": "09:00", "unit_lesson": "Subject A"},
    ]
    sorted_5 = sort_slots(slots_5)
    print(f"\nTest 5 (Tie-break by slot_num): Expected [Subject A, Subject B]")
    print(f"  Result: {[s['unit_lesson'] for s in sorted_5]}")
    assert [s['unit_lesson'] for s in sorted_5] == ["Subject A", "Subject B"]

    # Test 6: Dictionary input (handling as list of values)
    slots_6 = {
        "2": {"slot_number": 2, "start_time": "10:00", "unit_lesson": "Dict 2"},
        "1": {"slot_number": 1, "start_time": "09:00", "unit_lesson": "Dict 1"},
    }
    sorted_6 = sort_slots(slots_6)
    print(f"\nTest 6 (Dictionary input): Expected [Dict 1, Dict 2]")
    print(f"  Result: {[s['unit_lesson'] for s in sorted_6]}")
    assert [s['unit_lesson'] for s in sorted_6] == ["Dict 1", "Dict 2"]

    print("\nAll verification tests passed!")

if __name__ == "__main__":
    test_sorting()

"""
Test script for JSON merger functionality.
Tests merging multiple single-slot JSONs into a multi-slot structure.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.json_merger import merge_lesson_jsons, validate_merged_json, get_merge_summary
from tools.test_json_merger_samples import create_sample_slot


def test_json_merger():
    """Test the JSON merger with sample data."""
    print("=" * 60)
    print("Testing JSON Merger")
    print("=" * 60)

    # Create sample slots
    slot1 = create_sample_slot(1, 'ELA', 'Ms. Lang')
    slot2 = create_sample_slot(3, 'Science', 'Ms. Savoca')
    slot3 = create_sample_slot(5, 'Math', 'Mr. Davies')

    lessons = [slot1, slot2, slot3]

    print(f"\nInput: {len(lessons)} lesson slots")
    for lesson in lessons:
        print(f"  - Slot {lesson['slot_number']}: {lesson['subject']} ({lesson['lesson_json']['metadata']['teacher_name']})")

    # Merge
    print("\nMerging lessons...")
    merged = merge_lesson_jsons(lessons)

    # Validate
    print("\nValidating merged JSON...")
    is_valid, error_msg = validate_merged_json(merged)

    if is_valid:
        print("Validation: PASSED")
    else:
        print(f"Validation: FAILED - {error_msg}")
        return False

    # Print summary
    print("\n" + get_merge_summary(merged))

    # Verify structure
    print("\nVerifying structure...")
    for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
        slots = merged['days'][day]['slots']
        print(f"  {day.capitalize()}: {len(slots)} slots")
        for slot in slots:
            print(f"    - Slot {slot['slot_number']}: {slot['subject']} - {slot.get('unit_lesson', 'N/A')}")

    # Save to file for inspection
    output_file = Path(__file__).parent.parent / 'output' / 'test_merged.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    print(f"\nMerged JSON saved to: {output_file}")
    print("\nTest PASSED!")
    return True


if __name__ == '__main__':
    success = test_json_merger()
    sys.exit(0 if success else 1)

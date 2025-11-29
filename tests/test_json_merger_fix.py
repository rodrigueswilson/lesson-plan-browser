"""Test if json_merger preserves hyperlinks."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tools.json_merger import merge_lesson_jsons

# Create test lesson with hyperlinks
test_lessons = [
    {
        'slot_number': 1,
        'subject': 'ELA',
        'lesson_json': {
            'metadata': {'week_of': '10-20-10-24', 'grade': '2'},
            'days': {
                'monday': {'unit_lesson': 'Test'},
                'tuesday': {'unit_lesson': 'Test'},
                'wednesday': {'unit_lesson': 'Test'},
                'thursday': {'unit_lesson': 'Test'},
                'friday': {'unit_lesson': 'Test'}
            },
            '_hyperlinks': [
                {'text': 'Link 1', 'url': 'http://example.com/1'},
                {'text': 'Link 2', 'url': 'http://example.com/2'}
            ],
            '_media_schema_version': '2.0'
        }
    }
]

print("=" * 80)
print("TESTING JSON MERGER FIX")
print("=" * 80)

merged = merge_lesson_jsons(test_lessons)

print(f"\n📋 Input lesson had:")
print(f"   _hyperlinks: {len(test_lessons[0]['lesson_json']['_hyperlinks'])} links")
print(f"   _media_schema_version: {test_lessons[0]['lesson_json']['_media_schema_version']}")

print(f"\n📊 Merged JSON has:")
if '_hyperlinks' in merged:
    print(f"   ✅ _hyperlinks: {len(merged['_hyperlinks'])} links")
else:
    print(f"   ❌ _hyperlinks: MISSING!")

if '_media_schema_version' in merged:
    print(f"   ✅ _media_schema_version: {merged['_media_schema_version']}")
else:
    print(f"   ❌ _media_schema_version: MISSING!")

print("\n" + "=" * 80)

if '_hyperlinks' in merged and len(merged['_hyperlinks']) == 2:
    print("✅ JSON MERGER FIX IS WORKING!")
else:
    print("❌ JSON MERGER FIX IS NOT WORKING!")

print("=" * 80)

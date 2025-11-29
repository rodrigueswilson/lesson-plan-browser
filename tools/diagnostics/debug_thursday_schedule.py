#!/usr/bin/env python3
"""Debug script to understand Thursday schedule and slot matching."""

from backend.database import SQLiteDatabase
import json

db = SQLiteDatabase()
user = db.get_user_by_name('Wilson Rodrigues')

print("=" * 80)
print("THURSDAY SCHEDULE ENTRIES")
print("=" * 80)
entries = [e for e in db.get_schedule_entries(user.id) if e.day_of_week == 'thursday']
entries.sort(key=lambda e: (e.slot_number, e.start_time or ''))

for e in entries:
    active_str = "ACTIVE" if e.is_active else "inactive"
    print(f"slot {e.slot_number}: {e.subject:20s} {e.start_time}-{e.end_time} [{active_str}]")

print("\n" + "=" * 80)
print("THURSDAY LESSON PLAN SLOTS")
print("=" * 80)

plans = db.get_user_plans(user.id, limit=1)
if plans and plans[0].lesson_json:
    lesson_json = plans[0].lesson_json
    thursday_data = lesson_json.get('days', {}).get('thursday', {})
    slots = thursday_data.get('slots', [])
    
    print(f"Found {len(slots)} slots in lesson_json")
    for i, slot in enumerate(slots):
        print(f"\nSlot index {i}:")
        print(f"  slot_number: {slot.get('slot_number')}")
        print(f"  subject: {slot.get('subject')}")
        print(f"  unit_lesson: {slot.get('unit_lesson', '')[:60]}...")
        obj = slot.get('objective', {})
        sg = obj.get('student_goal', '')[:60]
        print(f"  student_goal: {sg}...")

print("\n" + "=" * 80)
print("NON-CLASS PERIODS IN SCHEDULE")
print("=" * 80)

non_class = ['PREP', 'PREP TIME', 'LUNCH', 'A.M. ROUTINE', 'AM ROUTINE', 'MORNING ROUTINE', 'DISMISSAL']
for e in entries:
    if e.subject.upper() in non_class:
        print(f"slot {e.slot_number}: {e.subject} (non-instructional)")

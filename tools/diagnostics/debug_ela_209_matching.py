#!/usr/bin/env python3
"""Debug ELA Grade 2 209 matching issue."""

from backend.database import SQLiteDatabase

db = SQLiteDatabase()
user = db.get_user_by_name('Wilson Rodrigues')

plans = db.get_user_plans(user.id, limit=1)
if not plans or not plans[0].lesson_json:
    print("No lesson plan found")
    exit(1)

lesson_json = plans[0].lesson_json
thursday = lesson_json.get('days', {}).get('thursday', {})

print("=" * 80)
print("THURSDAY LESSON PLAN SLOTS")
print("=" * 80)

slots = thursday.get('slots', [])
for i, slot in enumerate(slots):
    print(f"\nSlot {i}: slot_number={slot.get('slot_number')}, subject={slot.get('subject')}")
    print(f"  Goal: {slot.get('objective', {}).get('student_goal', '')[:60]}")

print("\n" + "=" * 80)
print("MATCHING LOGIC FOR ELA GRADE 2 209")
print("=" * 80)

print("\nSchedule Entry: ELA Grade 2 • 209 • 09:18 - 10:03")
print("\nCurrent matching order:")
print("1. Subject match (exact or compatible)")
print("   - Slot 0 (ELA): matches ELA ✓ <- WRONG: Returns this first!")
print("   - Slot 1 (ELA/SS): matches ELA ✓ <- CORRECT: Should prefer this!")
print("\nProblem: Both slots match, but findIndex returns slot 0 first")
print("\nSolution: Prefer compound subjects (ELA/SS) over simple (ELA)")
print("          when multiple matches exist")

print("\n" + "=" * 80)
print("CO-TEACHING PATTERN")
print("=" * 80)
print("\nSchedule for Grade 2 209:")
entries = db.get_user_schedule(user.id, day_of_week='thursday')
grade2_209 = [e for e in entries if e.is_active and e.grade == '2' and e.homeroom == '209']
grade2_209.sort(key=lambda e: e.slot_number)

for e in grade2_209:
    print(f"  slot#{e.slot_number} {e.start_time}-{e.end_time} {e.subject}")

print("\nBoth ELA and Social S. should map to slot 1 (ELA/SS)")

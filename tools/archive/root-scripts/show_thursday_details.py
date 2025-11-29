#!/usr/bin/env python3
"""Show Thursday lesson plan and schedule details."""

from backend.database import SQLiteDatabase
import json

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
    print(f"\nSlot {i}:")
    print(f"  slot_number: {slot.get('slot_number')}")
    print(f"  subject: {slot.get('subject')}")
    print(f"  grade: {slot.get('grade')}")
    print(f"  homeroom: {slot.get('homeroom')}")
    print(f"  time: {slot.get('start_time')}-{slot.get('end_time')}")
    print(f"  unit_lesson: {slot.get('unit_lesson', '')[:60]}")
    obj = slot.get('objective', {})
    print(f"  student_goal: {obj.get('student_goal', '')[:80]}")

print("\n" + "=" * 80)
print("THURSDAY SCHEDULE (unique entries)")
print("=" * 80)

entries = db.get_user_schedule(user.id, day_of_week='thursday')
active = [e for e in entries if e.is_active]

# Dedupe by slot_number + subject + grade + homeroom + time
seen = set()
unique = []
for e in sorted(active, key=lambda x: (x.slot_number, x.start_time or '')):
    key = (e.slot_number, e.subject, e.grade, e.homeroom, e.start_time, e.end_time)
    if key not in seen:
        seen.add(key)
        unique.append(e)

for e in unique:
    print(f"slot#{e.slot_number:2d} {e.start_time}-{e.end_time} | {e.subject:20s} | Grade {e.grade:5s} | {e.homeroom:6s}")

print("\n" + "=" * 80)
print("MATCHING PROBLEM")
print("=" * 80)
print("\nWhen browser shows: ELA Grade 3 • T5 • 08:30 - 09:15")
print("It should find slot with matching subject+grade+homeroom+time")

match = next((s for s in slots if 
    s.get('subject') == 'ELA' and
    s.get('grade') == '3' and
    s.get('homeroom') == 'T5' and
    s.get('start_time') == '08:30'), None)

if match:
    idx = slots.index(match)
    print(f"\nFound at index {idx}:")
    print(f"  Goal: {match.get('objective', {}).get('student_goal', '')[:80]}")
else:
    print("\nNOT FOUND - This is the problem!")
    print("\nLet me check what the browser might be matching instead...")
    
    # Check Grade 2, 209, ELA
    match2 = next((s for s in slots if 
        s.get('subject') == 'ELA' and
        s.get('grade') == '2' and
        s.get('homeroom') == '209'), None)
    
    if match2:
        idx = slots.index(match2)
        print(f"\nFound ELA Grade 2 209 at index {idx}:")
        print(f"  Time: {match2.get('start_time')}-{match2.get('end_time')}")
        print(f"  Goal: {match2.get('objective', {}).get('student_goal', '')[:80]}")

#!/usr/bin/env python3
"""Debug slot matching issue - correct metadata but wrong objectives."""

from backend.database import SQLiteDatabase
import json

db = SQLiteDatabase()
user = db.get_user_by_name('Wilson Rodrigues')

print("=" * 80)
print("THURSDAY SCHEDULE ENTRIES (sorted by time)")
print("=" * 80)
entries = [e for e in db.get_schedule_entries(user.id) if e.day_of_week == 'thursday']
entries.sort(key=lambda e: (e.start_time or '', e.slot_number))

for i, e in enumerate(entries):
    active = "ACTIVE" if e.is_active else "inactive"
    print(f"{i}: slot#{e.slot_number:2d} | {e.subject:25s} | Grade {e.grade:5s} | {e.homeroom:6s} | {e.start_time}-{e.end_time} [{active}]")

print("\n" + "=" * 80)
print("THURSDAY LESSON PLAN SLOTS")
print("=" * 80)

plans = db.get_user_plans(user.id, limit=1)
if plans and plans[0].lesson_json:
    lesson_json = plans[0].lesson_json
    thursday_data = lesson_json.get('days', {}).get('thursday', {})
    slots = thursday_data.get('slots', [])
    
    print(f"Found {len(slots)} slots in lesson_json\n")
    for i, slot in enumerate(slots):
        slot_num = slot.get('slot_number', 'N/A')
        subject = slot.get('subject', 'N/A')
        grade = slot.get('grade', 'N/A')
        homeroom = slot.get('homeroom', 'N/A')
        start = slot.get('start_time', 'N/A')
        end = slot.get('end_time', 'N/A')
        
        print(f"Slot array index {i}:")
        print(f"  slot_number: {slot_num}")
        print(f"  subject: {subject} | Grade {grade} | {homeroom} | {start}-{end}")
        
        obj = slot.get('objective', {})
        sg = obj.get('student_goal', 'N/A')
        print(f"  student_goal: {sg[:80]}")
        print()

print("=" * 80)
print("MATCHING ANALYSIS")
print("=" * 80)
print("\nSchedule entry: ELA Grade 3 • T5 • 08:30 - 09:15")
schedule_entry = next((e for e in entries if 
    e.subject == 'ELA' and 
    e.grade == '3' and 
    e.homeroom == 'T5' and
    e.start_time == '08:30'), None)

if schedule_entry:
    print(f"  Found in schedule: slot_number={schedule_entry.slot_number}")
    
    # Try to find matching lesson plan slot
    print("\n  Looking for matching lesson plan slot...")
    print(f"    By slot_number ({schedule_entry.slot_number}):")
    match_by_slot = next((s for s in slots if s.get('slot_number') == schedule_entry.slot_number), None)
    if match_by_slot:
        print(f"      Found: {match_by_slot.get('subject')} Grade {match_by_slot.get('grade')} {match_by_slot.get('homeroom')}")
        print(f"      Goal: {match_by_slot.get('objective', {}).get('student_goal', 'N/A')[:80]}")
    
    print(f"\n    By subject+grade+homeroom (ELA, 3, T5):")
    match_by_meta = next((s for s in slots if 
        s.get('subject') == 'ELA' and
        s.get('grade') == '3' and
        s.get('homeroom') == 'T5'), None)
    if match_by_meta:
        idx = slots.index(match_by_meta)
        print(f"      Found at index {idx}: {match_by_meta.get('subject')} Grade {match_by_meta.get('grade')} {match_by_meta.get('homeroom')}")
        print(f"      Goal: {match_by_meta.get('objective', {}).get('student_goal', 'N/A')[:80]}")
    
    print(f"\n    By time (08:30-09:15):")
    match_by_time = next((s for s in slots if 
        s.get('start_time') == '08:30' and
        s.get('end_time') == '09:15'), None)
    if match_by_time:
        idx = slots.index(match_by_time)
        print(f"      Found at index {idx}: {match_by_time.get('subject')} Grade {match_by_time.get('grade')} {match_by_time.get('homeroom')}")
        print(f"      Goal: {match_by_time.get('objective', {}).get('student_goal', 'N/A')[:80]}")

print("\n" + "=" * 80)
print("CO-TEACHING PATTERN CHECK")
print("=" * 80)
print("Looking for ELA and Social S./EL/ss sharing lesson plan...")

ela_entries = [e for e in entries if 'ELA' in e.subject.upper() and e.grade == '2' and e.homeroom == '209']
ss_entries = [e for e in entries if 'SOCIAL' in e.subject.upper() and e.grade == '2' and e.homeroom == '209']

print(f"\nFound {len(ela_entries)} ELA Grade 2 209 entries:")
for e in ela_entries:
    print(f"  slot#{e.slot_number} {e.subject} {e.start_time}-{e.end_time}")

print(f"\nFound {len(ss_entries)} Social S. Grade 2 209 entries:")
for e in ss_entries:
    print(f"  slot#{e.slot_number} {e.subject} {e.start_time}-{e.end_time}")

# Check lesson plan slots
ela_slots = [s for s in slots if 'ELA' in str(s.get('subject', '')).upper() and s.get('grade') == '2' and s.get('homeroom') == '209']
ss_slots = [s for s in slots if 'SOCIAL' in str(s.get('subject', '')).upper() and s.get('grade') == '2' and s.get('homeroom') == '209']

print(f"\nFound {len(ela_slots)} ELA Grade 2 209 slots in lesson plan:")
for s in ela_slots:
    idx = slots.index(s)
    print(f"  index {idx}: slot#{s.get('slot_number')} {s.get('subject')} {s.get('start_time')}-{s.get('end_time')}")
    print(f"    Goal: {s.get('objective', {}).get('student_goal', 'N/A')[:80]}")

print(f"\nFound {len(ss_slots)} Social S. Grade 2 209 slots in lesson plan:")
for s in ss_slots:
    idx = slots.index(s)
    print(f"  index {idx}: slot#{s.get('slot_number')} {s.get('subject')} {s.get('start_time')}-{s.get('end_time')}")
    print(f"    Goal: {s.get('objective', {}).get('student_goal', 'N/A')[:80]}")

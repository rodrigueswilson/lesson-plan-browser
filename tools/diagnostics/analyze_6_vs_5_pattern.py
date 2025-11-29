#!/usr/bin/env python3
"""Analyze the 6 schedule periods vs 5 lesson plan slots pattern."""

from backend.database import SQLiteDatabase

db = SQLiteDatabase()
user = db.get_user_by_name('Wilson Rodrigues')

# Non-instructional periods
NON_CLASS = ['PREP', 'PREP TIME', 'LUNCH', 'A.M. ROUTINE', 'AM ROUTINE', 'MORNING ROUTINE', 'DISMISSAL']

print("=" * 80)
print("ANALYZING 6 vs 5 PATTERN FOR EACH DAY")
print("=" * 80)

days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']

plans = db.get_user_plans(user.id, limit=1)
if plans and plans[0].lesson_json:
    lesson_json = plans[0].lesson_json
    
    for day in days:
        print(f"\n{'='*80}")
        print(f"{day.upper()}")
        print(f"{'='*80}")
        
        # Get schedule entries for this day
        entries = [e for e in db.get_schedule_entries(user.id) 
                   if e.day_of_week == day and e.is_active]
        entries.sort(key=lambda e: (e.start_time or '', e.slot_number))
        
        # Get lesson plan slots for this day
        day_data = lesson_json.get('days', {}).get(day, {})
        plan_slots = day_data.get('slots', [])
        
        print(f"\nSchedule entries: {len(entries)}")
        print(f"Lesson plan slots: {len(plan_slots)}")
        print(f"Difference: {len(entries) - len(plan_slots)}")
        
        print(f"\n{'-'*80}")
        print("SCHEDULE ENTRIES:")
        print(f"{'-'*80}")
        
        instructional_count = 0
        non_instructional = []
        
        for i, e in enumerate(entries):
            is_non_class = e.subject.upper() in NON_CLASS
            marker = "[NON-INSTRUCTIONAL]" if is_non_class else ""
            print(f"{i+1}. slot#{e.slot_number:2d} | {e.start_time}-{e.end_time} | {e.subject:25s} | Grade {e.grade:5s} | {e.homeroom:6s} {marker}")
            
            if is_non_class:
                non_instructional.append(e.subject)
            else:
                instructional_count += 1
        
        print(f"\nInstructional periods: {instructional_count}")
        print(f"Non-instructional: {len(non_instructional)} - {', '.join(non_instructional)}")
        
        print(f"\n{'-'*80}")
        print("LESSON PLAN SLOTS:")
        print(f"{'-'*80}")
        
        for i, slot in enumerate(plan_slots):
            subject = slot.get('subject', 'N/A')
            grade = slot.get('grade', 'N/A')
            homeroom = slot.get('homeroom', 'N/A')
            start = slot.get('start_time', 'N/A')
            end = slot.get('end_time', 'N/A')
            slot_num = slot.get('slot_number', 'N/A')
            
            print(f"{i+1}. slot#{slot_num:2d} | {start}-{end} | {subject:25s} | Grade {grade:5s} | {homeroom:6s}")
        
        if instructional_count != len(plan_slots):
            print(f"\n*** MISMATCH: {instructional_count} instructional periods but {len(plan_slots)} lesson slots ***")

print("\n" + "=" * 80)
print("RECOMMENDATION")
print("=" * 80)
print("\nThe browser should:")
print("1. Filter out non-instructional schedule entries before matching")
print("2. Match the remaining instructional entries to lesson plan slots")
print("3. Use subject + grade + homeroom for matching (not slot_number)")

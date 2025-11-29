#!/usr/bin/env python3
"""Find co-teaching patterns where multiple subjects share one lesson plan."""

from backend.database import SQLiteDatabase

db = SQLiteDatabase()
user = db.get_user_by_name('Wilson Rodrigues')

print("=" * 80)
print("FINDING CO-TEACHING PATTERNS")
print("=" * 80)

days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']

plans = db.get_user_plans(user.id, limit=1)
if not plans or not plans[0].lesson_json:
    print("No lesson plan found")
    exit(1)

lesson_json = plans[0].lesson_json

for day in days:
    print(f"\n{'='*80}")
    print(f"{day.upper()}")
    print(f"{'='*80}")
    
    # Get active schedule entries
    all_entries = db.get_user_schedule(user.id, day_of_week=day)
    active_entries = [e for e in all_entries if e.is_active]
    entries = sorted(active_entries, key=lambda e: (e.start_time or '', e.slot_number))
    
    # Get lesson plan slots
    day_data = lesson_json.get('days', {}).get(day, {})
    plan_slots = day_data.get('slots', [])
    
    print(f"\nSchedule: {len(entries)} periods | Lesson Plan: {len(plan_slots)} slots")
    
    # Group by grade + homeroom
    from collections import defaultdict
    groups = defaultdict(list)
    
    for e in entries:
        if e.subject.upper() not in ['PREP', 'PREP TIME', 'LUNCH', 'A.M. ROUTINE', 'AM ROUTINE']:
            key = f"{e.grade}-{e.homeroom}"
            groups[key].append(e)
    
    print("\nGrouped by Grade-Homeroom:")
    for key, group_entries in sorted(groups.items()):
        if len(group_entries) > 1:
            print(f"\n  {key}: {len(group_entries)} periods")
            for e in group_entries:
                print(f"    slot#{e.slot_number} {e.start_time}-{e.end_time} {e.subject}")
            
            # Check if lesson plan has matching slot
            grade, homeroom = key.split('-')
            matching_slots = [s for s in plan_slots if s.get('grade') == grade and s.get('homeroom') == homeroom]
            print(f"    Lesson plan has {len(matching_slots)} slot(s) for this grade-homeroom")
            
            if matching_slots:
                for s in matching_slots:
                    idx = plan_slots.index(s)
                    print(f"      index {idx}: slot#{s.get('slot_number')} {s.get('subject')}")

print("\n" + "=" * 80)
print("CO-TEACHING DETECTION NEEDED")
print("=" * 80)
print("\nThe frontend needs to:")
print("1. Allow multiple schedule entries to map to the same lesson plan slot")
print("2. Match by grade+homeroom when subjects are related (ELA, Social S./EL/ss)")
print("3. Not use 'usedIndices' to block reuse for co-teaching scenarios")

"""
Inspect lesson JSON to see why enrichment isn't setting day-specific times.
"""
import json
import sqlite3
from pathlib import Path

DB_PATH = Path("d:/LP/data/lesson_planner.db")

def inspect_lesson():
    db = sqlite3.connect(str(DB_PATH))
    cursor = db.cursor()
    
    # Get latest plan
    cursor.execute("""
        SELECT lesson_json, user_id
        FROM weekly_plans
        ORDER BY generated_at DESC
        LIMIT 1
    """)
    row = cursor.fetchone()
    if not row:
        print("No plans found")
        return
    
    lesson_json, user_id = row
    lesson_json = json.loads(lesson_json)
    
    print("Lesson JSON Slot Structure:")
    print("=" * 80)
    
    days = lesson_json.get("days", {})
    for day_name in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
        if day_name not in days:
            continue
        
        day_data = days[day_name]
        slots = day_data.get("slots", [])
        
        print(f"\n{day_name.capitalize()}:")
        for slot in slots:
            slot_num = slot.get("slot_number")
            subject = slot.get("subject", "")
            grade = slot.get("grade", "")
            homeroom = slot.get("homeroom", "")
            start_time = slot.get("start_time", "")
            
            print(f"  Slot {slot_num}: {subject} | Grade: {grade} | Homeroom: {homeroom} | Time: {start_time}")
    
    # Check metadata
    print("\n" + "=" * 80)
    print("Lesson JSON Metadata:")
    print("=" * 80)
    metadata = lesson_json.get("metadata", {})
    print(f"Subject: {metadata.get('subject')}")
    print(f"Grade: {metadata.get('grade')}")
    print(f"Homeroom: {metadata.get('homeroom')}")
    print(f"Start Time: {metadata.get('start_time')}")
    
    # Check schedule entries for this user
    print("\n" + "=" * 80)
    print("Schedule Entries for User (for matching comparison):")
    print("=" * 80)
    
    cursor.execute("""
        SELECT day_of_week, slot_number, start_time, subject, grade, homeroom
        FROM schedules
        WHERE user_id = ? AND is_active = 1
        ORDER BY day_of_week, start_time
    """, (user_id,))
    
    schedule_by_day = {}
    for entry in cursor.fetchall():
        day, slot_num, start, subject, grade, homeroom = entry
        if day not in schedule_by_day:
            schedule_by_day[day] = []
        schedule_by_day[day].append({
            'slot_number': slot_num,
            'start_time': start,
            'subject': subject,
            'grade': grade or '(None)',
            'homeroom': homeroom or '(None)'
        })
    
    for day in ['monday', 'wednesday', 'friday']:  # Just show a few days
        if day not in schedule_by_day:
            continue
        print(f"\n{day.capitalize()} Schedule:")
        for entry in schedule_by_day[day]:
            print(f"  {entry['start_time']:5s} | Slot {entry['slot_number']:2d} | {entry['subject']:15s} | Grade {entry['grade']:6s} | {entry['homeroom']}")
    
    db.close()

if __name__ == "__main__":
    inspect_lesson()

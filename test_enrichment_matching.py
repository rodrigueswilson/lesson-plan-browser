"""
Test to see why enrichment isn't matching correctly.
Simulates what happens when enrichment runs.
"""
import json
import sqlite3
from pathlib import Path
from backend.api import enrich_lesson_json_with_times

DB_PATH = Path("d:/LP/data/lesson_planner.db")

def test_enrichment():
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
    
    lesson_json_str, user_id = row
    lesson_json = json.loads(lesson_json_str)
    
    print("BEFORE Enrichment:")
    print("=" * 80)
    days = lesson_json.get("days", {})
    for day_name in ['monday', 'wednesday']:
        if day_name not in days:
            continue
        slots = days[day_name].get("slots", [])
        print(f"\n{day_name.capitalize()}:")
        for slot in slots:
            print(f"  Slot {slot.get('slot_number')}: {slot.get('subject')} | Grade: {slot.get('grade')} | Homeroom: {slot.get('homeroom')} | Time: {slot.get('start_time')}")
    
    # Run enrichment
    print("\n" + "=" * 80)
    print("Running enrichment...")
    print("=" * 80)
    enrich_lesson_json_with_times(lesson_json, user_id)
    
    print("\nAFTER Enrichment:")
    print("=" * 80)
    for day_name in ['monday', 'wednesday']:
        if day_name not in days:
            continue
        slots = days[day_name].get("slots", [])
        print(f"\n{day_name.capitalize()}:")
        for slot in slots:
            print(f"  Slot {slot.get('slot_number')}: {slot.get('subject')} | Grade: {slot.get('grade')} | Homeroom: {slot.get('homeroom')} | Time: {slot.get('start_time')}")
    
    # Check what the correct times should be from schedule
    print("\n" + "=" * 80)
    print("Expected Times from Schedule:")
    print("=" * 80)
    cursor.execute("""
        SELECT day_of_week, start_time, subject, grade, homeroom
        FROM schedules
        WHERE user_id = ? AND is_active = 1
        ORDER BY day_of_week, start_time
    """, (user_id,))
    
    schedule_by_day = {}
    for entry in cursor.fetchall():
        day, start, subject, grade, homeroom = entry
        if day not in schedule_by_day:
            schedule_by_day[day] = []
        schedule_by_day[day].append({
            'start_time': start,
            'subject': subject,
            'grade': str(grade) if grade else None,
            'homeroom': homeroom or None
        })
    
    for day_name in ['monday', 'wednesday']:
        if day_name not in schedule_by_day:
            continue
        print(f"\n{day_name.capitalize()} Schedule:")
        for entry in schedule_by_day[day_name]:
            print(f"  {entry['start_time']:5s} | {entry['subject']:15s} | Grade: {entry['grade'] or '(None)':6s} | {entry['homeroom'] or '(None)'}")
    
    db.close()

if __name__ == "__main__":
    test_enrichment()

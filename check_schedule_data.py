"""
Check schedule entries in database to see if they have day-specific times.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path("d:/LP/data/lesson_planner.db")

def check_schedule():
    db = sqlite3.connect(str(DB_PATH))
    cursor = db.cursor()
    
    # Get all active schedule entries
    cursor.execute("""
        SELECT day_of_week, slot_number, start_time, end_time, subject, grade, homeroom
        FROM schedules
        WHERE is_active = 1
        ORDER BY day_of_week, start_time, slot_number
    """)
    
    entries = cursor.fetchall()
    
    # Group by day
    by_day = {}
    for entry in entries:
        day, slot_num, start, end, subject, grade, homeroom = entry
        if day not in by_day:
            by_day[day] = []
        by_day[day].append({
            'slot_number': slot_num,
            'start_time': start,
            'end_time': end,
            'subject': subject,
            'grade': grade,
            'homeroom': homeroom
        })
    
    print("Schedule Entries by Day:")
    print("=" * 80)
    for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
        if day in by_day:
            print(f"\n{day.capitalize()}:")
            for entry in sorted(by_day[day], key=lambda e: (e['start_time'], e['slot_number'])):
                print(f"  Slot {entry['slot_number']:2d} | {entry['start_time']:5s} | {entry['subject']:10s} | Grade {entry['grade']} | {entry['homeroom']}")
    
    # Check if times vary by day for same slot numbers
    print("\n" + "=" * 80)
    print("Checking if same slot_number has different times across days:")
    print("=" * 80)
    
    slot_times = {}
    for day, entries in by_day.items():
        for entry in entries:
            slot_num = entry['slot_number']
            if slot_num not in slot_times:
                slot_times[slot_num] = {}
            slot_times[slot_num][day] = entry['start_time']
    
    for slot_num in sorted(slot_times.keys()):
        times = slot_times[slot_num]
        unique_times = set(times.values())
        if len(unique_times) > 1:
            print(f"Slot {slot_num}: DIFFERENT times by day: {dict(times)}")
        else:
            time_str = list(unique_times)[0] if unique_times else "(no time)"
            print(f"Slot {slot_num}: SAME time ({time_str}) for all days")
    
    db.close()

if __name__ == "__main__":
    check_schedule()

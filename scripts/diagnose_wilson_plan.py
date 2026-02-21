
import json
import sqlite3
from pathlib import Path

DB_PATH = "d:/LP/data/lesson_planner.db"
PLAN_ID = "plan_20251228152714"

def inspect_db_plan():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT lesson_json FROM weekly_plans WHERE id = ?", (PLAN_ID,))
    row = cursor.fetchone()
    if not row:
        print(f"Plan {PLAN_ID} not found.")
        return
        
    lesson_json_str = row["lesson_json"]
    try:
        data = json.loads(lesson_json_str)
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return
        
    days = data.get('days', {})
    monday = days.get('monday', {})
    slots = monday.get('slots', [])
    
    print(f"Plan ID: {PLAN_ID}")
    print(f"Metadata: {data.get('metadata', {})}")
    print(f"\nMonday Slots ({len(slots)}):")
    
    # Sort slots so we see them in the order they are in the JSON
    for i, slot in enumerate(slots):
        print(f"Slot {i+1}:")
        print(f"  Slot Number: {slot.get('slot_number')}")
        print(f"  Subject: {slot.get('subject')}")
        print(f"  Start Time: {slot.get('start_time')}")
        print(f"  End Time: {slot.get('end_time')}")
        print(f"  Teacher: {slot.get('teacher_name')}")
        print(f"  Grade: {slot.get('grade')}")
        print(f"  Homeroom: {slot.get('homeroom')}")
        print(f"  Unit/Lesson: {slot.get('unit_lesson', '')[:50]}...")
    
    conn.close()

if __name__ == "__main__":
    inspect_db_plan()

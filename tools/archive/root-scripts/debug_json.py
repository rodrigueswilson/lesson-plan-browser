
import sqlite3
import json
from pathlib import Path

db_path = Path(r"d:\LP\data\lesson_planner.db")

def diagnostic():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print(f"\n===== Checking lesson_json for DUPLICATES in DB: {db_path} =====")
    cursor.execute("SELECT id, week_of, CAST(lesson_json AS TEXT) as lesson_json FROM weekly_plans ORDER BY id DESC LIMIT 1")
    plan = cursor.fetchone()
    
    if not plan:
        print("No plans found.")
        return

    print(f"Plan ID: {plan['id']} (Week of: {plan['week_of']})")
    data = json.loads(plan['lesson_json'])
    days = data.get("days", {})
    
    for day_name in ["monday", "tuesday"]:
        day_data = days.get(day_name, {})
        slots = day_data.get("slots", [])
        print(f"\n--- {day_name.upper()} ---")
        for slot in slots:
            slot_num = slot.get("slot_number")
            subject = slot.get("subject")
            print(f"Slot {slot_num}: {subject}")
            
    conn.close()

if __name__ == "__main__":
    diagnostic()

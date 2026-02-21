
import sqlite3
import json
from pathlib import Path

db_path = Path(r"d:\LP\data\lesson_planner.db")

def inspect_json():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT lesson_json FROM weekly_plans WHERE lesson_json IS NOT NULL ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    if row:
        lesson_json = json.loads(row['lesson_json'])
        if 'days' in lesson_json and 'monday' in lesson_json['days']:
            monday = lesson_json['days']['monday']
            if 'slots' in monday and isinstance(monday['slots'], list) and len(monday['slots']) > 0:
                print(f"--- Format of First Slot (from list) ---")
                print(json.dumps(monday['slots'][0], indent=2))
            elif 'slots' in monday and isinstance(monday['slots'], dict):
                 slot_key = list(monday['slots'].keys())[0]
                 print(f"--- Format of Slot {slot_key} (from dict) ---")
                 print(json.dumps(monday['slots'][slot_key], indent=2))
            
    conn.close()

if __name__ == "__main__":
    inspect_json()

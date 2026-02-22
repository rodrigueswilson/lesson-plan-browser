import sqlite3
import json
from pathlib import Path

def inspect_plan():
    db_path = r"d:\LP\data\lesson_planner.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    plan_id = "plan_20251228152714"
    cursor.execute("SELECT lesson_json FROM weekly_plans WHERE id = ?", (plan_id,))
    row = cursor.fetchone()
    
    if not row:
        print(f"Plan {plan_id} not found.")
        return

    lesson_json = json.loads(row[0])
    wednesday = lesson_json.get("days", {}).get("wednesday", {})
    
    print(f"\n--- [lesson_json] Wednesday for Plan {plan_id} ---")
    slots = wednesday.get("slots", [])
    for slot in slots:
        subj = str(slot.get("subject", "")).upper()
        if "SCIENCE" in subj:
            print(f"Slot {slot.get('slot_number')}: {slot.get('unit_lesson')} / {slot.get('subject')}")
            frames = slot.get("sentence_frames", [])
            for frame in frames:
                eng = frame.get("english", "")
                pt = frame.get("portuguese", "")
                ft = frame.get("frame_type", "")
                print(f"  [{ft}] ENG: '{eng}'")
                print(f"  [{ft}] PT:  '{pt}'")

    print(f"\n--- [lesson_steps] Wednesday for Plan {plan_id} ---")
    cursor.execute("""
        SELECT slot_number, step_name, sentence_frames 
        FROM lesson_steps 
        WHERE lesson_plan_id = ? AND lower(day_of_week) = 'wednesday'
        ORDER BY slot_number, step_number
    """, (plan_id,))
    rows = cursor.fetchall()
    for slot, name, frames_json in rows:
        # We know from above that Science is likely Slot 1 or similar for this user
        print(f"Slot {slot} | Step: {name}")
        if frames_json:
            frames = json.loads(frames_json)
            for frame in frames:
                eng = frame.get("english", "")
                pt = frame.get("portuguese", "")
                ft = frame.get("frame_type", "")
                print(f"  [{ft}] ENG: '{eng}'")
                print(f"  [{ft}] PT:  '{pt}'")

    conn.close()

if __name__ == "__main__":
    inspect_plan()

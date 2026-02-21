import sqlite3
import json

def check_endings():
    db_path = r"d:\LP\data\lesson_planner.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    plan_id = "plan_20251228152714"
    cursor.execute("SELECT lesson_json FROM weekly_plans WHERE id = ?", (plan_id,))
    row = cursor.fetchone()
    if row:
        lesson_json = json.loads(row[0])
        wednesday = lesson_json.get("days", {}).get("wednesday", {})
        slots = wednesday.get("slots", [])
        print(f"--- lesson_json (Plan {plan_id}, Wednesday) ---")
        for slot in slots:
            if "SCIENCE" in str(slot.get("subject", "")).upper():
                frames = slot.get("sentence_frames", [])
                for i, frame in enumerate(frames):
                    eng = frame.get("english", "")
                    pt = frame.get("portuguese", "")
                    print(f"Frame {i+1} ENG: '{eng[-1]}' | PT: '{pt[-1]}'")

    cursor.execute("""
        SELECT step_name, sentence_frames 
        FROM lesson_steps 
        WHERE lesson_plan_id = ? AND lower(day_of_week) = 'wednesday'
    """, (plan_id,))
    print(f"\n--- lesson_steps (Plan {plan_id}, Wednesday) ---")
    for name, frames_json in cursor.fetchall():
        if frames_json:
            print(f"Step: {name}")
            frames = json.loads(frames_json)
            for i, frame in enumerate(frames):
                eng = frame.get("english", "")
                pt = frame.get("portuguese", "")
                if eng and pt:
                    print(f"  Frame {i+1} ENG: '{eng[-1]}' | PT: '{pt[-1]}'")
    
    conn.close()

if __name__ == "__main__":
    check_endings()

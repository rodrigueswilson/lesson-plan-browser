import sqlite3
import json

def check_science_steps():
    db_path = r"d:\LP\data\lesson_planner.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    plan_id = "plan_20251228152714"
    cursor.execute("""
        SELECT step_name, sentence_frames 
        FROM lesson_steps 
        WHERE lesson_plan_id = ? AND lower(day_of_week) = 'wednesday' AND slot_number = 6
    """, (plan_id,))
    
    print(f"--- Science lesson_steps (Plan {plan_id}, Wednesday, Slot 6) ---")
    for name, frames_json in cursor.fetchall():
        print(f"\nStep: {name}")
        if frames_json:
            frames = json.loads(frames_json)
            for i, frame in enumerate(frames):
                eng = frame.get("english", "")
                pt = frame.get("portuguese", "")
                ft = frame.get("frame_type", "")
                print(f"  Frame {i+1} [{ft}]")
                print(f"    ENG: '{eng}'")
                print(f"    PT:  '{pt}'")
        else:
            print("  No sentence frames.")
    
    conn.close()

if __name__ == "__main__":
    check_science_steps()

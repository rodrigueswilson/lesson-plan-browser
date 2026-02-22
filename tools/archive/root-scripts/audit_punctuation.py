import sqlite3
import json

def audit_punctuation():
    db_path = r"d:\LP\data\lesson_planner.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("--- Auditing SQLite weekly_plans ---")
    cursor.execute("SELECT id, user_id, week_of, lesson_json FROM weekly_plans")
    plans = cursor.fetchall()
    
    total_plans = len(plans)
    unnormalized_plans = 0
    
    for plan_id, user_id, week_of, lesson_json_str in plans:
        if not lesson_json_str:
            continue
        try:
            lesson_json = json.loads(lesson_json_str)
        except:
            continue
            
        is_fixed = True
        days = lesson_json.get("days", {})
        for day_name, day_data in days.items():
            # Check slots
            slots = day_data.get("slots", [])
            for slot in slots:
                frames = slot.get("sentence_frames", [])
                for frame in frames:
                    text_eng = frame.get("english", "")
                    text_pt = frame.get("portuguese", "")
                    ft = frame.get("frame_type", "")
                    
                    if ft in ["frame", "stem"]:
                        if text_eng and not text_eng.endswith("."):
                            is_fixed = False
                        if text_pt and not text_pt.endswith("."):
                            is_fixed = False
                    elif ft == "open_question":
                        if text_eng and not text_eng.endswith("?"):
                            is_fixed = False
                        if text_pt and not text_pt.endswith("?"):
                            is_fixed = False
            
            # Check legacy frames
            old_frames = day_data.get("sentence_frames", [])
            for frame in old_frames:
                text_eng = frame.get("english", "")
                text_pt = frame.get("portuguese", "")
                ft = frame.get("frame_type", "")
                if ft in ["frame", "stem"] and text_eng and not text_eng.endswith("."):
                    is_fixed = False
                if ft == "open_question" and text_eng and not text_eng.endswith("?"):
                    is_fixed = False

        if not is_fixed:
            print(f"Plan {plan_id} ({week_of}) - User {user_id} is NOT fully normalized.")
            unnormalized_plans += 1

    print(f"\nSummary: {unnormalized_plans}/{total_plans} plans are unnormalized.")

    print("\n--- Auditing SQLite lesson_steps ---")
    cursor.execute("SELECT id, lesson_plan_id, sentence_frames FROM lesson_steps WHERE sentence_frames IS NOT NULL")
    steps = cursor.fetchall()
    unnormalized_steps = 0
    for step_id, plan_id, frames_str in steps:
        try:
            frames = json.loads(frames_str)
        except:
            continue
        is_fixed = True
        for frame in frames:
            text_eng = frame.get("english", "")
            ft = frame.get("frame_type", "")
            if ft in ["frame", "stem"] and text_eng and not text_eng.endswith("."):
                is_fixed = False
            if ft == "open_question" and text_eng and not text_eng.endswith("?"):
                is_fixed = False
        if not is_fixed:
            unnormalized_steps += 1
    
    print(f"Summary: {unnormalized_steps}/{len(steps)} steps are unnormalized.")
    
    conn.close()

if __name__ == "__main__":
    audit_punctuation()

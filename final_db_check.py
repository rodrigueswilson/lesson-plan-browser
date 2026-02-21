import sqlite3
import json

def final_check():
    db_path = r"d:\LP\data\lesson_planner.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    plan_id = "plan_20251228152714"
    cursor.execute("""
        SELECT sentence_frames 
        FROM lesson_steps 
        WHERE lesson_plan_id = ? AND lower(day_of_week) = 'wednesday' AND slot_number = 6 AND step_name LIKE 'Sentence Frames%'
    """, (plan_id,))
    
    row = cursor.fetchone()
    if row and row[0]:
        frames = json.loads(row[0])
        print(f"Checking {len(frames)} frames for Science (Wed, Slot 6):")
        all_ok = True
        for i, frame in enumerate(frames):
            eng = frame.get("english", "")
            pt = frame.get("portuguese", "")
            ft = frame.get("frame_type", "")
            
            if ft in ["frame", "stem"]:
                if not eng.endswith(".") or not pt.endswith("."):
                    print(f"!!! Error in Frame {i+1} [frame]: ENG ends with '{eng[-1]}', PT ends with '{pt[-1]}'")
                    all_ok = False
                else:
                    print(f"Frame {i+1} [frame]: OK")
            elif ft == "open_question":
                if not eng.endswith("?") or not pt.endswith("?"):
                    print(f"!!! Error in Frame {i+1} [open_question]: ENG ends with '{eng[-1]}', PT ends with '{pt[-1]}'")
                    all_ok = False
                else:
                    print(f"Frame {i+1} [open_question]: OK")
        
        if all_ok:
            print("\nALL FRAMES IN THIS STEP ARE CORRECTLY PUNCTUATED.")
    else:
        print("No Science frames found in lesson_steps.")
    
    conn.close()

if __name__ == "__main__":
    final_check()

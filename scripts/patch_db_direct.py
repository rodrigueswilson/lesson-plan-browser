import sqlite3
import json
from pathlib import Path

def patch_db_directly():
    db_path = Path("data/lesson_planner.db")
    if not db_path.exists():
        if Path("../data/lesson_planner.db").exists():
            db_path = Path("../data/lesson_planner.db")
            
    print(f"Patching database at {db_path}...")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    plan_id = '6dc1bd72-9481-44f4-9ee7-123c7dc2d1b0'
    
    # 1. Fetch current lesson_json
    cursor.execute("SELECT lesson_json FROM weekly_plans WHERE id = ?", (plan_id,))
    row = cursor.fetchone()
    
    if not row:
        print("Plan not found!")
        return
        
    lesson_json = json.loads(row['lesson_json'])
    
    # 2. Get Slot 2 Data
    monday_slots = lesson_json["days"]["monday"]["slots"]
    slot2_data = None
    for s in monday_slots:
        if s["slot_number"] == 2:
            slot2_data = s
            break
            
    if not slot2_data:
        print("Error: Could not find Slot 2 data.")
        return

    print("Found Slot 2 data.")
    vocab = slot2_data.get("vocabulary_cognates", [])
    frames = slot2_data.get("sentence_frames", [])
    
    # 3. Update Slot 1
    updated = False
    for s in monday_slots:
        if s["slot_number"] == 1:
            s["vocabulary_cognates"] = vocab
            s["sentence_frames"] = frames
            print(f"Copied {len(vocab)} vocab items and {len(frames)} frames to Slot 1.")
            updated = True
            break
            
    if not updated:
        print("Slot 1 not found in JSON.")
        return
        
    # 4. Save back to DB
    cursor.execute(
        "UPDATE weekly_plans SET lesson_json = ? WHERE id = ?", 
        (json.dumps(lesson_json), plan_id)
    )
    conn.commit()
    conn.close()
    print("Database updated successfully.")
    
    # 5. Regenerate steps via API
    import requests
    gen_url = "http://localhost:8000/api/lesson-steps/generate"
    gen_params = {
        "plan_id": plan_id,
        "day": "monday",
        "slot": 1
    }
    headers = {"X-Current-User-Id": "04fe8898-cb89-4a73-affb-64a97a98f820"}
    
    print("Regenerating steps via API...")
    try:
        gen_response = requests.post(gen_url, params=gen_params, headers=headers)
        if gen_response.status_code == 200:
            print("Steps regenerated successfully.")
        else:
            print(f"Step regeneration failed: {gen_response.status_code} - {gen_response.text}")
    except Exception as e:
        print(f"Regeneration request failed: {e}")

if __name__ == "__main__":
    patch_db_directly()


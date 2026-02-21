
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path("d:/LP/data/lesson_planner.db")
PLAN_ID = "plan_20251229174144"
USER_ID = "04fe8898-cb89-4a73-affb-64a97a98f820"

def enrich_diagnostic(lesson_json: Dict[str, Any], user_id: str) -> None:
    if not lesson_json or "days" not in lesson_json:
        print("No days in lesson_json")
        return

    # Mock DB interaction to simulate api.py logic
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT day_of_week, start_time, end_time, subject, slot_number FROM schedules WHERE user_id = ?", (user_id,))
    schedule = cursor.fetchall()
    
    # Map (day, slot_number, subject) -> (start_time, end_time)
    time_map = {}
    # Map (day, slot_number) -> list of (subject, start_time, end_time)
    slot_map = {}
    
    for entry in schedule:
        day = entry["day_of_week"].lower()
        slot_num = entry["slot_number"]
        subject = entry["subject"].lower()
        time_map[(day, slot_num, subject)] = (entry["start_time"], entry["end_time"])
        
        if (day, slot_num) not in slot_map:
            slot_map[(day, slot_num)] = []
        slot_map[(day, slot_num)].append((subject, entry["start_time"], entry["end_time"]))

    print(f"\nDiagnostic for User {user_id}")
    
    for day_name, day_data in lesson_json["days"].items():
        day_lower = day_name.lower()
        slots = day_data.get("slots", [])
        
        print(f"\n{day_name.upper()}:")
        
        def get_times_diagnostic(s_num, s_subj):
            print(f"  Checking Slot #{s_num} Subject '{s_subj}'")
            # 1. Try exact match (including subject)
            times = time_map.get((day_lower, s_num, s_subj.lower()))
            if times:
                print(f"    -> Exact match found: {times}")
                return times
            
            # 2. Try slot mismatch fallback (if unique for that slot number)
            candidates = slot_map.get((day_lower, s_num), [])
            print(f"    -> No exact match. Candidates for Slot #{s_num}: {candidates}")
            if len(candidates) == 1:
                print(f"    -> Fallback match found: {(candidates[0][1], candidates[0][2])}")
                return (candidates[0][1], candidates[0][2])
            
            print(f"    -> No match found (candidates count: {len(candidates)})")
            return None

        if isinstance(slots, list):
            for slot in slots:
                if not isinstance(slot, dict): continue
                slot_num = slot.get("slot_number")
                subject = slot.get("subject", "")
                if slot_num is not None:
                    get_times_diagnostic(slot_num, subject)

    conn.close()

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT lesson_json FROM weekly_plans WHERE id = ?", (PLAN_ID,))
    row = cursor.fetchone()
    lesson_json = json.loads(row["lesson_json"])
    conn.close()
    
    enrich_diagnostic(lesson_json, USER_ID)

if __name__ == "__main__":
    main()

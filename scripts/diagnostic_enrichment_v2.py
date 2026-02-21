
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path("d:/LP/data/lesson_planner.db")
PLAN_ID = "plan_20251229174144"
USER_ID = "04fe8898-cb89-4a73-affb-64a97a98f820"

def enrich_diagnostic(lesson_json: Dict[str, Any], user_id: str):
    output = []
    if not lesson_json or "days" not in lesson_json:
        return "No days in lesson_json"

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT day_of_week, start_time, end_time, subject, slot_number FROM schedules WHERE user_id = ?", (user_id,))
    schedule = cursor.fetchall()
    
    time_map = {}
    slot_map = {}
    
    for entry in schedule:
        day = entry["day_of_week"].lower()
        slot_num = entry["slot_number"]
        subject = entry["subject"].lower()
        time_map[(day, slot_num, subject)] = (entry["start_time"], entry["end_time"])
        
        if (day, slot_num) not in slot_map:
            slot_map[(day, slot_num)] = []
        slot_map[(day, slot_num)].append((subject, entry["start_time"], entry["end_time"]))

    output.append(f"Diagnostic for User {user_id}")
    
    for day_name, day_data in lesson_json["days"].items():
        day_lower = day_name.lower()
        slots = day_data.get("slots", [])
        
        output.append(f"\n{day_name.upper()}:")
        
        if isinstance(slots, list):
            for slot in slots:
                if not isinstance(slot, dict): continue
                slot_num = slot.get("slot_number")
                subject = slot.get("subject", "")
                
                output.append(f"  Checking Slot #{slot_num} Subject '{subject}'")
                
                # 1. Try exact match
                times = time_map.get((day_lower, slot_num, subject.lower()))
                if times:
                    output.append(f"    -> Exact match found: {times}")
                    continue
                
                # 2. Try fallback
                candidates = slot_map.get((day_lower, slot_num), [])
                output.append(f"    -> No exact match. Candidates for Slot #{slot_num}: {candidates}")
                if len(candidates) == 1:
                    output.append(f"    -> Fallback match found: {(candidates[0][1], candidates[0][2])}")
                else:
                    output.append(f"    -> No match found (candidates count: {len(candidates)})")

    conn.close()
    return "\n".join(output)

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT lesson_json FROM weekly_plans WHERE id = ?", (PLAN_ID,))
    row = cursor.fetchone()
    lesson_json = json.loads(row["lesson_json"])
    conn.close()
    
    result = enrich_diagnostic(lesson_json, USER_ID)
    with open("d:/LP/scripts/diagnostic_output.txt", "w") as f:
        f.write(result)
    print("Diagnostic output written to d:/LP/scripts/diagnostic_output.txt")

if __name__ == "__main__":
    main()

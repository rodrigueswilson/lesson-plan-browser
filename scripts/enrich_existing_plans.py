"""
One-time script to enrich existing weekly plans with schedule times.
This adds start_time and end_time to lesson_json slots in the database.
"""
import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, List

# Standard database path
DB_PATH = Path("d:/LP/data/lesson_planner.db")

def enrich_lesson_json_with_times(lesson_json: Dict[str, Any], schedule_entries: List[Dict[str, Any]]) -> bool:
    """Enrich lesson_json with start_time and end_time from schedule entries."""
    if not lesson_json or "days" not in lesson_json:
        return False

    # Map (day, slot_number, subject) -> (start_time, end_time)
    time_map = {}
    # Map (day, slot_number) -> list of (subject, start_time, end_time)
    slot_map = {}
    
    for entry in schedule_entries:
        day = entry["day_of_week"].lower()
        slot_num = entry["slot_number"]
        subject = entry["subject"].lower()
        time_map[(day, slot_num, subject)] = (entry["start_time"], entry["end_time"])
        
        if (day, slot_num) not in slot_map:
            slot_map[(day, slot_num)] = []
        slot_map[(day, slot_num)].append((subject, entry["start_time"], entry["end_time"]))

    modified = False
    for day_name, day_data in lesson_json["days"].items():
        day_lower = day_name.lower()
        slots = day_data.get("slots", [])
        
        def get_times(s_num, s_subj):
            # 1. Try exact match (including subject)
            times = time_map.get((day_lower, s_num, s_subj))
            if times:
                return times
            
            # 2. Try slot mismatch fallback (if unique for that slot number)
            candidates = slot_map.get((day_lower, s_num), [])
            if len(candidates) == 1:
                return (candidates[0][1], candidates[0][2])
            
            return None

        if isinstance(slots, list):
            for slot in slots:
                if not isinstance(slot, dict):
                    continue
                slot_num = slot.get("slot_number")
                subject = slot.get("subject", "").lower()
                if slot_num is not None:
                    times = get_times(slot_num, subject)
                    if times:
                        if slot.get("start_time") != times[0] or slot.get("end_time") != times[1]:
                            slot["start_time"] = times[0]
                            slot["end_time"] = times[1]
                            modified = True
        elif isinstance(slots, dict):
             for slot_num_str, slot in slots.items():
                if not isinstance(slot, dict):
                    continue
                try:
                    slot_num = int(slot_num_str)
                except ValueError:
                    continue
                subject = slot.get("subject", "").lower()
                times = get_times(slot_num, subject)
                if times:
                    if slot.get("start_time") != times[0] or slot.get("end_time") != times[1]:
                        slot["start_time"] = times[0]
                        slot["end_time"] = times[1]
                        modified = True
    return modified

def main():
    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("Fetching weekly plans...")
    cursor.execute("SELECT id, user_id, lesson_json FROM weekly_plans WHERE lesson_json IS NOT NULL")
    plans = cursor.fetchall()

    print(f"Found {len(plans)} plans to process.")
    updated_count = 0

    for plan in plans:
        plan_id = plan["id"]
        user_id = plan["user_id"]
        lesson_json_raw = plan["lesson_json"]

        try:
            lesson_json = json.loads(lesson_json_raw) if isinstance(lesson_json_raw, str) else lesson_json_raw
        except Exception:
            print(f"  Skipping plan {plan_id}: invalid JSON")
            continue

        # Fetch schedule for this user
        cursor.execute(
            "SELECT day_of_week, slot_number, subject, start_time, end_time FROM schedules WHERE user_id = ?",
            (user_id,)
        )
        schedule_rows = cursor.fetchall()
        schedule_entries = [dict(row) for row in schedule_rows]

        if not schedule_entries:
            print(f"  No schedule found for user {user_id} (plan {plan_id})")
            continue

        if enrich_lesson_json_with_times(lesson_json, schedule_entries):
            updated_json = json.dumps(lesson_json)
            cursor.execute(
                "UPDATE weekly_plans SET lesson_json = ? WHERE id = ?",
                (updated_json, plan_id)
            )
            updated_count += 1
            print(f"  Updated plan {plan_id}")

    conn.commit()
    conn.close()
    print(f"\nDone. Updated {updated_count} plans.")

if __name__ == "__main__":
    main()

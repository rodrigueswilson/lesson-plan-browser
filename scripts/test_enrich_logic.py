import json
import sqlite3

def test_enrich():
    user_id = '04fe8898-cb89-4a73-affb-64a97a98f820'
    plan_id = 'plan_20251214200745'
    
    conn = sqlite3.connect('d:/LP/data/lesson_planner.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT lesson_json FROM weekly_plans WHERE id = ?", (plan_id,))
    row = cursor.fetchone()
    lesson_json = json.loads(row[0])
    
    cursor.execute("SELECT day_of_week, slot_number, subject, start_time, end_time FROM schedules WHERE user_id = ?", (user_id,))
    schedule = [dict(r) for r in cursor.fetchall()]
    
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
        
    print("Enrichment Check for Monday:")
    for slot in lesson_json['days']['monday']['slots']:
        s_num = slot.get('slot_number')
        s_subj = slot.get('subject', '').lower()
        
        # 1. Exact match
        times = time_map.get(('monday', s_num, s_subj))
        match_type = "Exact" if times else "None"
        
        if not times:
            # 2. Fallback
            candidates = slot_map.get(('monday', s_num), [])
            if len(candidates) == 1:
                times = (candidates[0][1], candidates[0][2])
                match_type = "Fallback (Unique Slot)"
        
        print(f"  Slot {s_num} ({s_subj}): {times} [Match: {match_type}]")

if __name__ == "__main__":
    test_enrich()

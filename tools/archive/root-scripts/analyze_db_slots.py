import sqlite3
import json

def analyze_db():
    conn = sqlite3.connect('d:/LP/data/lesson_planner.db')
    cursor = conn.cursor()
    
    user_id = '04fe8898-cb89-4a73-affb-64a97a98f820'
    
    print(f"Analyzing slots for user: {user_id}")
    
    # 1. Check class_slots
    print("\n--- CLASS SLOTS ---")
    cursor.execute("SELECT id, slot_number, subject, grade, homeroom FROM class_slots WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    
    slot_map = {}
    for row in rows:
        id, slot_num, subj, grade, room = row
        print(f"ID: {id} | Slot: {slot_num} | Subj: {subj} | Grade: {grade} | Room: {room}")
        if slot_num in slot_map:
            slot_map[slot_num].append(subj)
        else:
            slot_map[slot_num] = [subj]
            
    # Check for collisions
    collisions = [s for s, subjs in slot_map.items() if len(subjs) > 1]
    if collisions:
        print(f"\nWARNING: Found slot number collisions: {collisions}")
    else:
        print("\nNo slot number collisions found in class_slots.")

    # 2. Check weekly_plans (latest_lesson.json)
    print("\n--- LATEST WEEKLY PLAN ---")
    cursor.execute("SELECT id, week_of, CAST(lesson_json AS TEXT) FROM weekly_plans WHERE user_id = ? ORDER BY generated_at DESC LIMIT 1", (user_id,))
    row = cursor.fetchone()
    if row:
        plan_id, week_of, lesson_json_str = row
        data = json.loads(lesson_json_str)
        total_slots = 0
        for day, ddata in data.get('days', {}).items():
            slots = ddata.get('slots', [])
            total_slots += len(slots)
            slot_nums = [s.get('slot_number') for s in slots]
            print(f"{day.capitalize()}: {len(slots)} slots. Numbers: {slot_nums}")
        print(f"\nTotal slots in JSON: {total_slots}")
    else:
        print("No weekly plan found.")

    conn.close()

if __name__ == '__main__':
    analyze_db()

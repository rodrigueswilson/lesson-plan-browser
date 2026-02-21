
import sqlite3
from pathlib import Path

db_path = Path(r"d:\LP\data\lesson_planner.db")

def check_consistency():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    uid = "04fe8898-cb89-4a73-affb-64a97a98f820"
    print(f"\n===== Consistency Check for User {uid} =====")
    
    print("\n--- CLASS_SLOTS (The Generation Index) ---")
    cursor.execute("SELECT slot_number, subject, homeroom FROM class_slots WHERE user_id=? ORDER BY slot_number", (uid,))
    for s in cursor.fetchall():
        print(f"Slot {s['slot_number']}: {s['subject']} ({s['homeroom']})")

    for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
        print(f"\n--- SCHEDULE: {day.upper()} ---")
        cursor.execute("SELECT slot_number, subject, start_time FROM schedules WHERE user_id=? AND day_of_week=? ORDER BY slot_number", (uid, day))
        for s in cursor.fetchall():
            print(f"Slot {s['slot_number']}: {s['subject']} ({s['start_time']})")
            
    conn.close()

if __name__ == "__main__":
    check_consistency()

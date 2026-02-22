
import sqlite3
from pathlib import Path

db_path = Path(r"d:\LP\data\lesson_planner.db")

def inspect_intra_user_dups():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print(f"\n===== Intra-User Duplicate IDs in SCHEDULES =====")
    cursor.execute("""
        SELECT user_id, day_of_week, slot_number, COUNT(*) as cnt 
        FROM schedules 
        GROUP BY user_id, day_of_week, slot_number 
        HAVING cnt > 1
    """)
    dups = cursor.fetchall()
    
    if not dups:
        print("No duplicates found within users.")
    else:
        for d in dups:
            uid = d['user_id']
            day = d['day_of_week']
            slot = d['slot_number']
            print(f"\n--- User {uid} {day} Slot {slot} ({d['cnt']} entries) ---")
            cursor.execute("SELECT id, subject, start_time FROM schedules WHERE user_id=? AND day_of_week=? AND slot_number=?", (uid, day, slot))
            rows = cursor.fetchall()
            for r in rows:
                print(dict(r))
            
    conn.close()

if __name__ == "__main__":
    inspect_intra_user_dups()

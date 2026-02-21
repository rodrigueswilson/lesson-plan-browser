
import sqlite3
from pathlib import Path

db_path = Path(r"d:\LP\data\lesson_planner.db")

def inspect_duplicates():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print(f"\n===== Duplicate IDs in SCHEDULES =====")
    cursor.execute("""
        SELECT day_of_week, slot_number, COUNT(*) as cnt 
        FROM schedules 
        GROUP BY day_of_week, slot_number 
        HAVING cnt > 1
        LIMIT 5
    """)
    dups = cursor.fetchall()
    
    for d in dups:
        day = d['day_of_week']
        slot = d['slot_number']
        print(f"\n--- {day} Slot {slot} ---")
        cursor.execute("SELECT id, subject, start_time, user_id FROM schedules WHERE day_of_week=? AND slot_number=?", (day, slot))
        rows = cursor.fetchall()
        for r in rows:
            print(dict(r))
            
    conn.close()

if __name__ == "__main__":
    inspect_duplicates()

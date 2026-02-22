
import sqlite3
from pathlib import Path

db_path = Path(r"d:\LP\data\lesson_planner.db")

def inspect_slots():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print(f"\n===== Inspecting CLASS_SLOTS =====")
    cursor.execute("SELECT * FROM class_slots")
    slots = cursor.fetchall()
    for s in slots:
        print(dict(s))
            
    conn.close()

if __name__ == "__main__":
    inspect_slots()

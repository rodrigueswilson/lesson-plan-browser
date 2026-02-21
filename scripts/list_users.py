import sqlite3
from pathlib import Path

def main():
    db_path = Path("d:/LP/data/lesson_planner.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, email FROM users")
    rows = cursor.fetchall()
    
    print(f"Users in {db_path}:")
    for r in rows:
        print(f" - {r[0]} | {r[1]} | {r[2]}")
        
    conn.close()

if __name__ == "__main__":
    main()

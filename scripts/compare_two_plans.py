import sqlite3
import json
from pathlib import Path

def main():
    db_path = Path("d:/LP/data/lesson_planner.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    ids = ["plan_20251227172034", "plan_20251228152714"]
    
    print(f"Comparing plans in {db_path}...")
    
    for pid in ids:
        cursor.execute("SELECT id, user_id, week_of, generated_at, lesson_json FROM weekly_plans WHERE id=?", (pid,))
        row = cursor.fetchone()
        
        if not row:
            print(f"\nPlan {pid} NOT FOUND locally.")
            continue
            
        print(f"\nPLAN: {row['id']}")
        print(f"User ID: {row['user_id']}")
        print(f"Week: {row['week_of']}")
        print(f"Generated: {row['generated_at']}")
        
        data = json.loads(row['lesson_json'])
        thursday = data.get('days', {}).get('thursday', {})
        print(f"Thursday Unit: {thursday.get('unit_lesson', 'N/A')}")
        
    conn.close()

if __name__ == "__main__":
    main()

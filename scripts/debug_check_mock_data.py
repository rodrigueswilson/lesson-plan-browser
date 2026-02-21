import sqlite3
import json
from pathlib import Path

def main():
    db_path = Path("d:/LP/data/lesson_planner.db")
    if not db_path.exists():
        print(f"DB not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Checking {db_path} for 'TBD' in lesson_steps...")
    
    try:
        # Check weekly_plans
        cursor.execute("SELECT COUNT(*) FROM weekly_plans WHERE lesson_json LIKE '%TBD%'")
        tbd_plans = cursor.fetchone()[0]
        print(f"Plans with TBD: {tbd_plans}")
        
        # Check lesson_steps
        cursor.execute("SELECT COUNT(*) FROM lesson_steps WHERE display_content LIKE '%TBD%' OR hidden_content LIKE '%TBD%'")
        tbd_steps = cursor.fetchone()[0]
        print(f"Steps with TBD: {tbd_steps}")
        
        if tbd_steps > 0:
            cursor.execute("SELECT id, lesson_plan_id, display_content FROM lesson_steps WHERE display_content LIKE '%TBD%' OR hidden_content LIKE '%TBD%' LIMIT 5")
            rows = cursor.fetchall()
            print("\nSample TBD steps:")
            for row in rows:
                print(f"Step {row[0]} (Plan {row[1]}): {row[2][:50]}...")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()

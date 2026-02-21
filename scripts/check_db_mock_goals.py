import sqlite3
from pathlib import Path

def main():
    db_path = Path("d:/LP/data/lesson_planner.db")
    if not db_path.exists():
        print(f"DB not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Checking {db_path} for 'Mock Student Goal' in lesson_json...")
    
    try:
        # Check weekly_plans
        cursor.execute("SELECT id, lesson_json FROM weekly_plans WHERE lesson_json LIKE '%Mock Student Goal%'")
        rows = cursor.fetchall()
        print(f"Plans with 'Mock Student Goal': {len(rows)}")
        for r in rows:
            print(f" - Plan ID: {r[0]}")
            
        # Check lesson_steps
        cursor.execute("SELECT COUNT(*) FROM lesson_steps WHERE display_content LIKE '%Mock Student Goal%'")
        steps_count = cursor.fetchone()[0]
        print(f"Steps with 'Mock Student Goal': {steps_count}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()

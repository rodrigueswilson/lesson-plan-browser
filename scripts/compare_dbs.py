import sqlite3
import json
from pathlib import Path

def check_db(name, db_path):
    print(f"Checking {name} ({db_path})")
    if not Path(db_path).exists():
        print("  [ERROR] File not found")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Try to detect columns
    try:
        cursor.execute("PRAGMA table_info(weekly_plans)")
        columns = [r['name'] for r in cursor.fetchall()]
        time_col = 'generated_at' if 'generated_at' in columns else 'created_at' if 'created_at' in columns else None
    except Exception:
        time_col = None

    if not time_col:
        print("  [WARN] Could not determine time column (neither generated_at nor created_at)")
        query = "SELECT id, week_of, lesson_json FROM weekly_plans WHERE lesson_json LIKE '%Math%' AND lesson_json LIKE '%Grade 2%' AND lesson_json LIKE '%209%'"
    else:
        query = f"SELECT id, week_of, lesson_json, {time_col} FROM weekly_plans WHERE lesson_json LIKE '%Math%' AND lesson_json LIKE '%Grade 2%' AND lesson_json LIKE '%209%'"

    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        print(f"  Found {len(rows)} potential matches.")
        
        for row in rows:
            try:
                data = json.loads(row['lesson_json'])
                days = data.get('days', {})
                tuesday = days.get('tuesday', {})
                
                # Check for Mock Content in Tuesday
                objective = tuesday.get('objective', {})
                student_goal = objective.get('student_goal', '')
                wida = objective.get('wida_objective', '')
                
                has_mock = 'Mock Student Goal' in str(tuesday) or 'Mock Student Goal' in student_goal
                
                print(f"  Plan ID: {row['id']}")
                print(f"  Week: {row['week_of']}")
                if time_col:
                    print(f"  Time ({time_col}): {row[time_col]}")
                print(f"  Tuesday Student Goal: {student_goal[:50]}...")
                print(f"  Tuesday WIDA: {wida[:50]}...")
                print(f"  Has Mock Data: {has_mock}")
                print("  " + "-" * 30)
                
            except Exception as e:
                print(f"  Error parsing JSON for plan {row['id']}: {e}")

    except Exception as e:
        print(f"  Query failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # Based on settings.SQLITE_DB_PATH, the backend uses data/lesson_planner.db
    # BUT, the user says PC works and Tablet doesn't.
    # So we must compare the "working" DB (wherever that is) to the "broken" DB.
    # If settings point to data/lesson_planner.db, then PC and Tablet SHOULD be seeing the same file.
    # Unless Supabase is involved.
    
    check_db("Backend / Data DB", "d:/LP/data/lesson_planner.db")
    check_db("Root DB (Unused?)", "d:/LP/lesson_planner.db")

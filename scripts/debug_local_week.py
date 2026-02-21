
import sqlite3
import json
import sys
from pathlib import Path

DB_PATH = Path("data/lesson_planner.db")

def inspect_week(week_of_token):
    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    print(f"--- Inspecting Week: {week_of_token} ---")
    
    # Check WeeklyPlan
    plans = conn.execute(
        "SELECT * FROM weekly_plans WHERE week_of = ?", 
        (week_of_token,)
    ).fetchall()
    
    if not plans:
        print("No plans found in 'weekly_plans' table for this week.")
    else:
        for p in plans:
            print(f"\nPLAN: {p['id']}")
            print(f"  User ID: {p['user_id']}")
            print(f"  Status: {p['status']}")
            print(f"  Total Slots: {p['total_slots']}")
            print(f"  Generated At: {p['generated_at']}")
            
            # Check JSON content size
            lj_str = p['lesson_json']
            if lj_str:
                try:
                    lj = json.loads(lj_str)
                    days = lj.get('days', {})
                    print(f"  Lesson JSON: Valid JSON, {len(days)} days")
                    for d, data in days.items():
                        slots = data.get('slots', [])
                        print(f"    {d}: {len(slots)} slots")
                except Exception as e:
                    print(f"  Lesson JSON: ERROR parsing ({e})")
            else:
                print("  Lesson JSON: NULL/Empty")

            # Check LessonSteps
            steps = conn.execute(
                "SELECT count(*) as cnt FROM lesson_steps WHERE lesson_plan_id = ?",
                (p['id'],)
            ).fetchone()
            print(f"  Lesson Steps Count: {steps['cnt']}")

    conn.close()

if __name__ == "__main__":
    target_week = "01-05-01-09"
    if len(sys.argv) > 1:
        target_week = sys.argv[1]
    inspect_week(target_week)

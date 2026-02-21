import sqlite3
import json
from pathlib import Path

db_path = "d:/LP/data/lesson_planner.db"
plan_id = "plan_20251228152714"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT lesson_json FROM weekly_plans WHERE id=?", (plan_id,))
row = cursor.fetchone()
if row:
    with open("d:/LP/suspect_plan.json", "w") as f:
        f.write(json.dumps(json.loads(row[0]), indent=2))
    print(f"Dumped {plan_id} to d:/LP/suspect_plan.json")
else:
    print(f"Plan {plan_id} not found")
conn.close()

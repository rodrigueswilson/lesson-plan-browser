
import sys
import os
import json

# Add project root to path
sys.path.append(os.getcwd())

from backend.database import SQLiteDatabase

def dump_plan_structure(plan_id: str):
    db = SQLiteDatabase()
    plan = db.get_weekly_plan(plan_id)
    if not plan or not plan.lesson_json:
        print("Plan invalid")
        return

    days = plan.lesson_json.get("days", {})
    monday = days.get("monday", {})
    slots = monday.get("slots", [])
    
    if slots:
        print(json.dumps(slots[0], indent=2))
    else:
        print("No slots found for Monday")

if __name__ == "__main__":
    dump_plan_structure("plan_20251229174144")

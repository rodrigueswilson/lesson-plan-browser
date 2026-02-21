import sys
import os
import json

sys.path.append(os.getcwd())

from backend.database import SQLiteDatabase

def dump_json(plan_id: str):
    db = SQLiteDatabase()
    plan = db.get_weekly_plan(plan_id)
    if plan and plan.lesson_json:
        with open('full_plan.json', 'w', encoding='utf-8') as f:
            json.dump(plan.lesson_json, f, indent=2)
        print(f"Successfully dumped JSON to full_plan.json")
    else:
        print(f"Plan {plan_id} not found or has no JSON.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python dump_json.py <plan_id>")
    else:
        dump_json(sys.argv[1])

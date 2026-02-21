import sys
import os
import json

sys.path.append(os.getcwd())
from backend.database import SQLiteDatabase

def dump_slot1():
    db = SQLiteDatabase()
    plan = db.get_weekly_plan('plan_20251229135832')
    if not plan or not plan.lesson_json:
        print("Plan not found")
        return

    monday_slots = plan.lesson_json.get('days', {}).get('monday', {}).get('slots', [])
    slot1 = None
    for s in monday_slots:
        if s.get('slot_number') == 1 or (slot1 is None and s.get('metadata', {}).get('slot_number') == 1):
            slot1 = s
            break
    if not slot1 and monday_slots:
        slot1 = monday_slots[0]
    
    if slot1:
        print(json.dumps(slot1, indent=2))

dump_slot1()

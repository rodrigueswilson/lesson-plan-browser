import sys
import os
import json
import re

sys.path.append(os.getcwd())
from backend.database import SQLiteDatabase

def analyze_slot_1():
    db = SQLiteDatabase()
    plan = db.get_weekly_plan('plan_20251229135832')
    if not plan or not plan.lesson_json:
        print("Plan not found")
        return

    # 1. Intended links for Monday Slot 1
    intended = []
    for link in plan.lesson_json.get('_hyperlinks', []):
        day = (link.get('day_hint') or link.get('col_header') or '').lower().strip()
        slot = link.get('_source_slot')
        if day == 'monday' and slot == 1:
            intended.append(link)
    
    print(f"Intended for Monday Slot 1 ({len(intended)}):")
    for l in intended:
        print(f"  - [{l.get('text')}] ({l.get('url')})")

    # 2. Actual links found in Monday Slot 1
    monday_slots = plan.lesson_json.get('days', {}).get('monday', {}).get('slots', [])
    # Find slot with number 1 or index 0
    slot1 = None
    for s in monday_slots:
        if s.get('slot_number') == 1 or (slot1 is None and s.get('metadata', {}).get('slot_number') == 1):
            slot1 = s
            break
    if not slot1 and monday_slots:
        slot1 = monday_slots[0]
    
    if slot1:
        print(f"\nActual links in Monday Slot 1:")
        content = json.dumps(slot1)
        actual = re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', content)
        for text, url in actual:
            print(f"  - [{text}] ({url})")
            # Check where this URL came from in _hyperlinks
            for hl in plan.lesson_json.get('_hyperlinks', []):
                if hl.get('url') == url:
                    print(f"    (Source Metadata: Day={hl.get('day_hint')}, Slot={hl.get('_source_slot')})")

analyze_slot_1()

import sys
import os
import json

sys.path.append(os.getcwd())
from backend.database import SQLiteDatabase

def find_link(pattern):
    db = SQLiteDatabase()
    plan = db.get_weekly_plan('plan_20251229135832')
    if not plan or not plan.lesson_json:
        return

    print(f"Searching for '{pattern}' in root _hyperlinks...")
    found = False
    for hl in plan.lesson_json.get('_hyperlinks', []):
        if pattern.lower() in hl.get('text', '').lower():
            print(f"FOUND: {hl}")
            found = True
    
    if not found:
        print("Not found in _hyperlinks.")

find_link('Lenni Lenape')
find_link('Reading Log')
find_link('Second Grade Unit')

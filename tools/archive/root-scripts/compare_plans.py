
import sqlite3
import json

conn = sqlite3.connect("data/lesson_planner.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 1. Get Wilson's plan for 01-05-01-09
cursor.execute("SELECT * FROM weekly_plans WHERE user_id = '04fe8898-cb89-4a73-affb-64a97a98f820' AND week_of = '01-05-01-09'")
wilson_plan = cursor.fetchone()

if wilson_plan:
    print(f"=== Wilson's Plan {wilson_plan['id']} ===")
    print(f"Status: {wilson_plan['status']}")
    print(f"Outputs: {wilson_plan['output_file']}")
    try:
        ljson = json.loads(wilson_plan['lesson_json'])
        print(f"Days in JSON: {list(ljson.get('days', {}).keys())}")
        # Check first day
        day0 = list(ljson.get('days', {}).keys())[0] if ljson.get('days') else None
        if day0:
            slots = ljson['days'][day0].get('slots', [])
            print(f"Slots in {day0}: {len(slots)}")
    except Exception as e:
        print(f"Error parsing JSON: {e}")

# 2. Get any other successful plan for Wilson
cursor.execute("SELECT * FROM weekly_plans WHERE user_id = '04fe8898-cb89-4a73-affb-64a97a98f820' AND status = 'completed' AND week_of != '01-05-01-09' LIMIT 1")
other_plan = cursor.fetchone()

if other_plan:
    print(f"\n=== Other Plan {other_plan['id']} ({other_plan['week_of']}) ===")
    print(f"Status: {other_plan['status']}")

conn.close()

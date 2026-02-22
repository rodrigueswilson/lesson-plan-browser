
import sqlite3
import json
from datetime import datetime

conn = sqlite3.connect("data/lesson_planner.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=== USERS ===")
cursor.execute("SELECT id, name, email, created_at FROM users")
for row in cursor.fetchall():
    print(f"ID: {row['id']} | Name: {row['name']} | Email: {row['email']} | Created: {row['created_at']}")

print("\n=== PLANS FOR 01-05-01-09 ===")
cursor.execute("SELECT id, user_id, status, lesson_json, output_file FROM weekly_plans WHERE week_of = '01-05-01-09' ORDER BY user_id, id")
for row in cursor.fetchall():
    user_id = row['user_id']
    status = row['status']
    plan_id = row['id']
    output_file = row['output_file']
    
    lesson_json = {}
    if row['lesson_json']:
        try:
            lesson_json = json.loads(row['lesson_json'])
        except:
            lesson_json = {}
    
    if lesson_json is None:
        lesson_json = {}
        
    subjects = []
    days = lesson_json.get("days", {})
    if isinstance(days, dict):
        for day_name, day_data in days.items():
            if isinstance(day_data, dict):
                slots = day_data.get("slots", [])
                if isinstance(slots, list):
                    for slot in slots:
                        if isinstance(slot, dict):
                            subjects.append(slot.get("subject"))
    
    unique_subjects = sorted(list(set(s for s in subjects if s)))
    print(f"Plan ID: {plan_id} | User: {user_id} | Status: {status} | Subjects: {unique_subjects} | File: {output_file}")

conn.close()

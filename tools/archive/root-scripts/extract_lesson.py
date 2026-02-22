import sqlite3
import json
import os

def extract():
    db_path = r'd:\LP\data\lesson_planner.db'
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT lesson_json FROM weekly_plans WHERE id = "plan_20260118112824"')
    row = cursor.fetchone()
    conn.close()

    if row:
        lesson_json = json.loads(row[0])
        with open('latest_lesson.json', 'w', encoding='utf-8') as f:
            json.dump(lesson_json, f, indent=2)
        print("Successfully extracted lesson_json to latest_lesson.json")
    else:
        print("No plan found with the given ID")

if __name__ == "__main__":
    extract()

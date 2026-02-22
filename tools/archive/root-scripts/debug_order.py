
import sqlite3
import json
import os
from pathlib import Path

# Path to the database
db_paths = [
    Path(r"d:\LP\backend\data\lesson_planner.db"),
    Path(r"d:\LP\data\lesson_planner.db"),
    Path(r"d:\LP\data\lesson_plans.db")
]

def diagnostic():
    for db_path in db_paths:
        if not db_path.exists():
            print(f"\n===== DB NOT FOUND: {db_path} =====")
            continue
        
        print(f"\n===== Checking DB: {db_path} =====")
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
        except Exception as e:
            print(f"Error connecting to {db_path}: {e}")
            continue

        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row['name'] for row in cursor.fetchall()]
        print(f"Tables found: {tables}")

        if not tables:
            print("No tables found. Empty database.")
            conn.close()
            continue

        print("--- Row Counts ---")
        for table in ["users", "class_slots", "weekly_plans", "schedules"]:
            if table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"Table {table}: {count} rows")
            else:
                print(f"Table {table}: NOT FOUND")

        if "schedules" in tables:
            print("\n--- Checking Schedules Table ---")
            try:
                cursor.execute("SELECT id, user_id, day_of_week, slot_number, start_time, subject FROM schedules")
                rows = cursor.fetchall()
                
                schedule_counts = {}
                for row in rows:
                    key = (row['day_of_week'], row['slot_number'])
                    schedule_counts[key] = schedule_counts.get(key, 0) + 1
                
                duplicates = {k: v for k, v in schedule_counts.items() if v > 1}
                if duplicates:
                    print("Found duplicate (day, slot_number) in schedules:")
                    for k, v in duplicates.items():
                        print(f"  {k}: {v} occurrences")
                        cursor.execute("SELECT subject, start_time FROM schedules WHERE day_of_week = ? AND slot_number = ?", k)
                        dupe_rows = cursor.fetchall()
                        for dr in dupe_rows:
                            print(f"    Subject: {dr['subject']}, Time: {dr['start_time']}")
                else:
                    print("No duplicates found in schedules table.")
            except Exception as e:
                print(f"Error querying schedules: {e}")

        if "weekly_plans" in tables:
            print("\n--- Checking Weekly Plans (lesson_json) ---")
            try:
                cursor.execute(f"PRAGMA table_info(weekly_plans)")
                columns = [row['name'] for row in cursor.fetchall()]
                if 'lesson_json' in columns:
                    cursor.execute("SELECT id, week_of, CAST(lesson_json AS TEXT) as lesson_json FROM weekly_plans ORDER BY id DESC LIMIT 2")
                    plans = cursor.fetchall()
                    print(f"Fetched {len(plans)} plans.")

                    for plan in plans:
                        print(f"Plan ID: {plan['id']} (Week of: {plan['week_of']})")
                        if not plan['lesson_json']:
                            print("  No lesson_json found.")
                            continue
                        
                        try:
                            data = json.loads(plan['lesson_json'])
                        except:
                            print("  Failed to parse lesson_json.")
                            continue
                            
                        days_data = data.get("days", {})
                        for day, day_data in days_data.items():
                            slots = day_data.get("slots", [])
                            slot_nums = [s.get("slot_number") for s in slots if isinstance(s, dict)]
                            
                            # Check for duplicates
                            counts = {}
                            for n in slot_nums:
                                counts[n] = counts.get(n, 0) + 1
                            
                            day_dupes = {k: v for k, v in counts.items() if v > 1}
                            if day_dupes:
                                print(f"  Day '{day}' has duplicate slots in JSON: {day_dupes}")
                            
                            # Check for types
                            types = set(type(n) for n in slot_nums)
                            if len(types) > 1:
                                print(f"  Day '{day}' has mixed slot_number types: {types}")
                            elif types and str in types:
                                print(f"  Day '{day}' has string slot_numbers: {slot_nums}")
                else:
                    print("Column 'lesson_json' NOT FOUND in weekly_plans")
            except Exception as e:
                print(f"Error querying weekly_plans: {e}")

        conn.close()

if __name__ == "__main__":
    diagnostic()

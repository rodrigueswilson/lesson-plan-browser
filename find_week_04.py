#!/usr/bin/env python3
"""Find week '1_19_26-1_23' (week 04) in the database."""

import sqlite3
import json
from pathlib import Path

db_path = Path("data/lesson_planner.db")

if not db_path.exists():
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Try different format variations
week_patterns = [
    "01/19-01/23",  # Most common format
    "01-19-01-23",  # Alternative format
    "1-19-1-23",    # Without leading zeros
    "1/19-1/23",    # Without leading zeros, with slashes
]

print("Searching for week '1_19_26-1_23' (January 19-23, 2026) - Week 04...")
print("=" * 80)

found_any = False
all_plans = []

for pattern in week_patterns:
    cursor.execute(
        "SELECT id, user_id, week_of, status, generated_at, week_folder_path, total_slots, lesson_json "
        "FROM weekly_plans WHERE week_of = ? OR week_of LIKE ? "
        "ORDER BY generated_at DESC",
        (pattern, f"%{pattern}%")
    )
    plans = cursor.fetchall()
    
    if plans:
        found_any = True
        all_plans.extend(plans)
        print(f"\nFound {len(plans)} plan(s) matching pattern '{pattern}':")
        print("-" * 80)
        for plan in plans:
            print(f"Plan ID: {plan['id']}")
            print(f"  User ID: {plan['user_id']}")
            print(f"  Week Of: {plan['week_of']}")
            print(f"  Status: {plan['status']}")
            print(f"  Total Slots: {plan['total_slots']}")
            print(f"  Generated At: {plan['generated_at']}")
            if plan['week_folder_path']:
                print(f"  Week Folder: {plan['week_folder_path']}")
            print()

if not found_any:
    print("\nNo plans found with exact matches. Searching for similar patterns...")
    cursor.execute(
        "SELECT DISTINCT week_of FROM weekly_plans "
        "WHERE week_of LIKE '%01-19%' OR week_of LIKE '%01/19%' OR week_of LIKE '%1-19%' OR week_of LIKE '%1/19%' "
        "ORDER BY week_of"
    )
    weeks = cursor.fetchall()
    if weeks:
        print("Found weeks containing '01-19' or '01/19':")
        for week in weeks:
            print(f"  - {week['week_of']}")
    else:
        print("  No matching weeks found.")

# Display detailed information for found plans
if all_plans:
    print("\n" + "=" * 80)
    print("DETAILED PLAN INFORMATION:")
    print("=" * 80)
    
    for i, plan in enumerate(all_plans, 1):
        print(f"\n--- Plan {i} ---")
        print(f"Plan ID: {plan['id']}")
        print(f"User ID: {plan['user_id']}")
        print(f"Week Of: {plan['week_of']}")
        print(f"Status: {plan['status']}")
        print(f"Total Slots: {plan['total_slots']}")
        print(f"Generated At: {plan['generated_at']}")
        if plan['week_folder_path']:
            print(f"Week Folder: {plan['week_folder_path']}")
        
        # Try to parse and display lesson_json metadata
        if plan['lesson_json']:
            try:
                lesson_data = json.loads(plan['lesson_json']) if isinstance(plan['lesson_json'], str) else plan['lesson_json']
                if isinstance(lesson_data, dict):
                    metadata = lesson_data.get('metadata', {})
                    if metadata:
                        print("\nMetadata:")
                        for key, value in metadata.items():
                            print(f"  {key}: {value}")
                    
                    # Show days structure
                    days = lesson_data.get('days', {})
                    if days:
                        print(f"\nDays in plan: {', '.join(days.keys())}")
                        for day_name, day_data in days.items():
                            if isinstance(day_data, dict):
                                slots = day_data.get('slots', [])
                                print(f"  {day_name}: {len(slots)} slot(s)")
            except Exception as e:
                print(f"  Could not parse lesson_json: {e}")

# Also check if there's a week_number field or any metadata
print("\n" + "=" * 80)
print("All distinct week_of values in database (for reference):")
cursor.execute("SELECT DISTINCT week_of FROM weekly_plans ORDER BY week_of")
all_weeks = cursor.fetchall()
print(f"Total unique weeks in database: {len(all_weeks)}")
if len(all_weeks) <= 30:
    for week in all_weeks:
        print(f"  - {week['week_of']}")
else:
    print("  (Too many to display - showing first 30)")
    for week in all_weeks[:30]:
        print(f"  - {week['week_of']}")

conn.close()

#!/usr/bin/env python3
"""Quick script to check if plans for a specific week exist in the database."""

import sqlite3
import sys

week_pattern = sys.argv[1] if len(sys.argv) > 1 else "12-08"

conn = sqlite3.connect("data/lesson_planner.db")
cursor = conn.cursor()

# Check for plans matching the week pattern
plans = cursor.execute(
    "SELECT id, user_id, week_of, generated_at FROM weekly_plans WHERE week_of LIKE ? ORDER BY generated_at DESC",
    (f"%{week_pattern}%",)
).fetchall()

print(f"\nFound {len(plans)} plans matching '{week_pattern}':")
print("-" * 80)
for plan_id, user_id, week_of, generated_at in plans:
    print(f"ID: {plan_id[:8]}... | User: {user_id[:8]}... | Week: {week_of} | Generated: {generated_at}")

conn.close()


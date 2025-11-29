"""Check the status of the most recent processing plan."""

from backend.database import get_db
from datetime import datetime

db = get_db()

# Get all plans from database directly
import sqlite3
conn = sqlite3.connect('data/lesson_planner.db')
cursor = conn.cursor()
cursor.execute("SELECT * FROM weekly_plans ORDER BY generated_at DESC LIMIT 5")
columns = [desc[0] for desc in cursor.description]
plans = [dict(zip(columns, row)) for row in cursor.fetchall()]
conn.close()
if not plans:
    print("No plans found in database")
    exit(0)

# Sort by generated_at (most recent first)
plans_sorted = sorted(plans, key=lambda x: x.get('generated_at', ''), reverse=True)

print("=" * 60)
print("MOST RECENT PLANS")
print("=" * 60)
print()

for i, plan in enumerate(plans_sorted[:5], 1):
    print(f"Plan {i}:")
    print(f"  ID: {plan['id']}")
    print(f"  User ID: {plan['user_id']}")
    print(f"  Week: {plan['week_of']}")
    print(f"  Status: {plan['status']}")
    print(f"  Created: {plan['generated_at']}")
    if plan.get('error_message'):
        print(f"  Error: {plan['error_message']}")
    if plan.get('output_file'):
        print(f"  Output: {plan['output_file']}")
    print()

print("=" * 60)

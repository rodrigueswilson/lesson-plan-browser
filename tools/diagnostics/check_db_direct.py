"""Check database directly with sqlite3."""

import sqlite3
from pathlib import Path

db_path = Path("data/lesson_planner.db")

if not db_path.exists():
    print(f"❌ Database not found: {db_path}")
    exit(1)

print(f"✅ Database found: {db_path}")
print(f"   Size: {db_path.stat().st_size:,} bytes")

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Get most recent plans
print("\n" + "=" * 80)
print("MOST RECENT PLANS")
print("=" * 80)

cursor.execute("""
    SELECT plan_id, user_id, week_of, status, created_at, error_message, output_file
    FROM weekly_plans
    ORDER BY created_at DESC
    LIMIT 5
""")

plans = cursor.fetchall()

if not plans:
    print("\n❌ No plans found in database")
else:
    for plan in plans:
        plan_id, user_id, week_of, status, created_at, error_msg, output_file = plan
        print(f"\n📋 Plan: {plan_id[:8]}...")
        print(f"   User: {user_id[:8]}...")
        print(f"   Week: {week_of}")
        print(f"   Status: {status}")
        print(f"   Created: {created_at}")
        
        if status == "failed" and error_msg:
            print(f"   ❌ Error: {error_msg}")
        elif status == "completed" and output_file:
            print(f"   ✅ Output: {output_file}")
        elif status == "processing":
            print(f"   ⏳ Still processing (likely crashed)")

conn.close()

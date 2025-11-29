"""Check recent plans."""

import sqlite3
from pathlib import Path

db_path = Path("data/lesson_planner.db")
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 80)
print("MOST RECENT PLANS (Last 5)")
print("=" * 80)

cursor.execute("""
    SELECT id, user_id, week_of, status, generated_at, error_message, output_file
    FROM weekly_plans
    ORDER BY generated_at DESC
    LIMIT 5
""")

plans = cursor.fetchall()

for plan in plans:
    plan_id, user_id, week_of, status, generated_at, error_msg, output_file = plan
    print(f"\n📋 Plan: {plan_id[:8]}...")
    print(f"   User: {user_id[:8]}...")
    print(f"   Week: {week_of}")
    print(f"   Status: {status}")
    print(f"   Generated: {generated_at}")
    
    if status == "failed" and error_msg:
        print(f"   ❌ Error: {error_msg[:200]}")
    elif status == "completed" and output_file:
        print(f"   ✅ Output: {output_file}")
        # Check if file exists
        if Path(output_file).exists():
            print(f"      File exists: YES")
        else:
            print(f"      File exists: NO")
    elif status == "processing":
        print(f"   ⏳ Status: Processing (likely crashed)")
    elif status == "pending":
        print(f"   ⏸️  Status: Pending (never started)")

conn.close()

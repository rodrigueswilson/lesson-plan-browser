"""Check current processing status."""

import sqlite3
from pathlib import Path
from datetime import datetime

db_path = Path("data/lesson_plans.db")

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 80)
print("CURRENT PROCESSING STATUS")
print("=" * 80)

# Get most recent plan
cursor.execute("""
    SELECT id, user_id, week_of, status, generated_at, error_message
    FROM weekly_plans
    ORDER BY generated_at DESC
    LIMIT 1
""")

plan = cursor.fetchone()

if plan:
    plan_id, user_id, week_of, status, generated_at, error_msg = plan
    
    print(f"\n📋 Most Recent Plan:")
    print(f"   Plan ID: {plan_id}")
    print(f"   Week: {week_of}")
    print(f"   Status: {status}")
    print(f"   Started: {generated_at}")
    
    if error_msg:
        print(f"   ❌ Error: {error_msg}")
    
    # Check progress tracker
    print(f"\n🔍 Checking progress tracker...")
    print(f"   (Progress tracker is in-memory, so we can't check from here)")
    print(f"   The backend needs to be restarted to load the progress fix.")
    
    # Time elapsed
    try:
        start_time = datetime.fromisoformat(generated_at)
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n⏱️  Time elapsed: {elapsed:.0f} seconds")
        
        if elapsed > 60:
            print(f"   ({elapsed/60:.1f} minutes)")
    except:
        pass
else:
    print("\n❌ No plans found")

conn.close()

print("\n" + "=" * 80)
print("RECOMMENDATION")
print("=" * 80)
print("""
The progress bar fix requires a backend restart to take effect.

Current situation:
- Backend is running with OLD code (no progress connection)
- Processing is happening but progress tracker isn't initialized
- Progress bar shows fake/simulated progress

To fix:
1. Let current processing finish (or cancel it)
2. Restart the backend
3. Try processing again
4. Progress bar will show real updates

OR: Just wait for this processing to complete and check the output file.
The media anchoring will still work even without progress updates!
""")

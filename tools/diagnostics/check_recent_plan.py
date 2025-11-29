"""Check the most recent plan in the database."""

from backend.database import Database
from backend.config import settings
from datetime import datetime

db = Database(settings.DATABASE_URL)

print("=" * 80)
print("CHECKING MOST RECENT PLAN")
print("=" * 80)

# Get all users
users = db.get_users()
print(f"\nTotal users: {len(users)}")

for user in users:
    print(f"\n👤 User: {user.name} ({user.user_id})")
    
    # Get plans for this user
    plans = db.get_user_plans(user.user_id, limit=5)
    
    if plans:
        print(f"   Recent plans: {len(plans)}")
        
        for plan in plans[:3]:  # Show last 3
            print(f"\n   📋 Plan ID: {plan.plan_id[:8]}...")
            print(f"      Week: {plan.week_of}")
            print(f"      Status: {plan.status}")
            print(f"      Created: {plan.created_at}")
            
            if plan.status == "failed":
                print(f"      ❌ Error: {plan.error_message}")
            elif plan.status == "completed":
                print(f"      ✅ Output: {plan.output_file}")
            elif plan.status == "processing":
                print(f"      ⏳ Still processing...")
            elif plan.status == "pending":
                print(f"      ⏸️  Pending (never started)")
    else:
        print("   No plans found")

print("\n" + "=" * 80)

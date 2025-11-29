"""Check users in the database."""
from backend.database import Database

# Check main database
print("Main Database (data/lesson_planner.db):")
print("=" * 60)
db = Database("data/lesson_planner.db")
users = db.list_users()
print(f"Found {len(users)} users:")
for user in users:
    print(f"  - {user['name']} (ID: {user['id'][:8]}...)")
    print(f"    Email: {user.get('email', 'N/A')}")
    
    # Get slots for this user
    slots = db.get_user_slots(user['id'])
    print(f"    Slots: {len(slots)}")
    
    # Get plans for this user
    plans = db.get_user_plans(user['id'], limit=5)
    print(f"    Plans: {len(plans)}")
    print()

# Check demo database
print("\nDemo Database (data/demo_tracking.db):")
print("=" * 60)
try:
    demo_db = Database("data/demo_tracking.db")
    demo_users = demo_db.list_users()
    print(f"Found {len(demo_users)} users:")
    for user in demo_users:
        print(f"  - {user['name']} (ID: {user['id'][:8]}...)")
except Exception as e:
    print(f"Error: {e}")

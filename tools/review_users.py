"""
Review users and their data in SQLite database.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import SQLiteDatabase

def main():
    db = SQLiteDatabase()
    users = db.list_users()
    
    print("=" * 70)
    print("USERS IN SQLITE DATABASE")
    print("=" * 70)
    print(f"\nTotal users: {len(users)}\n")
    
    for i, user in enumerate(users, 1):
        # Handle both SQLModel objects and dictionaries
        if hasattr(user, "id"):
            user_id = user.id
            name = getattr(user, "name", "N/A")
            email = getattr(user, "email", "N/A")
        else:
            user_id = user['id']
            name = user.get('name', 'N/A')
            email = user.get('email', 'N/A')
        
        slots = db.get_user_slots(user_id)
        plans = db.get_user_plans(user_id, limit=10000)
        
        # Count performance metrics for this user's plans
        metrics_count = 0
        for plan in plans:
            # Handle both object and dict access for plans
            plan_id = plan.id if hasattr(plan, "id") else plan['id']
            plan_metrics = db.get_plan_metrics(plan_id)
            metrics_count += len(plan_metrics)
        
        print(f"{i}. {name}")
        print(f"   ID: {user_id}")
        print(f"   Email: {email}")
        print(f"   Class slots: {len(slots)}")
        print(f"   Weekly plans: {len(plans)}")
        print(f"   Performance metrics: {metrics_count}")
        print()
    
    # Find specific users
    print("=" * 70)
    print("USER ASSIGNMENT CHECK")
    print("=" * 70)
    
    daniela = None
    wilson = None
    
    for user in users:
        name = user.get('name', '').lower()
        if 'daniela' in name or 'silva' in name:
            daniela = user
        if 'wilson' in name or 'rodrigues' in name:
            wilson = user
    
    if daniela:
        print(f"\nDaniela Silva found:")
        print(f"  ID: {daniela['id']}")
        print(f"  Name: {daniela.get('name', 'N/A')}")
        slots = db.get_user_slots(daniela['id'])
        plans = db.get_user_plans(daniela['id'], limit=10000)
        metrics = sum(len(db.get_plan_metrics(p['id'])) for p in plans)
        print(f"  Class slots: {len(slots)}")
        print(f"  Weekly plans: {len(plans)}")
        print(f"  Performance metrics: {metrics}")
    else:
        print("\nDaniela Silva NOT found in database")
    
    if wilson:
        print(f"\nWilson Rodrigues found:")
        print(f"  ID: {wilson['id']}")
        print(f"  Name: {wilson.get('name', 'N/A')}")
        slots = db.get_user_slots(wilson['id'])
        plans = db.get_user_plans(wilson['id'], limit=10000)
        metrics = sum(len(db.get_plan_metrics(p['id'])) for p in plans)
        print(f"  Class slots: {len(slots)}")
        print(f"  Weekly plans: {len(plans)}")
        print(f"  Performance metrics: {metrics}")
    else:
        print("\nWilson Rodrigues NOT found in database")
    
    print("\n" + "=" * 70)
    print("MIGRATION PLAN")
    print("=" * 70)
    print("\nProject 1 (Wilson Rodrigues User 1) should contain:")
    if wilson:
        print(f"  - User: {wilson.get('name', 'N/A')}")
        print(f"  - Class slots: {len(db.get_user_slots(wilson['id']))}")
        print(f"  - Weekly plans: {len(db.get_user_plans(wilson['id'], limit=10000))}")
    else:
        print("  - User: Wilson Rodrigues (NOT FOUND)")
    
    print("\nProject 2 (Daniela Silva) should contain:")
    if daniela:
        print(f"  - User: {daniela.get('name', 'N/A')}")
        print(f"  - Class slots: {len(db.get_user_slots(daniela['id']))}")
        print(f"  - Weekly plans: {len(db.get_user_plans(daniela['id'], limit=10000))}")
    else:
        print("  - User: Daniela Silva (NOT FOUND)")

if __name__ == "__main__":
    main()


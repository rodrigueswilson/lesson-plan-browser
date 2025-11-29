"""Check data in Supabase database."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import get_db

def main():
    db = get_db()
    users = db.list_users()
    
    print("=" * 70)
    print("SUPABASE DATABASE STATUS")
    print("=" * 70)
    print(f"\nTotal users: {len(users)}\n")
    
    for user in users:
        user_id = user['id']
        name = user.get('name', 'N/A')
        email = user.get('email', 'N/A')
        
        slots = db.get_user_slots(user_id)
        plans = db.get_user_plans(user_id, limit=10000)
        
        # Count performance metrics
        metrics_count = 0
        for plan in plans:
            plan_metrics = db.get_plan_metrics(plan['id'])
            metrics_count += len(plan_metrics)
        
        print(f"User: {name}")
        print(f"  ID: {user_id}")
        print(f"  Email: {email}")
        print(f"  Class slots: {len(slots)}")
        print(f"  Weekly plans: {len(plans)}")
        print(f"  Performance metrics: {metrics_count}")
        print()

if __name__ == "__main__":
    main()


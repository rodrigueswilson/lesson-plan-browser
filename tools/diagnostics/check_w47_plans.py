"""Check if week 47 lesson plans exist in the database."""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database import get_db
from backend.config import settings

def check_w47_plans():
    """Check for week 47 plans in database."""
    db = get_db()
    
    # Get all users
    users = db.list_users()
    print(f"Found {len(users)} users in database")
    
    # Check each user for w47 plans
    w47_plans = []
    for user in users:
        user_id = user['id']
        plans = db.get_user_plans(user_id, limit=100)
        
        # Look for week 47 (could be "11/18-11/22" or similar format)
        for plan in plans:
            week_of = plan.get('week_of', '')
            # Check if it's week 47 - could be various formats
            if '47' in week_of or 'w47' in week_of.lower() or 'week 47' in week_of.lower():
                w47_plans.append({
                    'user_id': user_id,
                    'user_name': user.get('name', 'Unknown'),
                    'plan_id': plan.get('id'),
                    'week_of': week_of,
                    'status': plan.get('status'),
                    'output_file': plan.get('output_file')
                })
    
    if w47_plans:
        print(f"\nFound {len(w47_plans)} week 47 plans:")
        for plan in w47_plans:
            print(f"  - User: {plan['user_name']}")
            print(f"    Week: {plan['week_of']}")
            print(f"    Plan ID: {plan['plan_id']}")
            print(f"    Status: {plan['status']}")
            print(f"    Output: {plan['output_file']}")
            print()
    else:
        print("\nNo week 47 plans found in database.")
        print("\nRecent plans:")
        # Show recent plans to help identify format
        for user in users[:2]:  # Check first 2 users
            plans = db.get_user_plans(user['id'], limit=5)
            print(f"\nUser: {user.get('name', 'Unknown')}")
            for plan in plans:
                print(f"  Week: {plan.get('week_of', 'N/A')}, Status: {plan.get('status', 'N/A')}")

if __name__ == '__main__':
    check_w47_plans()


"""Script to clear cached lesson plans for a specific week to force regeneration."""
import sys
from backend.database import get_db

def clear_plan_cache(user_id: str, week_of: str = None):
    """Delete cached plans for a user/week to force regeneration."""
    print(f"Clearing plan cache for user: {user_id}")
    if week_of:
        print(f"  Week: {week_of}")
    print("=" * 80)
    
    db = get_db(user_id=user_id)
    
    if week_of:
        # Delete specific week
        plans = db.get_user_plans(user_id, limit=1000)
        deleted = 0
        for plan in plans:
            if plan.week_of == week_of:
                print(f"Deleting plan: {plan.id} (week_of: {plan.week_of})")
                # Note: This would need a delete method in the database interface
                # For now, just list what would be deleted
                deleted += 1
        print(f"\nWould delete {deleted} plans for week {week_of}")
        print("NOTE: To actually delete, you may need to use SQL directly or add a delete method.")
    else:
        # List all plans
        plans = db.get_user_plans(user_id, limit=1000)
        print(f"\nFound {len(plans)} plans for user {user_id}")
        print("\nTo force regeneration, delete the plans for the specific week you want to regenerate.")
        print("You can do this by:")
        print("1. Using the UI to delete the plan")
        print("2. Regenerating with force_ai=True (if available)")
        print("3. Manually deleting from database")

if __name__ == "__main__":
    user_id = sys.argv[1] if len(sys.argv) > 1 else "04fe8898-cb89-4a73-affb-64a97a98f820"
    week_of = sys.argv[2] if len(sys.argv) > 2 else None
    clear_plan_cache(user_id, week_of)

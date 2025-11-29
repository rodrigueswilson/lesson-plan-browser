"""
Script to check and fix lesson plan status in the database.
If a plan has output files but status is 'failed', update it to 'completed'.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.database import get_db

def fix_plan_status(plan_id: str, user_id: str):
    """Fix plan status if files exist but status is 'failed'."""
    db = get_db(user_id=user_id)
    
    plan = db.get_weekly_plan(plan_id)
    if not plan:
        print(f"[ERROR] Plan {plan_id} not found in database")
        return False
    
    print(f"\nPlan ID: {plan_id}")
    print(f"Status: {plan.status}")
    print(f"Output file: {plan.output_file}")
    print(f"Week of: {plan.week_of}")
    
    # Check if output file exists
    if plan.output_file:
        output_path = Path(plan.output_file)
        if output_path.exists():
            print(f"[OK] Output file exists: {output_path}")
            
            if plan.status == "failed":
                print(f"[FIXING] Updating status from 'failed' to 'completed'...")
                db.update_weekly_plan(plan_id, status="completed")
                print(f"[OK] Status updated to 'completed'")
                return True
            else:
                print(f"[OK] Status is already '{plan.status}'")
                return True
        else:
            print(f"[WARNING] Output file does not exist: {output_path}")
            return False
    else:
        print(f"[WARNING] No output file path in database")
        return False


def find_plans_by_week(week_of: str, user_id: str):
    """Find all plans for a given week."""
    db = get_db(user_id=user_id)
    
    # Get all plans for user
    plans = db.get_user_plans(user_id, limit=100)
    
    matching_plans = [p for p in plans if p.week_of == week_of]
    
    return matching_plans


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix lesson plan status in database")
    parser.add_argument("--plan-id", help="Plan ID to fix")
    parser.add_argument("--week-of", help="Week of (e.g., 11-17-11-21) to find and fix plans")
    parser.add_argument("--user-id", required=True, help="User ID")
    
    args = parser.parse_args()
    
    if args.plan_id:
        fix_plan_status(args.plan_id, args.user_id)
    elif args.week_of:
        print(f"Finding plans for week: {args.week_of}")
        plans = find_plans_by_week(args.week_of, args.user_id)
        print(f"\nFound {len(plans)} plan(s):")
        for plan in plans:
            print(f"  - Plan ID: {plan.id}, Status: {plan.status}, Output: {plan.output_file}")
            if plan.status == "failed" and plan.output_file:
                output_path = Path(plan.output_file)
                if output_path.exists():
                    print(f"    [FIXING] Updating status...")
                    fix_plan_status(plan.id, args.user_id)
    else:
        parser.print_help()


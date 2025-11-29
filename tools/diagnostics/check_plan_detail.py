"""
Script to check detailed lesson plan data structure.
"""

import sys
from pathlib import Path
import json

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.database import get_db

def check_plan_detail(plan_id: str, user_id: str):
    """Check detailed plan data structure."""
    db = get_db(user_id=user_id)
    
    plan = db.get_weekly_plan(plan_id)
    if not plan:
        print(f"[ERROR] Plan {plan_id} not found")
        return
    
    lesson_json = plan.lesson_json
    if isinstance(lesson_json, str):
        lesson_json = json.loads(lesson_json)
    
    print(f"\nPlan ID: {plan_id}")
    print(f"Week of: {plan.week_of}")
    print(f"Status: {plan.status}")
    print(f"\nLesson JSON structure:")
    print(f"  Top-level keys: {list(lesson_json.keys())}")
    
    if "days" in lesson_json:
        days = lesson_json["days"]
        print(f"\nDays found: {list(days.keys())}")
        
        # Check first day structure
        if days:
            first_day_name = list(days.keys())[0]
            first_day = days[first_day_name]
            print(f"\nFirst day ({first_day_name}):")
            print(f"  Keys: {list(first_day.keys())}")
            
            if "slots" in first_day:
                slots = first_day["slots"]
                print(f"  Has slots: {len(slots)} slots")
                if slots:
                    first_slot = slots[0]
                    print(f"  First slot keys: {list(first_slot.keys())[:10]}")
                    print(f"  First slot number: {first_slot.get('slot_number', 'N/A')}")
                    print(f"  First slot subject: {first_slot.get('subject', 'N/A')}")
            else:
                print(f"  [WARNING] No 'slots' key in day data")
    else:
        print(f"\n[ERROR] No 'days' key in lesson_json")
    
    # Also check if there's a JSON file on disk
    if plan.output_file:
        output_path = Path(plan.output_file)
        json_path = output_path.with_suffix('.json')
        if json_path.exists():
            print(f"\nJSON file exists: {json_path}")
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    file_json = json.load(f)
                print(f"  JSON file has {len(file_json.get('days', {}))} days")
                
                # Compare with database
                db_days = lesson_json.get("days", {})
                file_days = file_json.get("days", {})
                
                if len(db_days) != len(file_days):
                    print(f"  [WARNING] Day count mismatch: DB has {len(db_days)}, file has {len(file_days)}")
                else:
                    print(f"  [OK] Day count matches between DB and file")
            except Exception as e:
                print(f"  [ERROR] Failed to read JSON file: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Check detailed lesson plan data")
    parser.add_argument("--plan-id", required=True, help="Plan ID")
    parser.add_argument("--user-id", required=True, help="User ID")
    
    args = parser.parse_args()
    
    check_plan_detail(args.plan_id, args.user_id)


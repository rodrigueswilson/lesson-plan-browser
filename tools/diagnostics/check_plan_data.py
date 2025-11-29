"""
Script to check if a lesson plan has lesson_json stored in the database.
"""

import sys
from pathlib import Path
import json

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.database import get_db

def check_plan_data(plan_id: str, user_id: str):
    """Check if plan has lesson_json."""
    db = get_db(user_id=user_id)
    
    plan = db.get_weekly_plan(plan_id)
    if not plan:
        print(f"[ERROR] Plan {plan_id} not found in database")
        return False
    
    print(f"\nPlan ID: {plan_id}")
    print(f"Status: {plan.status}")
    print(f"Week of: {plan.week_of}")
    print(f"Output file: {plan.output_file}")
    print(f"Has lesson_json: {plan.lesson_json is not None}")
    
    if plan.lesson_json:
        if isinstance(plan.lesson_json, str):
            try:
                lesson_json = json.loads(plan.lesson_json)
                print(f"lesson_json is a string, parsed successfully")
            except json.JSONDecodeError:
                print(f"[ERROR] lesson_json is invalid JSON string")
                return False
        else:
            lesson_json = plan.lesson_json
            print(f"lesson_json is a dict/object")
        
        # Check structure
        if isinstance(lesson_json, dict):
            print(f"  Keys: {list(lesson_json.keys())[:10]}...")
            if "days" in lesson_json:
                days = lesson_json.get("days", {})
                print(f"  Days: {list(days.keys())}")
                if days:
                    first_day = list(days.values())[0]
                    if isinstance(first_day, dict):
                        if "slots" in first_day:
                            slots = first_day.get("slots", [])
                            print(f"  First day has {len(slots)} slots")
        else:
            print(f"[WARNING] lesson_json is not a dict: {type(lesson_json)}")
    else:
        print(f"[WARNING] plan.lesson_json is None or empty")
        
        # Check if output file exists and try to load JSON from there
        if plan.output_file:
            output_path = Path(plan.output_file)
            if output_path.exists():
                print(f"\nOutput file exists: {output_path}")
                # Look for corresponding JSON file
                json_path = output_path.with_suffix('.json')
                if json_path.exists():
                    print(f"Found JSON file: {json_path}")
                    try:
                        with open(json_path, 'r', encoding='utf-8') as f:
                            json_data = json.load(f)
                        print(f"[OK] JSON file is valid and has {len(json_data.get('days', {}))} days")
                        print(f"[INFO] You may need to update the plan with this JSON data")
                    except Exception as e:
                        print(f"[ERROR] Failed to read JSON file: {e}")
            else:
                print(f"[WARNING] Output file does not exist: {output_path}")
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Check lesson plan data in database")
    parser.add_argument("--plan-id", required=True, help="Plan ID to check")
    parser.add_argument("--user-id", required=True, help="User ID")
    
    args = parser.parse_args()
    
    check_plan_data(args.plan_id, args.user_id)

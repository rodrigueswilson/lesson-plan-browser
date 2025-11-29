"""Check what lesson_json data exists in the database"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database import get_db
import json

def main():
    db = get_db()
    
    # Get all plans
    print("Checking weekly_plans table...")
    print("=" * 60)
    
    # Try to get plans for a user (you may need to adjust user_id)
    # First, let's see what users exist
    try:
        users = db.list_users()
        print(f"\nFound {len(users)} users:")
        for user in users[:5]:  # Show first 5
            print(f"  - {user['id']}: {user.get('first_name', '')} {user.get('last_name', '')}")
        
        if users:
            user_id = users[0]['id']
            print(f"\nChecking plans for user: {user_id}")
            plans = db.get_user_plans(user_id, limit=5)
            
            print(f"\nFound {len(plans)} plans:")
            for plan in plans:
                print(f"\n  Plan ID: {plan['id']}")
                print(f"  Week of: {plan.get('week_of', 'N/A')}")
                print(f"  Status: {plan.get('status', 'N/A')}")
                print(f"  Generated at: {plan.get('generated_at', 'N/A')}")
                
                lesson_json = plan.get('lesson_json')
                if lesson_json is None:
                    print(f"  lesson_json: NULL (not set)")
                elif isinstance(lesson_json, str):
                    try:
                        parsed = json.loads(lesson_json)
                        print(f"  lesson_json: String (length: {len(lesson_json)})")
                        print(f"  Parsed structure: {list(parsed.keys()) if isinstance(parsed, dict) else type(parsed)}")
                        if isinstance(parsed, dict) and 'days' in parsed:
                            print(f"  Days available: {list(parsed['days'].keys())}")
                    except json.JSONDecodeError as e:
                        print(f"  lesson_json: Invalid JSON string - {e}")
                elif isinstance(lesson_json, dict):
                    print(f"  lesson_json: Dict with keys: {list(lesson_json.keys())}")
                    if 'days' in lesson_json:
                        print(f"  Days available: {list(lesson_json['days'].keys())}")
                else:
                    print(f"  lesson_json: {type(lesson_json)}")
        else:
            print("\nNo users found in database")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()


"""Backfill lesson_json from JSON files to database"""
import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database import get_db

def find_json_files(base_path, week_of):
    """Find JSON files for a given week"""
    json_files = []
    
    # Try to find week folder
    # Week format is typically "MM-DD-MM-DD" like "11-10-11-14"
    # Folder might be named like "25 W45" or similar
    
    if not base_path or not os.path.exists(base_path):
        return json_files
    
    base = Path(base_path)
    
    # Look for week folders
    for folder in base.iterdir():
        if not folder.is_dir():
            continue
            
        # Check if this folder might contain our week
        # Look for JSON files in the folder
        for json_file in folder.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Check if this JSON matches our week
                    metadata = data.get('metadata', {})
                    if metadata.get('week_of') == week_of or week_of in str(json_file):
                        json_files.append((json_file, data))
            except Exception as e:
                print(f"  Error reading {json_file}: {e}")
                continue
    
    return json_files

def main():
    db = get_db()
    
    # Get all plans with NULL lesson_json
    print("Finding plans with NULL lesson_json...")
    print("=" * 60)
    
    users = db.list_users()
    
    for user in users:
        user_id = user['id']
        user_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
        base_path = user.get('base_path_override')
        
        print(f"\nUser: {user_name} ({user_id})")
        print(f"Base path: {base_path or 'Not set'}")
        
        if not base_path:
            print("  Skipping - no base_path_override set")
            continue
        
        plans = db.get_user_plans(user_id, limit=50)
        
        for plan in plans:
            plan_id = plan['id']
            week_of = plan.get('week_of')
            lesson_json = plan.get('lesson_json')
            
            if lesson_json is not None:
                print(f"  Plan {plan_id} ({week_of}): Already has lesson_json")
                continue
            
            print(f"  Plan {plan_id} ({week_of}): Looking for JSON files...")
            
            # Try to find JSON files
            json_files = find_json_files(base_path, week_of)
            
            if json_files:
                print(f"    Found {len(json_files)} JSON file(s)")
                # Use the first one (or merge if multiple)
                json_file, json_data = json_files[0]
                print(f"    Loading from: {json_file}")
                
                try:
                    # Save to database
                    db.update_weekly_plan(plan_id, lesson_json=json_data)
                    print(f"    [OK] Saved lesson_json to database")
                except Exception as e:
                    print(f"    [ERROR] Error saving: {e}")
            else:
                print(f"    No JSON files found for this week")

if __name__ == '__main__':
    main()


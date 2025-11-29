"""
Generate objectives DOCX file from lesson plan data in the database.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from backend.database import SQLiteDatabase
from backend.services.objectives_printer import ObjectivesPrinter


def find_latest_plan(user_id: str = None):
    """Find the latest weekly plan in the database."""
    db = SQLiteDatabase()
    
    # Get all weekly plans - use get_all_weekly_plans or query directly
    with db.get_connection() as conn:
        if user_id:
            cursor = conn.execute(
                "SELECT * FROM weekly_plans WHERE user_id = ? ORDER BY generated_at DESC",
                (user_id,)
            )
        else:
            cursor = conn.execute(
                "SELECT * FROM weekly_plans ORDER BY generated_at DESC"
            )
        
        rows = cursor.fetchall()
        if not rows:
            print("No lesson plans found in database.")
            return None
        
        # Convert to dict
        plans = [dict(row) for row in rows]
    
    return plans[0]


def generate_objectives_for_plan(plan_id: str, output_path: str = None):
    """Generate objectives DOCX for a specific plan."""
    db = SQLiteDatabase()
    
    # Get the plan
    plan = db.get_weekly_plan(plan_id)
    
    if not plan:
        print(f"Plan {plan_id} not found.")
        return None
    
    # Get lesson_json
    lesson_json = plan.get('lesson_json')
    
    # Parse if it's a string
    if isinstance(lesson_json, str):
        try:
            lesson_json = json.loads(lesson_json)
        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to parse lesson_json: {e}")
            return None
    
    # If not in database, try to load from JSON file
    if not lesson_json:
        print(f"WARNING: No lesson_json found in database for plan {plan_id}")
        print(f"Attempting to load from JSON file...")
        
        output_file = plan.get('output_file')
        week_of = plan.get('week_of', 'Unknown')
        
        # Try output_file location first
        if output_file:
            json_file = Path(output_file).with_suffix('.json')
            if json_file.exists():
                print(f"Loading from: {json_file}")
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        lesson_json = json.load(f)
                    print("Successfully loaded lesson_json from file")
                except Exception as e:
                    print(f"Failed to load JSON file: {e}")
        
        # Try week folder
        if not lesson_json:
            from backend.file_manager import get_file_manager
            file_mgr = get_file_manager()
            week_folder = file_mgr.get_week_folder(week_of)
            
            if week_folder.exists():
                json_files = list(week_folder.glob("*.json"))
                if json_files:
                    # Use the most recent one
                    json_file = max(json_files, key=lambda p: p.stat().st_mtime)
                    print(f"Found JSON file: {json_file.name}")
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            lesson_json = json.load(f)
                        print("Successfully loaded lesson_json from file")
                    except Exception as e:
                        print(f"Failed to load JSON file: {e}")
        
        # Also try checking the output_file's parent directory (OneDrive folder)
        if not lesson_json and output_file:
            output_path = Path(output_file)
            parent_folder = output_path.parent
            if parent_folder.exists():
                json_files = list(parent_folder.glob("*.json"))
                if json_files:
                    # Use the most recent one
                    json_file = max(json_files, key=lambda p: p.stat().st_mtime)
                    print(f"Found JSON file in output folder: {json_file.name}")
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            lesson_json = json.load(f)
                        print("Successfully loaded lesson_json from output folder")
                    except Exception as e:
                        print(f"Failed to load JSON file: {e}")
        
        if not lesson_json:
            print(f"ERROR: Could not find lesson_json in database or files")
            return None
    
    # Get user info
    user_id = plan.get('user_id')
    user = db.get_user(user_id) if user_id else None
    user_name = user.get('name') if user else None
    
    # Get week_of
    week_of = plan.get('week_of', 'Unknown')
    
    # Generate output path if not provided
    if not output_path:
        from backend.file_manager import get_file_manager
        file_mgr = get_file_manager()
        week_folder = file_mgr.get_week_folder(week_of)
        week_folder.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        user_name_safe = user_name.replace(' ', '_') if user_name else 'Unknown'
        filename = f"{user_name_safe}_W{week_of}_objectives.docx"
        output_path = str(week_folder / filename)
    
    # Generate objectives DOCX
    printer = ObjectivesPrinter()
    
    try:
        result_path = printer.generate_docx(
            lesson_json,
            output_path,
            user_name=user_name,
            week_of=week_of
        )
        
        print(f"SUCCESS: Objectives DOCX generated at: {result_path}")
        return result_path
        
    except Exception as e:
        print(f"ERROR: Failed to generate objectives DOCX: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate objectives DOCX from database')
    parser.add_argument('--plan-id', type=str, help='Specific plan ID to generate')
    parser.add_argument('--user-id', type=str, help='User ID to filter plans')
    parser.add_argument('--week-of', type=str, help='Week identifier (e.g., "11-17-11-21")')
    parser.add_argument('--output', type=str, help='Output file path')
    
    args = parser.parse_args()
    
    if args.plan_id:
        # Generate for specific plan
        plan_id = args.plan_id
        print(f"Generating objectives for plan: {plan_id}")
        result = generate_objectives_for_plan(plan_id, args.output)
        
    elif args.week_of:
        # Find plan by week_of
        db = SQLiteDatabase()
        with db.get_connection() as conn:
            if args.user_id:
                cursor = conn.execute(
                    "SELECT * FROM weekly_plans WHERE user_id = ? AND week_of = ? ORDER BY generated_at DESC",
                    (args.user_id, args.week_of)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM weekly_plans WHERE week_of = ? ORDER BY generated_at DESC",
                    (args.week_of,)
                )
            rows = cursor.fetchall()
            matching_plans = [dict(row) for row in rows]
        
        if not matching_plans:
            print(f"No plans found for week: {args.week_of}")
            return
        
        # Use the most recent one
        matching_plans.sort(key=lambda p: p.get('generated_at', ''), reverse=True)
        plan = matching_plans[0]
        plan_id = plan.get('id')
        
        print(f"Generating objectives for week: {args.week_of} (plan: {plan_id})")
        result = generate_objectives_for_plan(plan_id, args.output)
        
    else:
        # Find latest plan
        plan = find_latest_plan(args.user_id)
        
        if not plan:
            return
        
        plan_id = plan.get('id')
        week_of = plan.get('week_of', 'Unknown')
        user_id = plan.get('user_id')
        
        # Get user info
        db = SQLiteDatabase()
        user = db.get_user(user_id) if user_id else None
        user_name = user.get('name') if user else 'Unknown'
        
        print(f"Found latest plan:")
        print(f"  Plan ID: {plan_id}")
        print(f"  Week: {week_of}")
        print(f"  User: {user_name}")
        print(f"  Generated: {plan.get('generated_at', 'Unknown')}")
        print()
        
        result = generate_objectives_for_plan(plan_id, args.output)
    
    if result:
        print(f"\nObjectives DOCX successfully generated!")
        print(f"File: {result}")
    else:
        print("\nFailed to generate objectives DOCX.")


if __name__ == "__main__":
    main()


"""
Script to convert lesson plan from old single-slot format to new multi-slot format.
The old format has lesson data directly in each day.
The new format has a 'slots' array in each day.
"""

import sys
from pathlib import Path
import json

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.database import get_db

def convert_day_to_slots_format(day_data: dict, slot_number: int = 1, subject: str = None, metadata: dict = None) -> dict:
    """Convert old single-slot day format to new slots array format."""
    # If already in new format, return as is
    if "slots" in day_data and isinstance(day_data["slots"], list):
        return day_data
    
    # Extract subject from metadata if not provided
    if not subject and metadata:
        subject = metadata.get("subject", "Unknown")
    
    # Create a slot from the day data
    slot = {
        "slot_number": slot_number,
        "subject": subject,
        "unit_lesson": day_data.get("unit_lesson", ""),
        "objective": day_data.get("objective", {}),
        "anticipatory_set": day_data.get("anticipatory_set", {}),
        "vocabulary_cognates": day_data.get("vocabulary_cognates", ""),
        "sentence_frames": day_data.get("sentence_frames", ""),
        "tailored_instruction": day_data.get("tailored_instruction", {}),
        "misconceptions": day_data.get("misconceptions", {}),
        "assessment": day_data.get("assessment", {}),
        "homework": day_data.get("homework", {}),
    }
    
    # Add metadata from original day data if present
    if "grade" in day_data:
        slot["grade"] = day_data["grade"]
    if "homeroom" in day_data:
        slot["homeroom"] = day_data["homeroom"]
    if "start_time" in day_data:
        slot["start_time"] = day_data["start_time"]
    if "end_time" in day_data:
        slot["end_time"] = day_data["end_time"]
    if "teacher_name" in day_data:
        slot["teacher_name"] = day_data["teacher_name"]
    
    # Return new format with slots array
    return {
        "slots": [slot]
    }


def convert_plan_format(plan_id: str, user_id: str, dry_run: bool = False):
    """Convert plan from old format to new format."""
    db = get_db(user_id=user_id)
    
    plan = db.get_weekly_plan(plan_id)
    if not plan:
        print(f"[ERROR] Plan {plan_id} not found")
        return False
    
    lesson_json = plan.lesson_json
    if isinstance(lesson_json, str):
        lesson_json = json.loads(lesson_json)
    
    print(f"\nPlan ID: {plan_id}")
    print(f"Week of: {plan.week_of}")
    print(f"Status: {plan.status}")
    
    # Check if conversion is needed
    needs_conversion = False
    if "days" in lesson_json:
        days = lesson_json["days"]
        for day_name, day_data in days.items():
            if not isinstance(day_data, dict):
                continue
            if "slots" not in day_data or not isinstance(day_data.get("slots"), list):
                needs_conversion = True
                print(f"  Day '{day_name}' needs conversion (no 'slots' array)")
                break
    
    if not needs_conversion:
        print(f"\n[OK] Plan is already in new format - no conversion needed")
        return True
    
    print(f"\n[INFO] Converting plan to new format...")
    
    # Get metadata for subject extraction
    metadata = lesson_json.get("metadata", {})
    subject = metadata.get("subject", "Unknown")
    
    # Convert each day
    converted_days = {}
    for day_name, day_data in lesson_json.get("days", {}).items():
        if not isinstance(day_data, dict):
            converted_days[day_name] = day_data
            continue
        
        # Check if already in new format
        if "slots" in day_data and isinstance(day_data["slots"], list):
            converted_days[day_name] = day_data
            print(f"  Day '{day_name}': already in new format")
        else:
            # Convert to new format
            converted_day = convert_day_to_slots_format(day_data, slot_number=1, subject=subject, metadata=metadata)
            converted_days[day_name] = converted_day
            print(f"  Day '{day_name}': converted to new format (1 slot)")
    
    # Create new lesson_json
    new_lesson_json = {
        **lesson_json,
        "days": converted_days
    }
    
    # Remove old format keys from top level if they exist
    old_keys = ["unit_lesson", "objective", "anticipatory_set", "tailored_instruction", "misconceptions", "assessment", "homework"]
    for key in old_keys:
        if key in new_lesson_json and key not in ["metadata", "days"]:
            del new_lesson_json[key]
    
    if dry_run:
        print(f"\n[DRY RUN] Would update plan with converted format")
        print(f"  Sample converted day structure:")
        if converted_days:
            first_day_name = list(converted_days.keys())[0]
            first_day = converted_days[first_day_name]
            print(f"    {first_day_name}: has 'slots' array with {len(first_day.get('slots', []))} slot(s)")
        return True
    
    # Update plan in database
    print(f"\n[UPDATING] Updating plan in database...")
    db.update_weekly_plan(plan_id, lesson_json=new_lesson_json)
    print(f"[OK] Plan updated successfully!")
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert lesson plan to new format")
    parser.add_argument("--plan-id", required=True, help="Plan ID to convert")
    parser.add_argument("--user-id", required=True, help="User ID")
    parser.add_argument("--dry-run", action="store_true", help="Dry run - don't update database")
    
    args = parser.parse_args()
    
    convert_plan_format(args.plan_id, args.user_id, dry_run=args.dry_run)


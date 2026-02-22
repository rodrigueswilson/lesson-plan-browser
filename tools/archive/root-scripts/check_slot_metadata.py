"""Check slot metadata (grade, homeroom) in lesson_json for a plan."""
import sys
import json
from backend.database import get_db

def check_slot_metadata(plan_id: str):
    """Check if slots have their own grade/homeroom values."""
    print(f"Checking slot metadata for plan: {plan_id}")
    print("=" * 80)
    
    # Find the plan
    db = get_db()
    plan = db.get_weekly_plan(plan_id)
    
    if not plan:
        from backend.supabase_database import get_project1_db
        db = get_project1_db()
        plan = db.get_weekly_plan(plan_id)
    
    if not plan:
        from backend.supabase_database import get_project2_db
        db = get_project2_db()
        plan = db.get_weekly_plan(plan_id)
    
    if not plan:
        print(f"ERROR: Plan {plan_id} not found")
        return
    
    print(f"Plan: {plan.id}")
    print(f"User: {plan.user_id}")
    print(f"Week: {plan.week_of}")
    print()
    
    # Get lesson_json
    lesson_json = plan.lesson_json
    if isinstance(lesson_json, str):
        try:
            lesson_json = json.loads(lesson_json)
        except:
            print("ERROR: Could not parse lesson_json")
            return
    
    if not lesson_json or "days" not in lesson_json:
        print("ERROR: lesson_json is empty or missing 'days' key")
        return
    
    # Check metadata
    metadata = lesson_json.get("metadata", {})
    print("Lesson-level metadata:")
    print(f"  Grade: {metadata.get('grade', 'N/A')}")
    print(f"  Homeroom: {metadata.get('homeroom', 'N/A')}")
    print(f"  Room: {metadata.get('room', 'N/A')}")
    print()
    
    # Check each day and slot
    days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    
    for day in days:
        day_data = lesson_json.get("days", {}).get(day, {})
        if not day_data:
            continue
        
        if "slots" in day_data and isinstance(day_data.get("slots"), list):
            # Multi-slot structure
            slots = day_data["slots"]
            print(f"{day.capitalize()}:")
            for slot_data in slots:
                if not isinstance(slot_data, dict):
                    continue
                slot_number = slot_data.get("slot_number")
                if slot_number is None:
                    continue
                
                slot_grade = slot_data.get("grade")
                slot_homeroom = slot_data.get("homeroom")
                slot_room = slot_data.get("room")
                slot_subject = slot_data.get("subject")
                
                print(f"  Slot {slot_number} ({slot_subject}):")
                print(f"    Grade: {slot_grade if slot_grade else 'MISSING (will use lesson-level: ' + str(metadata.get('grade', 'N/A')) + ')'}")
                print(f"    Homeroom: {slot_homeroom if slot_homeroom else 'MISSING (will use lesson-level: ' + str(metadata.get('homeroom', 'N/A')) + ')'}")
                print(f"    Room: {slot_room if slot_room else 'MISSING (will use lesson-level: ' + str(metadata.get('room', 'N/A')) + ')'}")
        else:
            # Single-slot structure
            slot_number = day_data.get("slot_number")
            if slot_number is not None:
                slot_grade = day_data.get("grade")
                slot_homeroom = day_data.get("homeroom")
                slot_room = day_data.get("room")
                slot_subject = day_data.get("subject")
                
                print(f"{day.capitalize()} Slot {slot_number} ({slot_subject}):")
                print(f"  Grade: {slot_grade if slot_grade else 'MISSING (will use lesson-level: ' + str(metadata.get('grade', 'N/A')) + ')'}")
                print(f"  Homeroom: {slot_homeroom if slot_homeroom else 'MISSING (will use lesson-level: ' + str(metadata.get('homeroom', 'N/A')) + ')'}")
                print(f"  Room: {slot_room if slot_room else 'MISSING (will use lesson-level: ' + str(metadata.get('room', 'N/A')) + ')'}")

if __name__ == "__main__":
    plan_id = sys.argv[1] if len(sys.argv) > 1 else "plan_20251228152714"
    check_slot_metadata(plan_id)

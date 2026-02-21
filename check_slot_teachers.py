"""Check if slot-specific teacher fields are present in lesson JSON."""
import sys
import json
from backend.database import get_db

def check_slot_teachers(plan_id: str, user_id: str):
    """Check teacher fields in slots."""
    print(f"Checking slot teachers for plan: {plan_id}")
    print("=" * 80)
    
    # Get plan
    db = get_db(user_id=user_id)
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
    
    # Get lesson_json
    lesson_json = plan.lesson_json
    if isinstance(lesson_json, str):
        try:
            lesson_json = json.loads(lesson_json)
        except:
            print("ERROR: Could not parse lesson_json")
            return
    
    # Check metadata
    metadata = lesson_json.get("metadata", {})
    print("\nMETADATA (lesson-level):")
    print(f"  teacher_name: {metadata.get('teacher_name')}")
    print(f"  primary_teacher_name: {metadata.get('primary_teacher_name')}")
    print(f"  primary_teacher_first_name: {metadata.get('primary_teacher_first_name')}")
    print(f"  primary_teacher_last_name: {metadata.get('primary_teacher_last_name')}")
    
    # Check each day's slots
    days = lesson_json.get("days", {})
    day_names = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    
    for day_name in day_names:
        if day_name not in days:
            continue
        
        day_data = days[day_name]
        slots = day_data.get("slots", [])
        
        if not isinstance(slots, list) or len(slots) == 0:
            continue
        
        print(f"\n{day_name.upper()}:")
        for slot in slots:
            slot_num = slot.get("slot_number")
            subject = slot.get("subject")
            print(f"  Slot {slot_num} ({subject}):")
            print(f"    teacher_name: {slot.get('teacher_name')}")
            print(f"    primary_teacher_name: {slot.get('primary_teacher_name')}")
            print(f"    primary_teacher_first_name: {slot.get('primary_teacher_first_name')}")
            print(f"    primary_teacher_last_name: {slot.get('primary_teacher_last_name')}")
            
            # Test get_teacher_name
            from backend.utils.metadata_utils import get_teacher_name
            teacher = get_teacher_name(metadata, slot=slot)
            print(f"    get_teacher_name() result: {teacher}")

if __name__ == "__main__":
    plan_id = sys.argv[1] if len(sys.argv) > 1 else "plan_20251228152714"
    user_id = sys.argv[2] if len(sys.argv) > 2 else "04fe8898-cb89-4a73-affb-64a97a98f820"
    check_slot_teachers(plan_id, user_id)

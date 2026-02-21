"""Check if sentence frames are using the same sorted slots as objectives."""
import sys
import json
from backend.database import get_db
from backend.services.sorting_utils import sort_slots

def check_sentence_frames_order(plan_id: str, user_id: str):
    """Check slot order for sentence frames vs objectives."""
    print(f"Checking slot order for plan: {plan_id}")
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
    
    # Check each day
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
        print(f"  Raw slots order: {[s.get('slot_number') for s in slots]}")
        print(f"  Raw slots with times: {[(s.get('slot_number'), s.get('start_time', 'N/A')) for s in slots]}")
        
        # Sort using sort_slots
        sorted_slots = sort_slots(slots)
        print(f"  Sorted slots order: {[s.get('slot_number') for s in sorted_slots]}")
        print(f"  Sorted slots with times: {[(s.get('slot_number'), s.get('start_time', 'N/A')) for s in sorted_slots]}")
        
        # Check if order changed
        raw_order = [s.get('slot_number') for s in slots]
        sorted_order = [s.get('slot_number') for s in sorted_slots]
        if raw_order != sorted_order:
            print(f"  *** ORDER CHANGED AFTER SORTING ***")
        else:
            print(f"  Order unchanged (already sorted)")

if __name__ == "__main__":
    plan_id = sys.argv[1] if len(sys.argv) > 1 else "plan_20251228152714"
    user_id = sys.argv[2] if len(sys.argv) > 2 else "04fe8898-cb89-4a73-affb-64a97a98f820"
    check_sentence_frames_order(plan_id, user_id)

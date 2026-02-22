"""Check slot order for each day in lesson_json."""
import sys
import json
from backend.database import get_db
from backend.services.sorting_utils import sort_slots

def check_slot_order(plan_id: str):
    """Check slot order for each day."""
    print(f"Checking slot order for plan: {plan_id}")
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
    
    # Check each day
    days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    
    for day in days:
        day_data = lesson_json.get("days", {}).get(day, {})
        if not day_data:
            continue
        
        if "slots" in day_data and isinstance(day_data.get("slots"), list):
            slots = day_data["slots"]
            
            # Show original order
            print(f"\n{day.upper()}:")
            print(f"  Original order: {[s.get('slot_number') for s in slots]}")
            
            # Show sorted order
            sorted_slots = sort_slots(slots)
            print(f"  Sorted order: {[s.get('slot_number') for s in sorted_slots]}")
            
            # Show details
            print(f"  Slot details:")
            for slot in sorted_slots:
                slot_num = slot.get("slot_number")
                start_time = slot.get("start_time", "N/A")
                subject = slot.get("subject", "N/A")
                print(f"    Slot {slot_num} ({subject}): start_time={start_time}")

if __name__ == "__main__":
    plan_id = sys.argv[1] if len(sys.argv) > 1 else "plan_20251228152714"
    check_slot_order(plan_id)

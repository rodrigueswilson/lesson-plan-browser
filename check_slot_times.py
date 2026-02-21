"""Check slot start_time and end_time values in lesson_json."""
import sys
import json
from backend.database import get_db

def check_slot_times(plan_id: str):
    """Check if slots have start_time/end_time values."""
    print(f"Checking slot times for plan: {plan_id}")
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
            print(f"\n{day.capitalize()}:")
            for slot_data in slots:
                if not isinstance(slot_data, dict):
                    continue
                slot_number = slot_data.get("slot_number")
                if slot_number is None:
                    continue
                
                start_time = slot_data.get("start_time")
                end_time = slot_data.get("end_time")
                time_field = slot_data.get("time")
                
                print(f"  Slot {slot_number} ({slot_data.get('subject')}):")
                print(f"    start_time: {start_time}")
                print(f"    end_time: {end_time}")
                print(f"    time field: {time_field}")

if __name__ == "__main__":
    plan_id = sys.argv[1] if len(sys.argv) > 1 else "plan_20251228152714"
    check_slot_times(plan_id)

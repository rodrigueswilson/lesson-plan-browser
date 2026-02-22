"""Check mismatch between lesson_json slots and schedule for Wednesday."""
import sys
import json
from backend.database import get_db

def check_wednesday_mismatch(plan_id: str, user_id: str):
    """Check if Wednesday slots match schedule."""
    print(f"Checking Wednesday slot mismatch for plan: {plan_id}")
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
    
    # Get schedule
    schedule_entries = db.get_user_schedule(user_id)
    wednesday_schedule = [e for e in schedule_entries if e.day_of_week.lower() == "wednesday"]
    wednesday_schedule.sort(key=lambda x: x.start_time)
    
    print("\nWEDNESDAY SCHEDULE (by time):")
    for entry in wednesday_schedule:
        print(f"  {entry.start_time}-{entry.end_time}: Slot {entry.slot_number} ({entry.subject})")
    
    # Get lesson_json slots for Wednesday
    wednesday_slots = lesson_json.get("days", {}).get("wednesday", {}).get("slots", [])
    
    print("\nWEDNESDAY LESSON_JSON SLOTS (current order):")
    for slot in wednesday_slots:
        slot_num = slot.get("slot_number")
        subject = slot.get("subject")
        start_time = slot.get("start_time", "N/A")
        print(f"  Slot {slot_num} ({subject}): start_time={start_time}")
    
    print("\nEXPECTED ORDER (from schedule):")
    # Match lesson_json slots to schedule entries by subject/time
    matched = []
    for entry in wednesday_schedule:
        # Find matching slot in lesson_json
        for slot in wednesday_slots:
            if (slot.get("subject", "").lower() == entry.subject.lower() and 
                slot.get("start_time") == entry.start_time):
                matched.append((entry.start_time, slot))
                break
    
    for start_time, slot in sorted(matched, key=lambda x: x[0]):
        print(f"  {start_time}: Slot {slot.get('slot_number')} ({slot.get('subject')})")

if __name__ == "__main__":
    plan_id = sys.argv[1] if len(sys.argv) > 1 else "plan_20251228152714"
    user_id = sys.argv[2] if len(sys.argv) > 2 else "04fe8898-cb89-4a73-affb-64a97a98f820"
    check_wednesday_mismatch(plan_id, user_id)

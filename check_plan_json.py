"""Check if lesson_json in the plan has vocabulary_cognates and sentence_frames."""
import sys
import json
from backend.database import get_db

def check_plan_json(plan_id: str):
    """Check if lesson_json has vocabulary_cognates and sentence_frames."""
    print(f"Checking lesson_json for plan: {plan_id}")
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
    
    # Check each day and slot
    days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    slots_with_vocab = 0
    slots_with_frames = 0
    slots_missing_both = 0
    
    for day in days:
        day_data = lesson_json.get("days", {}).get(day, {})
        if not day_data:
            continue
        
        if "slots" in day_data and isinstance(day_data.get("slots"), list):
            # Multi-slot structure
            slots = day_data["slots"]
            for slot_data in slots:
                if not isinstance(slot_data, dict):
                    continue
                slot_number = slot_data.get("slot_number")
                if slot_number is None:
                    continue
                
                has_vocab = bool(slot_data.get("vocabulary_cognates"))
                has_frames = bool(slot_data.get("sentence_frames"))
                
                if has_vocab:
                    slots_with_vocab += 1
                    vocab_count = len(slot_data.get("vocabulary_cognates", []))
                    print(f"{day.capitalize()} Slot {slot_number}: HAS vocabulary ({vocab_count} items)")
                if has_frames:
                    slots_with_frames += 1
                    frames_count = len(slot_data.get("sentence_frames", []))
                    print(f"{day.capitalize()} Slot {slot_number}: HAS sentence_frames ({frames_count} items)")
                if not has_vocab and not has_frames:
                    slots_missing_both += 1
                    print(f"{day.capitalize()} Slot {slot_number}: MISSING both vocabulary and frames")
        else:
            # Single-slot structure
            slot_number = day_data.get("slot_number")
            if slot_number is not None:
                has_vocab = bool(day_data.get("vocabulary_cognates"))
                has_frames = bool(day_data.get("sentence_frames"))
                
                if has_vocab:
                    slots_with_vocab += 1
                    vocab_count = len(day_data.get("vocabulary_cognates", []))
                    print(f"{day.capitalize()} Slot {slot_number}: HAS vocabulary ({vocab_count} items)")
                if has_frames:
                    slots_with_frames += 1
                    frames_count = len(day_data.get("sentence_frames", []))
                    print(f"{day.capitalize()} Slot {slot_number}: HAS sentence_frames ({frames_count} items)")
                if not has_vocab and not has_frames:
                    slots_missing_both += 1
                    print(f"{day.capitalize()} Slot {slot_number}: MISSING both vocabulary and frames")
    
    print()
    print("=" * 80)
    print("SUMMARY:")
    print(f"  Slots with vocabulary_cognates: {slots_with_vocab}")
    print(f"  Slots with sentence_frames: {slots_with_frames}")
    print(f"  Slots missing both: {slots_missing_both}")
    
    if slots_missing_both > 0:
        print()
        print("ISSUE: Some slots are missing vocabulary_cognates and sentence_frames in lesson_json")
        print("  - Enrichment should try to get this from lesson steps")
        print("  - But lesson steps don't exist in database")
        print("  - So enrichment cannot help")

if __name__ == "__main__":
    plan_id = sys.argv[1] if len(sys.argv) > 1 else "plan_20251229174144"
    check_plan_json(plan_id)

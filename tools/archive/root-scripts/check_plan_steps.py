"""Check database for lesson steps for a specific plan."""
import sys
from backend.database import get_db
from backend.database_interface import DatabaseInterface

def check_plan_steps(plan_id: str):
    """Check if lesson steps exist for a plan and if they have vocabulary/frames."""
    print(f"Checking lesson steps for plan: {plan_id}")
    print("=" * 80)
    
    # First, find the plan to get the user_id
    db = get_db()
    plan = db.get_weekly_plan(plan_id)
    
    if not plan:
        # Try project1
        from backend.supabase_database import get_project1_db
        db = get_project1_db()
        plan = db.get_weekly_plan(plan_id)
    
    if not plan:
        # Try project2
        from backend.supabase_database import get_project2_db
        db = get_project2_db()
        plan = db.get_weekly_plan(plan_id)
    
    if not plan:
        print(f"ERROR: Plan {plan_id} not found in any database")
        return
    
    print(f"Found plan:")
    print(f"  Plan ID: {plan.id}")
    print(f"  User ID: {plan.user_id}")
    print(f"  Week of: {plan.week_of}")
    print(f"  Status: {plan.status}")
    print()
    
    # Get the correct database for this user
    db_for_plan = get_db(user_id=plan.user_id)
    
    # Check all days and slots
    days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    slots = [1, 2, 3, 4, 5, 6]
    
    total_steps = 0
    vocab_steps_found = 0
    frames_steps_found = 0
    vocab_steps_with_data = 0
    frames_steps_with_data = 0
    
    for day in days:
        for slot in slots:
            try:
                steps = db_for_plan.get_lesson_steps(plan_id, day_of_week=day, slot_number=slot)
                if steps:
                    total_steps += len(steps)
                    print(f"{day.capitalize()} Slot {slot}: {len(steps)} steps")
                    
                    for step in steps:
                        step_name = getattr(step, 'step_name', 'unknown')
                        has_vocab_attr = hasattr(step, 'vocabulary_cognates')
                        has_frames_attr = hasattr(step, 'sentence_frames')
                        
                        vocab_value = getattr(step, 'vocabulary_cognates', None)
                        frames_value = getattr(step, 'sentence_frames', None)
                        
                        vocab_is_truthy = bool(vocab_value)
                        frames_is_truthy = bool(frames_value)
                        
                        if step_name == "Vocabulary / Cognate Awareness":
                            vocab_steps_found += 1
                            if vocab_is_truthy:
                                vocab_steps_with_data += 1
                                vocab_count = len(vocab_value) if isinstance(vocab_value, (list, dict)) else 1
                                print(f"  ✓ Vocabulary step found with {vocab_count} items")
                            else:
                                print(f"  ✗ Vocabulary step found but NO DATA (value: {vocab_value})")
                        
                        if step_name == "Sentence Frames / Stems / Questions":
                            frames_steps_found += 1
                            if frames_is_truthy:
                                frames_steps_with_data += 1
                                frames_count = len(frames_value) if isinstance(frames_value, (list, dict)) else 1
                                print(f"  ✓ Sentence Frames step found with {frames_count} items")
                            else:
                                print(f"  ✗ Sentence Frames step found but NO DATA (value: {frames_value})")
            except Exception as e:
                print(f"  ERROR querying {day} slot {slot}: {e}")
    
    print()
    print("=" * 80)
    print("SUMMARY:")
    print(f"  Total steps found: {total_steps}")
    print(f"  Vocabulary steps found: {vocab_steps_found}")
    print(f"  Vocabulary steps with data: {vocab_steps_with_data}")
    print(f"  Sentence Frames steps found: {frames_steps_found}")
    print(f"  Sentence Frames steps with data: {frames_steps_with_data}")
    
    if vocab_steps_found == 0 and frames_steps_found == 0:
        print()
        print("WARNING: No vocabulary or sentence frames steps found!")
        print("   This means the enrichment function cannot extract data from steps.")
    elif vocab_steps_found > 0 and vocab_steps_with_data == 0:
        print()
        print("WARNING: Vocabulary steps exist but have no data!")
    elif frames_steps_found > 0 and frames_steps_with_data == 0:
        print()
        print("WARNING: Sentence frames steps exist but have no data!")

if __name__ == "__main__":
    plan_id = sys.argv[1] if len(sys.argv) > 1 else "plan_20251229174144"
    check_plan_steps(plan_id)

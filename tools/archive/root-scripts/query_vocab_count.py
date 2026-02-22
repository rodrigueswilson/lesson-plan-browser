"""
Query database to count Vocabulary / Cognate Awareness sections in W49 for Wilson Rodrigues.
"""
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database import get_db
from backend.config import settings

def query_vocab_count():
    """Query database for Vocabulary / Cognate Awareness count in W49 for Wilson Rodrigues."""
    
    # Use the known user ID for Wilson Rodrigues
    user_id = "04fe8898-cb89-4a73-affb-64a97a98f820"
    
    # Get database connection - use user_id to get the correct database (Supabase project1)
    db = get_db(user_id=user_id)
    
    # Get user
    user = db.get_user(user_id)
    
    if not user:
        print(f"ERROR: User with ID '{user_id}' not found in database")
        return
    
    print(f"Found user: {user.name} (ID: {user.id})")
    
    # Get all plans for this user
    all_plans = db.get_user_plans(user_id)
    
    # Filter for W49 plans (week containing 12/01-12/05 or week 49)
    w49_plans = []
    for plan in all_plans:
        week_of = plan.week_of or ""
        week_of_upper = week_of.upper()
        # Check for various formats: 12/01, 12/05, W49, Week 49, etc.
        if ("12/01" in week_of or "12/05" in week_of or 
            "W49" in week_of_upper or "WEEK 49" in week_of_upper or
            "12-01" in week_of or "12-05" in week_of or
            (week_of and "49" in week_of and ("12" in week_of or "dec" in week_of_upper))):
            w49_plans.append(plan)
    
    # Sort by generated_at descending
    w49_plans.sort(key=lambda p: p.generated_at if p.generated_at else datetime.min, reverse=True)
    all_plans.sort(key=lambda p: p.generated_at if p.generated_at else datetime.min, reverse=True)
    
    if not w49_plans:
        print(f"\nNo W49 plans found for user {user.name}")
        print(f"Total plans for user: {len(all_plans)}")
        if all_plans:
            print("\nRecent plans (showing all to help identify W49):")
            for plan in all_plans[:20]:
                print(f"  - {plan.id}: week_of='{plan.week_of}', generated_at={plan.generated_at}")
        
        # If no W49 found, use the most recent plan
        if all_plans:
            print(f"\nUsing most recent plan instead: {all_plans[0].id}")
            most_recent_w49 = all_plans[0]
        else:
            return
    else:
        # Get the most recent W49 plan
        most_recent_w49 = w49_plans[0]
    
    print(f"\nMost recent W49 plan: {most_recent_w49.id}")
    print(f"  week_of: {most_recent_w49.week_of}")
    print(f"  generated_at: {most_recent_w49.generated_at}")
    
    # Check lesson_json for vocabulary_cognates
    import json
    lesson_json = most_recent_w49.lesson_json
    if isinstance(lesson_json, str):
        try:
            lesson_json = json.loads(lesson_json)
        except:
            lesson_json = {}
    
    vocab_count_in_json = 0
    frames_count_in_json = 0
    
    if lesson_json and "days" in lesson_json:
        for day_name, day_data in lesson_json["days"].items():
            if isinstance(day_data, dict):
                # Check for slots structure
                slots = day_data.get("slots", [])
                if isinstance(slots, list) and slots:
                    for slot in slots:
                        if isinstance(slot, dict):
                            if slot.get("vocabulary_cognates"):
                                vocab_count_in_json += 1
                            if slot.get("sentence_frames"):
                                frames_count_in_json += 1
                else:
                    # Single slot structure
                    if day_data.get("vocabulary_cognates"):
                        vocab_count_in_json += 1
                    if day_data.get("sentence_frames"):
                        frames_count_in_json += 1
    
    print(f"\nVocabulary / Cognate Awareness in lesson_json: {vocab_count_in_json} slots")
    print(f"Sentence Frames in lesson_json: {frames_count_in_json} slots")
    
    # Query for Vocabulary / Cognate Awareness steps
    # Get all steps for this plan
    try:
        all_steps = db.get_lesson_steps(most_recent_w49.id)
    except Exception as e:
        print(f"\nCould not query lesson steps (table may not exist): {e}")
        all_steps = []
    
    vocab_steps = [s for s in all_steps if s.step_name == "Vocabulary / Cognate Awareness"]
    
    print(f"\nVocabulary / Cognate Awareness steps found: {len(vocab_steps)}")
    
    # Group by day and slot for better reporting
    by_day_slot = {}
    for step in vocab_steps:
        key = f"{step.day_of_week}_slot{step.slot_number}"
        if key not in by_day_slot:
            by_day_slot[key] = []
        by_day_slot[key].append(step)
    
    print(f"\nBreakdown by day and slot:")
    for key in sorted(by_day_slot.keys()):
        steps = by_day_slot[key]
        print(f"  {key}: {len(steps)} step(s)")
        for step in steps:
            vocab_count = len(step.vocabulary_cognates) if step.vocabulary_cognates else 0
            print(f"    - Step {step.step_number}: {vocab_count} vocabulary pairs")
    
    # Also check for Sentence Frames for comparison
    frames_steps = [s for s in all_steps if s.step_name == "Sentence Frames / Stems / Questions"]
    print(f"\nSentence Frames / Stems / Questions steps found: {len(frames_steps)}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY for W49 (most recent plan: {most_recent_w49.id})")
    print(f"{'='*60}")
    print(f"Vocabulary / Cognate Awareness in JSON: {vocab_count_in_json} slots")
    print(f"Vocabulary / Cognate Awareness in database steps: {len(vocab_steps)} sections")
    print(f"Sentence Frames in JSON: {frames_count_in_json} slots")
    print(f"Sentence Frames in database steps: {len(frames_steps)} sections")
    print(f"Expected: 25 sections (5 days × 5 slots)")
    print(f"{'='*60}")

if __name__ == "__main__":
    query_vocab_count()

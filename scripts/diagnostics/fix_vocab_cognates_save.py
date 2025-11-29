"""
Fix vocabulary_cognates not being saved by ensuring it's explicitly set.
Since direct save works, the issue might be with how vocabulary_cognates is extracted
or passed during actual step generation. This script will update existing steps.
"""
import sys
from pathlib import Path
import uuid

sys.path.append(str(Path(__file__).parent))

from backend.database import get_db
from backend.schema import LessonStep
from sqlmodel import Session, select, update

plan_id = "plan_20251122160826"
db = get_db()

# Get plan to extract vocabulary_cognates
plan = db.get_weekly_plan(plan_id)
lesson_json = plan.lesson_json
monday = lesson_json.get("days", {}).get("monday", {})
slots = monday.get("slots", [])
slot1 = next((s for s in slots if s.get("slot_number") == 1), None)

if not slot1:
    print("[FAIL] Slot 1 not found")
    sys.exit(1)

vocabulary_cognates = slot1.get("vocabulary_cognates", [])
print(f"Found vocabulary_cognates: {len(vocabulary_cognates)} items")

# Find vocabulary step and update it
with Session(db.engine) as session:
    # Find vocabulary step
    query = select(LessonStep).where(
        LessonStep.lesson_plan_id == plan_id,
        LessonStep.day_of_week == "monday",
        LessonStep.slot_number == 1,
        LessonStep.step_name.like("%Vocabulary%")
    )
    vocab_step = session.exec(query).first()
    
    if vocab_step:
        print(f"\nFound vocabulary step: {vocab_step.step_name} (ID: {vocab_step.id})")
        print(f"Current vocabulary_cognates: {vocab_step.vocabulary_cognates}")
        
        # Update with correct vocabulary_cognates
        vocab_step.vocabulary_cognates = vocabulary_cognates
        session.add(vocab_step)
        session.commit()
        session.refresh(vocab_step)
        
        print(f"\nUpdated vocabulary_cognates:")
        print(f"  Type: {type(vocab_step.vocabulary_cognates)}")
        print(f"  Length: {len(vocab_step.vocabulary_cognates) if isinstance(vocab_step.vocabulary_cognates, list) else 'N/A'}")
        print(f"  Value: {vocab_step.vocabulary_cognates}")
        
        if vocab_step.vocabulary_cognates and isinstance(vocab_step.vocabulary_cognates, list) and len(vocab_step.vocabulary_cognates) > 0:
            print(f"\n[SUCCESS] vocabulary_cognates updated successfully!")
        else:
            print(f"\n[FAIL] vocabulary_cognates still None or empty after update")
    else:
        print(f"\n[FAIL] Vocabulary step not found")
        sys.exit(1)

# Verify via API-style retrieval
print(f"\nVerifying via database retrieval...")
steps = db.get_lesson_steps(plan_id, day_of_week="monday", slot_number=1)
vocab_step_retrieved = next((s for s in steps if "vocabulary" in s.step_name.lower()), None)

if vocab_step_retrieved:
    vocab_retrieved = vocab_step_retrieved.vocabulary_cognates
    if vocab_retrieved and isinstance(vocab_retrieved, list) and len(vocab_retrieved) > 0:
        print(f"[OK] vocabulary_cognates retrieved correctly: {len(vocab_retrieved)} items")
    else:
        print(f"[FAIL] vocabulary_cognates not retrieved correctly: {vocab_retrieved}")


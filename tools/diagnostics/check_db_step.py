"""
Check what's actually in the database LessonStep for vocabulary step.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from backend.database import get_db

plan_id = "plan_20251122160826"

db = get_db()
steps = db.get_lesson_steps(plan_id, day_of_week="monday", slot_number=1)

print(f"Found {len(steps)} steps in database\n")

vocab_step = None
for step in steps:
    step_name = step.step_name if hasattr(step, 'step_name') else step.get('step_name', '')
    if "vocabulary" in step_name.lower() or "cognate" in step_name.lower():
        vocab_step = step
        print(f"Found vocabulary step: {step_name}")
        break

if vocab_step:
    print(f"\nVocabulary step attributes:")
    print(f"  Has vocabulary_cognates attribute: {hasattr(vocab_step, 'vocabulary_cognates')}")
    
    if hasattr(vocab_step, 'vocabulary_cognates'):
        vocab_data = vocab_step.vocabulary_cognates
        print(f"  vocabulary_cognates type: {type(vocab_data)}")
        print(f"  vocabulary_cognates value: {vocab_data}")
        print(f"  vocabulary_cognates is list: {isinstance(vocab_data, list)}")
        if isinstance(vocab_data, list):
            print(f"  vocabulary_cognates length: {len(vocab_data)}")
            if len(vocab_data) > 0:
                print(f"  First item: {vocab_data[0]}")
    else:
        print(f"  [FAIL] vocabulary_cognates attribute not found on step object")
        
        # Try to access as dict
        if isinstance(vocab_step, dict):
            vocab_data = vocab_step.get('vocabulary_cognates')
            print(f"  vocabulary_cognates (as dict): {vocab_data}")
        elif hasattr(vocab_step, '__dict__'):
            print(f"  Step attributes: {list(vocab_step.__dict__.keys())}")
else:
    print("[FAIL] Vocabulary step not found")

# Also check all steps
print(f"\n\nAll steps in database:")
for i, step in enumerate(steps):
    step_name = step.step_name if hasattr(step, 'step_name') else step.get('step_name', '')
    has_vocab_attr = hasattr(step, 'vocabulary_cognates')
    vocab_val = getattr(step, 'vocabulary_cognates', None) if has_vocab_attr else None
    print(f"  Step {i+1}: {step_name}")
    print(f"    Has vocabulary_cognates: {has_vocab_attr}")
    if vocab_val:
        print(f"    vocabulary_cognates: {type(vocab_val)} = {len(vocab_val) if isinstance(vocab_val, list) else vocab_val}")


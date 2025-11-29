"""
Check what steps are generated for a specific plan and why vocabulary/frames steps are missing.
"""
import sys
import requests
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from backend.database import get_db

API_BASE = "http://localhost:8000/api"

plan_id = "6dc1bd72-9481-44f4-9ee7-123c7dc2d1b0"
user_id = "04fe8898-cb89-4a73-affb-64a97a98f820"

print("="*80)
print(f"CHECKING PLAN: {plan_id}")
print("="*80)

# Get plan detail
detail_response = requests.get(
    f"{API_BASE}/plans/{plan_id}",
    headers={"X-Current-User-Id": user_id}
)

if detail_response.status_code == 200:
    detail = detail_response.json()
    lesson_json = detail.get("lesson_json", {})
    
    if lesson_json:
        print("\n[OK] Plan has lesson_json")
        
        # Check Monday slot 1
        days = lesson_json.get("days", {})
        monday = days.get("monday", {})
        slots = monday.get("slots", [])
        slot1 = next((s for s in slots if s.get("slot_number") == 1), None)
        
        if slot1:
            print(f"\n[OK] Slot 1 found")
            vocab = slot1.get("vocabulary_cognates", [])
            frames = slot1.get("sentence_frames", [])
            
            print(f"\nVocabulary/Frames in lesson_json:")
            print(f"  vocabulary_cognates type: {type(vocab)}")
            print(f"  vocabulary_cognates is list: {isinstance(vocab, list)}")
            print(f"  vocabulary_cognates length: {len(vocab) if isinstance(vocab, list) else 'N/A'}")
            print(f"  vocabulary_cognates value: {vocab}")
            
            print(f"\n  sentence_frames type: {type(frames)}")
            print(f"  sentence_frames is list: {isinstance(frames, list)}")
            print(f"  sentence_frames length: {len(frames) if isinstance(frames, list) else 'N/A'}")
            print(f"  sentence_frames value: {frames}")
            
            if vocab and isinstance(vocab, list) and len(vocab) > 0:
                print(f"\n[OK] vocabulary_cognates found: {len(vocab)} items")
            else:
                print(f"\n[FAIL] vocabulary_cognates missing or empty")
            
            if frames and isinstance(frames, list) and len(frames) > 0:
                print(f"\n[OK] sentence_frames found: {len(frames)} items")
            else:
                print(f"\n[FAIL] sentence_frames missing or empty")
        else:
            print(f"\n[FAIL] Slot 1 not found")
    else:
        print(f"\n[FAIL] Plan has no lesson_json")
else:
    print(f"\n[FAIL] Cannot get plan detail: {detail_response.status_code}")

# Get existing steps
print(f"\n{'='*80}")
print("EXISTING STEPS IN DATABASE")
print("="*80)

db = get_db()
steps = db.get_lesson_steps(plan_id, day_of_week="monday", slot_number=1)

print(f"\nFound {len(steps)} steps in database:")
for i, step in enumerate(steps):
    print(f"  {i+1}. {step.step_name} (type: {step.content_type})")
    if "vocabulary" in step.step_name.lower():
        print(f"      vocabulary_cognates: {step.vocabulary_cognates}")
    if step.content_type == "sentence_frames":
        print(f"      sentence_frames: {step.sentence_frames}")

# Try generating steps
print(f"\n{'='*80}")
print("GENERATING STEPS")
print("="*80)

gen_response = requests.post(
    f"{API_BASE}/lesson-steps/generate?plan_id={plan_id}&day=monday&slot=1",
    headers={"X-Current-User-Id": user_id},
    timeout=30
)

if gen_response.status_code == 200:
    generated_steps = gen_response.json()
    print(f"\nGenerated {len(generated_steps)} steps:")
    for i, step in enumerate(generated_steps):
        print(f"  {i+1}. {step.get('step_name')} (type: {step.get('content_type')})")
        if "vocabulary" in step.get('step_name', '').lower():
            vocab_data = step.get('vocabulary_cognates')
            print(f"      vocabulary_cognates: {vocab_data} (type: {type(vocab_data)}, length: {len(vocab_data) if isinstance(vocab_data, list) else 'N/A'})")
        if step.get('content_type') == 'sentence_frames':
            frames_data = step.get('sentence_frames')
            print(f"      sentence_frames: {frames_data} (type: {type(frames_data)}, length: {len(frames_data) if isinstance(frames_data, list) else 'N/A'})")
else:
    print(f"\n[FAIL] Cannot generate steps: {gen_response.status_code}")
    print(gen_response.text[:500])

print("\n" + "="*80)


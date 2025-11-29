"""
Check what happens during step generation - specifically what slot_data contains.
"""
import requests
import json

API_BASE = "http://localhost:8000/api"

# Get plan
users_response = requests.get(f"{API_BASE}/users")
users = users_response.json()
user_id = next(u["id"] for u in users if "Wilson" in u.get("name", ""))

plans_response = requests.get(
    f"{API_BASE}/users/{user_id}/plans",
    headers={"X-Current-User-Id": user_id}
)
plans = plans_response.json()
plan = next(p for p in plans if "11-17" in p.get("week_of", ""))
plan_id = plan["id"]

print(f"Plan ID: {plan_id}")
print(f"User ID: {user_id}")
print(f"Week: {plan.get('week_of')}")

# Get plan detail to see slot_data
detail_response = requests.get(
    f"{API_BASE}/plans/{plan_id}",
    headers={"X-Current-User-Id": user_id}
)
detail = detail_response.json()
lesson_json = detail["lesson_json"]

# Check Monday slot 1
monday = lesson_json.get("days", {}).get("monday", {})
slots = monday.get("slots", [])
slot1 = next((s for s in slots if s.get("slot_number") == 1), None)

if slot1:
    print(f"\nSlot 1 found:")
    print(f"  slot_number: {slot1.get('slot_number')}")
    print(f"  vocabulary_cognates type: {type(slot1.get('vocabulary_cognates'))}")
    print(f"  vocabulary_cognates value: {slot1.get('vocabulary_cognates')}")
    print(f"  vocabulary_cognates length: {len(slot1.get('vocabulary_cognates', []))}")
    print(f"  sentence_frames type: {type(slot1.get('sentence_frames'))}")
    print(f"  sentence_frames value: {slot1.get('sentence_frames')}")
    print(f"  sentence_frames length: {len(slot1.get('sentence_frames', []))}")
    print(f"\nAll keys in slot1: {list(slot1.keys())[:30]}")
    
    if slot1.get("vocabulary_cognates"):
        vocab = slot1.get("vocabulary_cognates")
        if isinstance(vocab, list) and len(vocab) > 0:
            print(f"\n✅ Vocabulary found: {len(vocab)} items")
            print(f"   First item: {vocab[0]}")
        else:
            print(f"\n❌ Vocabulary is empty or not a list")
    else:
        print(f"\n❌ vocabulary_cognates key missing")
    
    if slot1.get("sentence_frames"):
        frames = slot1.get("sentence_frames")
        if isinstance(frames, list) and len(frames) > 0:
            print(f"\n✅ Sentence frames found: {len(frames)} items")
            print(f"   First frame: {frames[0]}")
        else:
            print(f"\n❌ Sentence frames is empty or not a list")
    else:
        print(f"\n❌ sentence_frames key missing")

# Now generate steps and see what happens
print(f"\n{'='*60}")
print("Generating lesson steps...")
print(f"{'='*60}")

gen_response = requests.post(
    f"{API_BASE}/lesson-steps/generate",
    params={"plan_id": plan_id, "day": "monday", "slot": 1},
    headers={"X-Current-User-Id": user_id},
    timeout=30
)

if gen_response.status_code == 200:
    steps = gen_response.json()
    print(f"\nGenerated {len(steps)} steps:")
    for step in steps:
        step_name = step.get("step_name", "")
        has_vocab = bool(step.get("vocabulary_cognates"))
        has_frames = bool(step.get("sentence_frames"))
        print(f"  - {step_name}: vocab={has_vocab}, frames={has_frames}")
        
        if "vocabulary" in step_name.lower():
            vocab_data = step.get("vocabulary_cognates")
            print(f"      vocabulary_cognates: {vocab_data}")
        
        if "sentence" in step_name.lower() or step.get("content_type") == "sentence_frames":
            frames_data = step.get("sentence_frames")
            print(f"      sentence_frames: {frames_data}")
else:
    print(f"\n❌ Failed to generate steps: {gen_response.status_code}")
    print(gen_response.text[:500])


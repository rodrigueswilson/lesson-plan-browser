"""
Find the plan that has vocabulary_cognates and sentence_frames in its lesson_json.
"""
import sys
import requests
from pathlib import Path

API_BASE = "http://localhost:8000/api"
user_id = "04fe8898-cb89-4a73-affb-64a97a98f820"

print("="*80)
print("FINDING PLAN WITH VOCABULARY/FRAMES")
print("="*80)

# Get all plans for user
plans_response = requests.get(
    f"{API_BASE}/users/{user_id}/plans?limit=100",
    headers={"X-Current-User-Id": user_id}
)

if plans_response.status_code != 200:
    print(f"[FAIL] Cannot get plans: {plans_response.status_code}")
    sys.exit(1)

plans = plans_response.json()
print(f"\nFound {len(plans)} plans")

# Check each plan for vocabulary/frames
print(f"\nChecking plans for vocabulary/frames...")
plans_with_vocab = []

for i, plan in enumerate(plans):
    plan_id = plan["id"]
    week_of = plan.get("week_of", "")
    
    # Get plan detail
    detail_response = requests.get(
        f"{API_BASE}/plans/{plan_id}",
        headers={"X-Current-User-Id": user_id}
    )
    
    if detail_response.status_code != 200:
        continue
    
    detail = detail_response.json()
    lesson_json = detail.get("lesson_json", {})
    
    if not lesson_json:
        continue
    
    # Check Monday slot 1
    days = lesson_json.get("days", {})
    monday = days.get("monday", {})
    slots = monday.get("slots", [])
    slot1 = next((s for s in slots if s.get("slot_number") == 1), None)
    
    if not slot1:
        continue
    
    vocab = slot1.get("vocabulary_cognates", [])
    frames = slot1.get("sentence_frames", [])
    
    has_vocab = vocab and isinstance(vocab, list) and len(vocab) > 0
    has_frames = frames and isinstance(frames, list) and len(frames) > 0
    
    if has_vocab or has_frames:
        print(f"\n{i+1}. Plan: {plan_id} (Week: {week_of})")
        print(f"   vocabulary_cognates: {len(vocab) if isinstance(vocab, list) else 0} items")
        print(f"   sentence_frames: {len(frames) if isinstance(frames, list) else 0} items")
        plans_with_vocab.append({
            "id": plan_id,
            "week_of": week_of,
            "vocab_count": len(vocab) if isinstance(vocab, list) else 0,
            "frames_count": len(frames) if isinstance(frames, list) else 0,
        })

print(f"\n{'='*80}")
print(f"Found {len(plans_with_vocab)} plans with vocabulary/frames")
print("="*80)

if plans_with_vocab:
    print(f"\nPlans with vocabulary/frames:")
    for plan in plans_with_vocab:
        print(f"  - {plan['id']} (Week: {plan['week_of']}) - vocab: {plan['vocab_count']}, frames: {plan['frames_count']}")
    
    print(f"\nTo use these plans:")
    print(f"1. Navigate to Lesson Plan Browser")
    print(f"2. Find the plan for week: {plans_with_vocab[0]['week_of']}")
    print(f"3. Click on Monday, Slot 1")
    print(f"4. Vocabulary and sentence frames should appear")
else:
    print(f"\n[INFO] No plans found with vocabulary/frames in lesson_json")
    print(f"       The plans need to be updated with vocabulary/frames data")

print("\n" + "="*80)


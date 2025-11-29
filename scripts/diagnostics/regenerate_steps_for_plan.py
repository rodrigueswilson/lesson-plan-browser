"""
Regenerate lesson steps for a specific plan and check if vocabulary/frames steps are created.
"""
import requests
import sys

API_BASE = "http://localhost:8000/api"

# Find the correct plan
users_response = requests.get(f"{API_BASE}/users")
users = users_response.json()
user_id = next(u["id"] for u in users if "Wilson" in u.get("name", ""))

plans_response = requests.get(
    f"{API_BASE}/users/{user_id}/plans",
    headers={"X-Current-User-Id": user_id}
)
plans = plans_response.json()

# Find plan with vocabulary/frames (the one we just fixed)
plan_id = None
for p in plans:
    if "11-17" in p.get("week_of", ""):
        # Check if this plan has vocabulary/frames
        detail_response = requests.get(
            f"{API_BASE}/plans/{p['id']}",
            headers={"X-Current-User-Id": user_id}
        )
        if detail_response.status_code == 200:
            detail = detail_response.json()
            lesson_json = detail.get("lesson_json", {})
            monday = lesson_json.get("days", {}).get("monday", {})
            slots = monday.get("slots", [])
            slot1 = next((s for s in slots if s.get("slot_number") == 1), None)
            if slot1 and slot1.get("vocabulary_cognates"):
                plan_id = p["id"]
                print(f"Found plan with vocabulary/frames: {plan_id}")
                print(f"  Week: {p.get('week_of')}")
                vocab = slot1.get("vocabulary_cognates", [])
                frames = slot1.get("sentence_frames", [])
                print(f"  vocabulary_cognates: {len(vocab)} items")
                print(f"  sentence_frames: {len(frames)} items")
                break

# If not found, use the plan we just fixed
if not plan_id:
    # Try the plan ID we know exists (from fix_plan_vocab_frames.py output)
    test_plan_id = "plan_20251122160826"
    detail_response = requests.get(
        f"{API_BASE}/plans/{test_plan_id}",
        headers={"X-Current-User-Id": user_id}
    )
    if detail_response.status_code == 200:
        detail = detail_response.json()
        lesson_json = detail.get("lesson_json", {})
        monday = lesson_json.get("days", {}).get("monday", {})
        slots = monday.get("slots", [])
        slot1 = next((s for s in slots if s.get("slot_number") == 1), None)
        if slot1 and slot1.get("vocabulary_cognates"):
            plan_id = test_plan_id
            print(f"\n[OK] Using known plan with vocabulary/frames: {plan_id}")
        else:
            print(f"\n[FAIL] Known plan {test_plan_id} doesn't have vocabulary/frames")
    else:
        print(f"\n[FAIL] Cannot access plan {test_plan_id}: {detail_response.status_code}")

if not plan_id:
    print("\n[ERROR] No plan found with vocabulary/frames")
    print("Available plans for week 11-17:")
    for p in plans:
        if "11-17" in p.get("week_of", "") or "11/17" in p.get("week_of", ""):
            print(f"  - {p['id']}: {p.get('week_of')}")
    sys.exit(1)

# Delete existing steps first
print(f"\nDeleting existing steps for plan {plan_id}...")
# (Steps will be deleted automatically when we regenerate)

# Generate steps
print(f"\nGenerating lesson steps for plan {plan_id}, Monday slot 1...")
gen_response = requests.post(
    f"{API_BASE}/lesson-steps/generate",
    params={"plan_id": plan_id, "day": "monday", "slot": 1},
    headers={"X-Current-User-Id": user_id},
    timeout=30
)

if gen_response.status_code == 200:
    steps = gen_response.json()
    print(f"\n[OK] Generated {len(steps)} steps:\n")
    
    vocab_step = None
    frames_step = None
    
    for step in steps:
        step_name = step.get("step_name", "")
        content_type = step.get("content_type", "")
        has_vocab = bool(step.get("vocabulary_cognates"))
        has_frames = bool(step.get("sentence_frames"))
        
        print(f"  {step_name} (type: {content_type})")
        print(f"    vocabulary_cognates: {has_vocab}")
        print(f"    sentence_frames: {has_frames}")
        
        if "vocabulary" in step_name.lower() or "cognate" in step_name.lower():
            vocab_step = step
        if content_type == "sentence_frames":
            frames_step = step
    
    # Check vocabulary step
    print(f"\n{'='*60}")
    if vocab_step:
        vocab_data = vocab_step.get("vocabulary_cognates")
        if vocab_data and isinstance(vocab_data, list) and len(vocab_data) > 0:
            print(f"[OK] Vocabulary step found with {len(vocab_data)} items")
            print(f"     Step name: {vocab_step.get('step_name')}")
            print(f"     Sample: {vocab_data[0].get('english')} -> {vocab_data[0].get('portuguese')}")
        else:
            print(f"[FAIL] Vocabulary step found but vocabulary_cognates is empty")
            print(f"        Type: {type(vocab_data)}, Value: {vocab_data}")
    else:
        print(f"[FAIL] No vocabulary step found")
    
    # Check frames step
    if frames_step:
        frames_data = frames_step.get("sentence_frames")
        if frames_data and isinstance(frames_data, list) and len(frames_data) > 0:
            print(f"[OK] Sentence frames step found with {len(frames_data)} items")
            print(f"     Step name: {frames_step.get('step_name')}")
            print(f"     Sample: {frames_data[0].get('english', 'N/A')}")
        else:
            print(f"[FAIL] Sentence frames step found but sentence_frames is empty")
            print(f"        Type: {type(frames_data)}, Value: {frames_data}")
    else:
        print(f"[FAIL] No sentence frames step found")
    
    print(f"{'='*60}\n")
    
    if vocab_step and vocab_step.get("vocabulary_cognates") and frames_step and frames_step.get("sentence_frames"):
        print("[SUCCESS] Both vocabulary and sentence frames steps are present!")
    else:
        print("[ISSUE] Vocabulary or sentence frames steps are missing.")
        print("\nThis suggests the step generation code isn't extracting vocabulary/frames properly.")
else:
    print(f"\n[FAIL] Failed to generate steps: {gen_response.status_code}")
    print(gen_response.text[:500])


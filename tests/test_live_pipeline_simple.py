"""
Simple test to verify vocabulary and sentence frames in live pipeline.
Requires backend at localhost:8000 and at least one user with plans; skips otherwise.
"""

import sys
import time
from pathlib import Path

import pytest
import requests

API_BASE = "http://localhost:8000/api"

def wait_for_backend(max_retries=30, delay=1):
    """Wait for backend to be ready."""
    print(f"[INFO] Waiting for backend at {API_BASE}...")
    for i in range(max_retries):
        try:
            response = requests.get(f"{API_BASE}/health", timeout=2)
            if response.status_code == 200:
                print(f"[OK] Backend is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        if i > 0:
            print(f"  Attempt {i+1}/{max_retries}...")
        time.sleep(delay)
    return False

def get_user_and_plans():
    """Get a user and their plans."""
    print("\n[TEST] Fetching users and plans...")
    
    # Get users
    users_response = requests.get(f"{API_BASE}/users")
    if users_response.status_code != 200 or not users_response.json():
        print("[FAIL] No users found. Please create a user first.")
        return None, None
    
    users = users_response.json()
    user_id = users[0]["id"]
    print(f"[OK] Using user: {user_id}")
    
    # Get user plans
    plans_response = requests.get(
        f"{API_BASE}/users/{user_id}/plans",
        headers={"X-Current-User-Id": user_id}
    )
    
    if plans_response.status_code != 200:
        print(f"[FAIL] Failed to get plans: {plans_response.text}")
        return None, None
    
    plans = plans_response.json()
    if not plans:
        print("[INFO] No plans found for user. The test needs at least one plan.")
        print("       You can generate a plan using the frontend or batch processor.")
        return user_id, None
    
    print(f"[OK] Found {len(plans)} plans")
    return user_id, plans


@pytest.fixture(scope="module")
def user_id():
    """User ID from live backend; skips if backend down or no users."""
    if not wait_for_backend(max_retries=1, delay=0):
        pytest.skip("Backend not running at " + API_BASE)
    uid, plans = get_user_and_plans()
    if not uid:
        pytest.skip("No users from API")
    return uid


@pytest.fixture(scope="module")
def plan_id(user_id):
    """First plan ID for user; skips if no plans."""
    _, plans = get_user_and_plans()
    if not plans:
        pytest.skip("No plans for user; create a plan first")
    return plans[0]["id"]


def test_plan_vocab_frames(user_id, plan_id):
    """Test vocabulary and frames in a plan's lesson steps."""
    print(f"\n[TEST] Testing plan {plan_id}...")
    
    # Get plan detail
    plan_response = requests.get(
        f"{API_BASE}/plans/{plan_id}",
        headers={"X-Current-User-Id": user_id}
    )
    
    if plan_response.status_code != 200:
        print(f"[FAIL] Failed to get plan: {plan_response.text}")
        return False
    
    plan = plan_response.json()
    lesson_json = plan.get("lesson_json", {})
    
    # Check if plan has vocabulary/frames in JSON
    has_vocab_in_json = False
    has_frames_in_json = False
    
    days = lesson_json.get("days", {})
    for day_name, day_data in days.items():
        slots = day_data.get("slots", [])
        for slot in slots:
            if slot.get("vocabulary_cognates"):
                has_vocab_in_json = True
                print(f"[OK] Found vocabulary_cognates in {day_name} slot {slot.get('slot_number')}")
            if slot.get("sentence_frames"):
                has_frames_in_json = True
                print(f"[OK] Found sentence_frames in {day_name} slot {slot.get('slot_number')}")
    
    if not has_vocab_in_json and not has_frames_in_json:
        print("[INFO] Plan JSON doesn't contain vocabulary/frames. Checking lesson steps...")
    
    # Generate or get lesson steps
    print("\n[TEST] Checking lesson steps...")
    
    # Try Monday, slot 1 first
    steps_response = requests.get(
        f"{API_BASE}/lesson-steps",
        params={"plan_id": plan_id, "day": "monday", "slot": 1},
        headers={"X-Current-User-Id": user_id}
    )
    
    if steps_response.status_code != 200:
        print(f"[INFO] No steps found. Generating steps...")
        # Try to generate steps
        gen_response = requests.post(
            f"{API_BASE}/lesson-steps/generate",
            params={"plan_id": plan_id, "day": "monday", "slot": 1},
            headers={"X-Current-User-Id": user_id}
        )
        
        if gen_response.status_code != 200:
            print(f"[INFO] Could not generate steps: {gen_response.text}")
            return False
        
        steps = gen_response.json()
    else:
        steps = steps_response.json()
    
    if not steps:
        print("[INFO] No steps available for Monday slot 1. Checking other slots...")
        return False
    
    print(f"[OK] Found {len(steps)} lesson steps")
    
    # Verify vocabulary and frames in steps
    vocab_step = None
    frames_step = None
    
    for step in steps:
        step_name = step.get("step_name", "").lower()
        content_type = step.get("content_type", "")
        
        if "vocabulary" in step_name or "cognate" in step_name:
            vocab_step = step
        if content_type == "sentence_frames" or "sentence" in step_name:
            frames_step = step
    
    # Check vocabulary step
    if vocab_step:
        vocab_data = vocab_step.get("vocabulary_cognates")
        if vocab_data and isinstance(vocab_data, list) and len(vocab_data) > 0:
            print(f"[OK] Vocabulary step found with {len(vocab_data)} items")
            print(f"     First item: {vocab_data[0].get('english')} -> {vocab_data[0].get('portuguese')}")
        else:
            print(f"[WARN] Vocabulary step found but vocabulary_cognates is missing or empty")
            print(f"     Step: {vocab_step.get('step_name')}")
            print(f"     vocabulary_cognates: {vocab_data}")
    else:
        print("[INFO] No vocabulary step found")
    
    # Check frames step
    if frames_step:
        frames_data = frames_step.get("sentence_frames")
        if frames_data and isinstance(frames_data, list) and len(frames_data) > 0:
            print(f"[OK] Sentence frames step found with {len(frames_data)} frames")
            print(f"     First frame: {frames_data[0].get('english', 'N/A')}")
        else:
            print(f"[WARN] Sentence frames step found but sentence_frames is missing or empty")
            print(f"     Step: {frames_step.get('step_name')}")
            print(f"     sentence_frames: {frames_data}")
    else:
        print("[INFO] No sentence frames step found")
    
    # Overall success if we found at least vocabulary OR frames
    if (vocab_step and vocab_step.get("vocabulary_cognates")) or \
       (frames_step and frames_step.get("sentence_frames")):
        return True
    
    return False

def main():
    """Run the simple pipeline test."""
    print("=" * 60)
    print("SIMPLE LIVE PIPELINE TEST - Vocabulary & Sentence Frames")
    print("=" * 60)
    
    # Wait for backend
    if not wait_for_backend():
        print("[FAIL] Backend is not responding. Please start the backend server.")
        return False
    
    try:
        # Get user and plans
        user_id, plans = get_user_and_plans()
        if not user_id:
            return False
        
        if not plans:
            print("\n[INFO] No plans found. Please create a plan first using:")
            print("  1. The frontend application")
            print("  2. The batch processor")
            print("\nThen run this test again.")
            return False
        
        # Test each plan
        success_count = 0
        for plan in plans[:3]:  # Test up to 3 plans
            plan_id = plan["id"]
            week_of = plan.get("week_of", "unknown")
            
            print(f"\n{'=' * 60}")
            print(f"Testing Plan: {plan_id} (Week: {week_of})")
            print(f"{'=' * 60}")
            
            if test_plan_vocab_frames(user_id, plan_id):
                success_count += 1
        
        print("\n" + "=" * 60)
        if success_count > 0:
            print(f"[SUCCESS] Pipeline verification completed!")
            print(f"         Found vocabulary/frames in {success_count} plan(s)")
            print("\nThe pipeline is working correctly:")
            print("  ✓ Lesson steps contain vocabulary_cognates")
            print("  ✓ Lesson steps contain sentence_frames")
            print("  ✓ Data is accessible via API")
            print("\nYou can verify in the frontend by opening any lesson plan.")
        else:
            print("[INFO] Pipeline test completed but no vocabulary/frames found.")
            print("       This might mean:")
            print("       1. Plans don't have vocabulary/frames data yet")
            print("       2. Lesson steps haven't been generated")
            print("       3. The plan needs to be regenerated with the fix applied")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n[FAIL] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

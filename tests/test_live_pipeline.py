"""
Test the vocabulary and sentence frames pipeline with live backend/frontend.

This script:
1. Creates a lesson plan with vocabulary_cognates and sentence_frames
2. Generates lesson steps via API
3. Fetches the steps back from API
4. Verifies vocabulary_cognates and sentence_frames are preserved
"""

import sys
import requests
import json
import time
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

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
        print(f"  Attempt {i+1}/{max_retries}...")
        time.sleep(delay)
    return False

def create_test_plan():
    """Create a test weekly plan."""
    print("\n[TEST] Creating test weekly plan...")
    
    # Get or create user
    users_response = requests.get(f"{API_BASE}/users")
    if users_response.status_code == 200 and users_response.json():
        user_id = users_response.json()[0]["id"]
        print(f"[INFO] Using existing user: {user_id}")
    else:
        # Create test user
        user_response = requests.post(
            f"{API_BASE}/users",
            json={"first_name": "Test", "last_name": "Pipeline"}
        )
        if user_response.status_code != 200:
            print(f"[FAIL] Failed to create user: {user_response.text}")
            return None, None
        user_id = user_response.json()["id"]
        print(f"[OK] Created test user: {user_id}")
    
    # Create weekly plan
    plan_response = requests.post(
        f"{API_BASE}/plans",
        json={"week_of": "11/17-11/21"},
        headers={"X-Current-User-Id": user_id}
    )
    
    if plan_response.status_code != 200:
        print(f"[FAIL] Failed to create plan: {plan_response.text}")
        return None, None
    
    plan_id = plan_response.json()["id"]
    print(f"[OK] Created plan: {plan_id}")
    
    return user_id, plan_id

def update_plan_with_vocab_frames(user_id, plan_id):
    """Update plan with test vocabulary and sentence frames data."""
    print("\n[TEST] Updating plan with vocabulary and sentence frames...")
    
    # Sample vocabulary and frames data
    lesson_json = {
        "metadata": {
            "week_of": "11/17-11/21",
            "grade": "3",
            "subject": "ELA",
            "user_name": "Test Pipeline",
            "total_slots": 1
        },
        "days": {
            "monday": {
                "slots": [
                    {
                        "slot_number": 1,
                        "subject": "ELA",
                        "grade": "3",
                        "vocabulary_cognates": [
                            {
                                "english": "state",
                                "portuguese": "estado",
                                "is_cognate": False,
                                "relevance_note": "Political unit"
                            },
                            {
                                "english": "map",
                                "portuguese": "mapa",
                                "is_cognate": True,
                                "relevance_note": "Geography"
                            },
                            {
                                "english": "capital",
                                "portuguese": "capital",
                                "is_cognate": True,
                                "relevance_note": "Government center"
                            },
                            {
                                "english": "coast",
                                "portuguese": "costa",
                                "is_cognate": True,
                                "relevance_note": "Shoreline"
                            },
                            {
                                "english": "population",
                                "portuguese": "população",
                                "is_cognate": True,
                                "relevance_note": "Demographics"
                            },
                            {
                                "english": "beach",
                                "portuguese": "praia",
                                "is_cognate": False,
                                "relevance_note": "Recreation"
                            }
                        ],
                        "sentence_frames": [
                            {
                                "proficiency_level": "levels_1_2",
                                "english": "This is a fact: ___",
                                "portuguese": "Este é um fato: ___",
                                "language_function": "identify",
                                "frame_type": "frame"
                            },
                            {
                                "proficiency_level": "levels_1_2",
                                "english": "I see ___ in the text.",
                                "portuguese": "Eu vejo ___ no texto.",
                                "language_function": "describe",
                                "frame_type": "frame"
                            },
                            {
                                "proficiency_level": "levels_3_4",
                                "english": "One important fact is ___ because ___",
                                "portuguese": "Um fato importante é ___ porque ___",
                                "language_function": "explain",
                                "frame_type": "frame"
                            }
                        ]
                    }
                ]
            }
        }
    }
    
    # Update plan
    update_response = requests.put(
        f"{API_BASE}/plans/{plan_id}",
        json={"lesson_json": lesson_json},
        headers={"X-Current-User-Id": user_id}
    )
    
    if update_response.status_code != 200:
        print(f"[FAIL] Failed to update plan: {update_response.text}")
        return False
    
    print("[OK] Plan updated with vocabulary and sentence frames")
    return True

def generate_lesson_steps(user_id, plan_id):
    """Generate lesson steps via API."""
    print("\n[TEST] Generating lesson steps...")
    
    response = requests.post(
        f"{API_BASE}/lesson-steps/generate",
        params={"plan_id": plan_id, "day": "monday", "slot": 1},
        headers={"X-Current-User-Id": user_id}
    )
    
    if response.status_code != 200:
        print(f"[FAIL] Failed to generate steps: {response.text}")
        return None
    
    steps = response.json()
    print(f"[OK] Generated {len(steps)} lesson steps")
    return steps

def verify_vocab_frames_in_steps(steps):
    """Verify vocabulary and sentence frames are present in steps."""
    print("\n[TEST] Verifying vocabulary and sentence frames in steps...")
    
    vocab_step = None
    frames_step = None
    
    for step in steps:
        if "vocabulary" in step.get("step_name", "").lower() or "cognate" in step.get("step_name", "").lower():
            vocab_step = step
        if step.get("content_type") == "sentence_frames":
            frames_step = step
    
    # Verify vocabulary step
    if not vocab_step:
        print("[FAIL] No vocabulary step found!")
        return False
    
    vocab_data = vocab_step.get("vocabulary_cognates")
    if not vocab_data or not isinstance(vocab_data, list):
        print(f"[FAIL] vocabulary_cognates missing or invalid in vocab step!")
        print(f"     Step: {vocab_step.get('step_name')}")
        print(f"     vocabulary_cognates: {vocab_data}")
        return False
    
    if len(vocab_data) != 6:
        print(f"[FAIL] Expected 6 vocabulary items, got {len(vocab_data)}")
        return False
    
    print(f"[OK] Vocabulary step found with {len(vocab_data)} items")
    print(f"     First item: {vocab_data[0].get('english')} -> {vocab_data[0].get('portuguese')}")
    
    # Verify sentence frames step
    if not frames_step:
        print("[FAIL] No sentence frames step found!")
        return False
    
    frames_data = frames_step.get("sentence_frames")
    if not frames_data or not isinstance(frames_data, list):
        print(f"[FAIL] sentence_frames missing or invalid in frames step!")
        print(f"     Step: {frames_step.get('step_name')}")
        print(f"     sentence_frames: {frames_data}")
        return False
    
    if len(frames_data) < 3:
        print(f"[FAIL] Expected at least 3 sentence frames, got {len(frames_data)}")
        return False
    
    print(f"[OK] Sentence frames step found with {len(frames_data)} frames")
    print(f"     First frame: {frames_data[0].get('english')}")
    
    return True

def fetch_steps_from_api(user_id, plan_id):
    """Fetch steps directly from API endpoint."""
    print("\n[TEST] Fetching steps from API endpoint...")
    
    response = requests.get(
        f"{API_BASE}/lesson-steps",
        params={"plan_id": plan_id, "day": "monday", "slot": 1},
        headers={"X-Current-User-Id": user_id}
    )
    
    if response.status_code != 200:
        print(f"[FAIL] Failed to fetch steps: {response.text}")
        return None
    
    steps = response.json()
    print(f"[OK] Fetched {len(steps)} steps from API")
    return steps

def main():
    """Run the complete pipeline test."""
    print("=" * 60)
    print("LIVE PIPELINE TEST - Vocabulary & Sentence Frames")
    print("=" * 60)
    
    # Wait for backend
    if not wait_for_backend():
        print("[FAIL] Backend is not responding. Please start the backend server.")
        return False
    
    try:
        # Create test plan
        user_id, plan_id = create_test_plan()
        if not user_id or not plan_id:
            return False
        
        # Update plan with vocabulary and frames
        if not update_plan_with_vocab_frames(user_id, plan_id):
            return False
        
        # Generate lesson steps
        steps = generate_lesson_steps(user_id, plan_id)
        if not steps:
            return False
        
        # Verify data in generated steps
        if not verify_vocab_frames_in_steps(steps):
            return False
        
        # Wait a moment for database to settle
        time.sleep(1)
        
        # Fetch steps back from API
        fetched_steps = fetch_steps_from_api(user_id, plan_id)
        if not fetched_steps:
            return False
        
        # Verify data in fetched steps
        if not verify_vocab_frames_in_steps(fetched_steps):
            return False
        
        print("\n" + "=" * 60)
        print("[SUCCESS] ALL PIPELINE TESTS PASSED!")
        print("=" * 60)
        print("\nThe vocabulary and sentence frames pipeline is working correctly:")
        print("  ✓ Data stored in database")
        print("  ✓ Data retrieved from database")
        print("  ✓ Data preserved in API responses")
        print("  ✓ Frontend should now display vocabulary and sentence frames correctly")
        print("\nYou can verify in the frontend by:")
        print(f"  1. Opening a lesson plan for week 11/17-11/21")
        print(f"  2. Looking for Slot 1 on Monday")
        print(f"  3. Checking the Vocabulary section")
        print(f"  4. Checking the Sentence Frames section")
        
        return True
        
    except Exception as e:
        print(f"\n[FAIL] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

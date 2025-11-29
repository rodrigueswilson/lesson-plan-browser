"""
Final comprehensive test to verify the complete pipeline.
"""
import sys
import requests
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from backend.database import get_db

API_BASE = "http://localhost:8000/api"

# Get user and plan
users_response = requests.get(f"{API_BASE}/users")
users = users_response.json()
user_id = next(u["id"] for u in users if "Wilson" in u.get("name", ""))
plan_id = "plan_20251122160826"

print("="*80)
print("FINAL PIPELINE VERIFICATION")
print("="*80)

# 1. Check database directly
print("\n1. DATABASE CHECK")
db = get_db()
steps = db.get_lesson_steps(plan_id, day_of_week="monday", slot_number=1)
vocab_step = next((s for s in steps if "vocabulary" in s.step_name.lower()), None)

if vocab_step:
    print(f"   [OK] Found vocabulary step: {vocab_step.step_name}")
    vocab_from_db = vocab_step.vocabulary_cognates
    print(f"   vocabulary_cognates in DB: {type(vocab_from_db)} = {vocab_from_db}")
    if vocab_from_db and isinstance(vocab_from_db, list):
        print(f"   [OK] vocabulary_cognates has {len(vocab_from_db)} items")
    else:
        print(f"   [FAIL] vocabulary_cognates is None or not a list")
else:
    print(f"   [FAIL] Vocabulary step not found")

# 2. Check API response
print("\n2. API RESPONSE CHECK")
response = requests.get(
    f"{API_BASE}/lesson-steps/{plan_id}/monday/1",
    headers={"X-Current-User-Id": user_id}
)

if response.status_code == 200:
    steps = response.json()
    vocab_step_api = next((s for s in steps if "vocabulary" in s.get("step_name", "").lower()), None)
    
    if vocab_step_api:
        print(f"   [OK] Found vocabulary step in API response")
        vocab_from_api = vocab_step_api.get("vocabulary_cognates")
        print(f"   vocabulary_cognates in API: {type(vocab_from_api)} = {vocab_from_api}")
        
        # Check all fields
        all_keys = list(vocab_step_api.keys())
        print(f"   All fields: {all_keys}")
        
        if vocab_from_api and isinstance(vocab_from_api, list):
            print(f"   [OK] vocabulary_cognates has {len(vocab_from_api)} items in API response")
        else:
            print(f"   [FAIL] vocabulary_cognates missing or None in API response")
            print(f"          Expected from DB: {vocab_from_db if vocab_step else 'N/A'}")
    else:
        print(f"   [FAIL] Vocabulary step not found in API response")
else:
    print(f"   [FAIL] API returned status {response.status_code}")

print("\n" + "="*80)


"""
Comprehensive diagnostic script to trace vocabulary and sentence frames pipeline.
Run this to identify exactly where the data is being lost.
"""
import json
import sys
import requests
from pathlib import Path
from typing import Dict, Any, Optional

SOURCE_FILE = Path(r"F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W47\Wilson_Rodrigues_Weekly_W47_11-17-11-21_20251122_162906.json")
API_BASE = "http://localhost:8000/api"

def print_section(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def check_source_file() -> Optional[Dict[str, Any]]:
    """CHECK 1: Verify source JSON has vocabulary and sentence frames."""
    print_section("CHECK 1: Source JSON File")
    
    if not SOURCE_FILE.exists():
        print(f"[FAIL] Source file not found: {SOURCE_FILE}")
        return None
    
    try:
        with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"[OK] Source file loaded")
        
        # Check Monday slot 1
        monday = data.get("days", {}).get("monday", {})
        slots = monday.get("slots", [])
        slot1 = next((s for s in slots if s.get("slot_number") == 1), None)
        
        if not slot1:
            print("[FAIL] Slot 1 not found")
            return None
        
        vocab = slot1.get("vocabulary_cognates", [])
        frames = slot1.get("sentence_frames", [])
        
        print(f"[OK] Slot 1 vocabulary_cognates: {len(vocab)} items")
        print(f"[OK] Slot 1 sentence_frames: {len(frames)} items")
        
        if vocab:
            print(f"     Sample: {vocab[0].get('english')} -> {vocab[0].get('portuguese')}")
        
        return data
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_backend_health() -> bool:
    """CHECK 2: Backend is running."""
    print_section("CHECK 2: Backend Health")
    
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            print("[OK] Backend is running")
            return True
        else:
            print(f"[FAIL] Backend returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Cannot connect to backend: {e}")
        print(f"      Make sure backend is running on {API_BASE}")
        return False

def check_plan_in_db(week_of: str = "11/17-11/21"):
    """CHECK 3: Find plan and check lesson_json."""
    # Normalize week format (handle both "/" and "-" separators)
    week_normalized = week_of.replace("/", "-")
    week_alt = week_of.replace("-", "/")
    
    print_section("CHECK 3: Plan in Database")
    """CHECK 3: Find plan and check lesson_json."""
    print_section("CHECK 3: Plan in Database")
    
    try:
        # Get users
        users_response = requests.get(f"{API_BASE}/users", timeout=5)
        if users_response.status_code != 200:
            print(f"[FAIL] Cannot get users: {users_response.status_code}")
            return None, None
        
        users = users_response.json()
        if not users:
            print("[FAIL] No users found")
            return None, None
        
        print(f"[OK] Found {len(users)} users")
        
        # Try to find plan for week across all users
        plan = None
        user_id = None
        
        for user in users:
            test_user_id = user["id"]
            print(f"[INFO] Checking user: {user.get('name', test_user_id)}")
            
            # Get plans for this user
            plans_response = requests.get(
                f"{API_BASE}/users/{test_user_id}/plans",
                headers={"X-Current-User-Id": test_user_id},
                timeout=5
            )
            
            if plans_response.status_code == 200:
                plans = plans_response.json()
                # Try to find plan for week (check both formats)
                found_plan = next(
                    (p for p in plans 
                     if p.get("week_of") == week_of 
                     or p.get("week_of") == week_normalized 
                     or p.get("week_of") == week_alt),
                    None
                )
                if found_plan:
                    plan = found_plan
                    user_id = test_user_id
                    print(f"[OK] Found plan for week {week_of} (stored as: {plan.get('week_of')}) under user: {user.get('name', test_user_id)}")
                    break
        
        if not plan:
            print(f"[FAIL] Plan not found for {week_of} (or {week_normalized}) in any user")
            # Show available weeks
            for user in users[:3]:  # Check first 3 users
                test_user_id = user["id"]
                plans_response = requests.get(
                    f"{API_BASE}/users/{test_user_id}/plans",
                    headers={"X-Current-User-Id": test_user_id},
                    timeout=5
                )
                if plans_response.status_code == 200:
                    plans = plans_response.json()
                    if plans:
                        print(f"      User {user.get('name', test_user_id)} has weeks: {[p.get('week_of') for p in plans[:5]]}")
                        # Try to match with normalized format
                        for p in plans:
                            stored_week = p.get("week_of", "")
                            if stored_week.replace("-", "/") == week_of or stored_week.replace("/", "-") == week_normalized:
                                plan = p
                                user_id = test_user_id
                                print(f"[OK] Found matching plan: {p['id']} with week format: {stored_week}")
                                break
                        if plan:
                            break
            if not plan:
                return None, None
        
        plan_id = plan["id"]
        print(f"[OK] Plan found: {plan_id}")
        print(f"[OK] User: {user_id}")
        
        # Get plan detail
        detail_response = requests.get(
            f"{API_BASE}/plans/{plan_id}",
            headers={"X-Current-User-Id": user_id},
            timeout=10
        )
        if detail_response.status_code != 200:
            print(f"[FAIL] Cannot get plan detail: {detail_response.status_code}")
            print(f"      Response: {detail_response.text[:200]}")
            return None, None
        
        plan_detail = detail_response.json()
        lesson_json = plan_detail.get("lesson_json", {})
        
        if not lesson_json:
            print("[FAIL] Plan has no lesson_json")
            return plan_id, user_id
        
        print("[OK] Plan has lesson_json")
        
        # Check Monday slot 1
        monday = lesson_json.get("days", {}).get("monday", {})
        slots = monday.get("slots", [])
        slot1 = next((s for s in slots if s.get("slot_number") == 1), None)
        
        if slot1:
            vocab = slot1.get("vocabulary_cognates", [])
            frames = slot1.get("sentence_frames", [])
            print(f"[OK] Slot 1 found in lesson_json")
            
            if isinstance(vocab, list) and len(vocab) > 0:
                print(f"[OK] vocabulary_cognates: {len(vocab)} items")
            elif vocab is None:
                print(f"[FAIL] vocabulary_cognates is None")
            elif isinstance(vocab, list):
                print(f"[FAIL] vocabulary_cognates is empty list")
            else:
                print(f"[FAIL] vocabulary_cognates invalid type: {type(vocab)}")
            
            if isinstance(frames, list) and len(frames) > 0:
                print(f"[OK] sentence_frames: {len(frames)} items")
            elif frames is None:
                print(f"[FAIL] sentence_frames is None")
            elif isinstance(frames, list):
                print(f"[FAIL] sentence_frames is empty list")
            else:
                print(f"[FAIL] sentence_frames invalid type: {type(frames)}")
            
            if vocab and isinstance(vocab, list) and len(vocab) > 0:
                print(f"     Sample vocab: {vocab[0].get('english')} -> {vocab[0].get('portuguese')}")
            if frames and isinstance(frames, list) and len(frames) > 0:
                print(f"     Sample frame: {frames[0].get('english', 'N/A')}")
        else:
            print("[FAIL] Slot 1 not found in plan lesson_json")
            print(f"      Available slots: {[s.get('slot_number') for s in slots if isinstance(s, dict)]}")
        
        return plan_id, user_id
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def check_lesson_steps(plan_id: str, user_id: str, day: str = "monday", slot: int = 1):
    """CHECK 4: Check lesson steps for vocabulary/frames."""
    print_section(f"CHECK 4: Lesson Steps (day={day}, slot={slot})")
    
    try:
        # Try to get existing steps
        response = requests.get(
            f"{API_BASE}/lesson-steps",
            params={"plan_id": plan_id, "day": day, "slot": slot},
            headers={"X-Current-User-Id": user_id},
            timeout=10
        )
        
        if response.status_code == 200:
            steps = response.json()
            print(f"[OK] Found {len(steps)} existing steps")
        else:
            print(f"[INFO] No steps found (status {response.status_code}), generating...")
            gen_response = requests.post(
                f"{API_BASE}/lesson-steps/generate",
                params={"plan_id": plan_id, "day": day, "slot": slot},
                headers={"X-Current-User-Id": user_id},
                timeout=30
            )
            if gen_response.status_code != 200:
                print(f"[FAIL] Cannot generate: {gen_response.status_code}")
                print(gen_response.text[:300])
                return False
            steps = gen_response.json()
            print(f"[OK] Generated {len(steps)} steps")
        
        if not steps:
            print("[FAIL] No lesson steps available")
            return False
        
        # Find vocab and frames steps
        vocab_step = None
        frames_step = None
        
        print(f"\n[INFO] Step details:")
        for step in steps:
            step_name = step.get("step_name", "")
            content_type = step.get("content_type", "")
            has_vocab = bool(step.get("vocabulary_cognates"))
            has_frames = bool(step.get("sentence_frames"))
            print(f"  - {step_name} (type: {content_type}, vocab: {has_vocab}, frames: {has_frames})")
            
            if "vocabulary" in step_name.lower() or "cognate" in step_name.lower():
                vocab_step = step
            if content_type == "sentence_frames":
                frames_step = step
        
        # Check vocabulary step
        if vocab_step:
            vocab_data = vocab_step.get("vocabulary_cognates")
            print(f"\n[OK] Vocabulary step found: {vocab_step.get('step_name')}")
            print(f"     vocabulary_cognates type: {type(vocab_data)}")
            print(f"     vocabulary_cognates is list: {isinstance(vocab_data, list)}")
            if vocab_data and isinstance(vocab_data, list):
                print(f"[OK] Has {len(vocab_data)} vocabulary items")
                print(f"     Sample: {vocab_data[0].get('english')} -> {vocab_data[0].get('portuguese')}")
            else:
                print(f"[FAIL] vocabulary_cognates missing or not a list")
                print(f"        Value: {vocab_data}")
        else:
            print(f"\n[FAIL] No vocabulary step found")
        
        # Check frames step
        if frames_step:
            frames_data = frames_step.get("sentence_frames")
            print(f"\n[OK] Sentence frames step found: {frames_step.get('step_name')}")
            print(f"     sentence_frames type: {type(frames_data)}")
            print(f"     sentence_frames is list: {isinstance(frames_data, list)}")
            if frames_data and isinstance(frames_data, list):
                print(f"[OK] Has {len(frames_data)} sentence frames")
                print(f"     Sample: {frames_data[0].get('english', 'N/A')}")
            else:
                print(f"[FAIL] sentence_frames missing or not a list")
                print(f"        Value: {frames_data}")
        else:
            print(f"\n[FAIL] No sentence frames step found")
        
        return (vocab_step and vocab_step.get("vocabulary_cognates") and isinstance(vocab_step.get("vocabulary_cognates"), list)) and \
               (frames_step and frames_step.get("sentence_frames") and isinstance(frames_step.get("sentence_frames"), list))
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "=" * 80)
    print("  VOCABULARY & SENTENCE FRAMES PIPELINE DIAGNOSTIC")
    print("=" * 80)
    
    results = {}
    
    # Check 1: Source file
    source_data = check_source_file()
    results["source"] = source_data is not None
    
    if not source_data:
        print("\n[ERROR] Source file check failed. Cannot proceed.")
        return
    
    # Check 2: Backend
    if not check_backend_health():
        print("\n[ERROR] Backend is not running. Please start it first.")
        return
    results["backend"] = True
    
    # Check 3: Plan in DB
    plan_id, user_id = check_plan_in_db()
    if not plan_id:
        print("\n[ERROR] Plan not found in database.")
        print("        You may need to import the JSON file first.")
        return
    results["plan_found"] = True
    
    # Check 4: Lesson steps
    results["lesson_steps"] = check_lesson_steps(plan_id, user_id)
    
    # Summary
    print_section("DIAGNOSTIC SUMMARY")
    
    all_checks = [
        ("Source file has vocab/frames", results.get("source")),
        ("Backend is running", results.get("backend")),
        ("Plan found in database", results.get("plan_found")),
        ("Lesson steps have vocab/frames", results.get("lesson_steps")),
    ]
    
    for check_name, passed in all_checks:
        status = "[OK]" if passed else "[FAIL]"
        print(f"{status} {check_name}")
    
    print("\n" + "=" * 80)
    
    if all(passed for _, passed in all_checks if passed is not None):
        print("[SUCCESS] All checks passed! The pipeline should be working.")
    else:
        print("[ISSUE] Some checks failed. Review the output above to identify the problem.")
        print("\nCommon issues:")
        print("  1. Plan not imported - run batch processor or import script")
        print("  2. Lesson steps not generated - generate via API or frontend")
        print("  3. vocabulary_cognates/sentence_frames not in lesson_json - check import process")
        print("  4. Data not extracted during step generation - check backend logs")

if __name__ == "__main__":
    main()


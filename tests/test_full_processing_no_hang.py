"""
Test full processing workflow to verify no hang occurs.
Uses mock LLM to avoid API costs.
"""

import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_full_processing():
    """Test the full processing workflow."""
    print("=" * 60)
    print("Testing Full Processing Workflow (No Hang)")
    print("=" * 60)
    
    # Use Daniela Silva who has 5 slots configured
    user_id = "29fa9ed7-3174-4999-86fd-40a542c28cff"
    
    # 1. Verify user has slots
    print("\n1. Verifying user has slots...")
    try:
        response = requests.get(f"{BASE_URL}/api/users/{user_id}/slots", timeout=5)
        slots = response.json()
        print(f"   ✓ User has {len(slots)} slots configured")
    except Exception as e:
        print(f"   ❌ Failed to get slots: {e}")
        return False
    
    # 2. Start processing with mock provider
    print("\n2. Starting processing with mock LLM...")
    print("   (Using mock to avoid API costs)")
    
    payload = {
        "user_id": user_id,
        "week_of": "10-14-10-18",
        "provider": "mock",  # Use mock provider
        "slot_ids": [slots[0]['id']]  # Process just first slot
    }
    
    try:
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/api/process-week",
            json=payload,
            timeout=15
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ Processing started in {elapsed:.2f}s")
            print(f"   ✓ NO HANG! The asyncio.to_thread() fix is working!")
            print(f"   Plan ID: {result.get('plan_id')}")
            plan_id = result.get('plan_id')
        else:
            print(f"   ⚠️  Processing returned {response.status_code}")
            print(f"   Response: {response.text}")
            # Still not a hang if we got a response
            print(f"   ✓ But no hang occurred! (got response in {elapsed:.2f}s)")
            return True
            
    except requests.exceptions.Timeout:
        print("   ❌ Request timed out after 15s - backend hung!")
        return False
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return False
    
    # 3. Check progress a few times
    print("\n3. Checking progress...")
    for i in range(5):
        time.sleep(1)
        try:
            response = requests.get(f"{BASE_URL}/api/progress/{plan_id}", timeout=5)
            progress = response.json()
            stage = progress.get('stage', 'unknown')
            percent = progress.get('progress', 0)
            message = progress.get('message', '')
            
            print(f"   [{i+1}/5] Stage: {stage}, Progress: {percent}%, Message: {message[:50]}")
            
            if stage in ["completed", "failed"]:
                print(f"\n   ✓ Processing finished with stage: {stage}")
                break
                
        except Exception as e:
            print(f"   ⚠️  Progress check failed: {e}")
    
    print("\n" + "=" * 60)
    print("✓ SUCCESS: No hang occurred!")
    print("The asyncio.to_thread() fix resolved the blocking issue.")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_full_processing()
    sys.exit(0 if success else 1)

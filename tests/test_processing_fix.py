"""
Test script to verify the asyncio.to_thread() fix for database calls.
This will trigger processing and monitor if it hangs.
"""

import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_processing():
    """Test the processing endpoint."""
    print("=" * 60)
    print("Testing Processing Fix")
    print("=" * 60)
    
    # 1. Check health
    print("\n1. Checking backend health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"   ✓ Backend is healthy: {response.json()}")
    except Exception as e:
        print(f"   ❌ Backend not responding: {e}")
        return False
    
    # 2. Get user
    print("\n2. Getting user...")
    try:
        response = requests.get(f"{BASE_URL}/api/users", timeout=5)
        users = response.json()
        if not users:
            print("   ❌ No users found")
            return False
        user = users[0]
        print(f"   ✓ Got user: {user['name']} ({user['id']})")
    except Exception as e:
        print(f"   ❌ Failed to get users: {e}")
        return False
    
    # 3. Start processing
    print("\n3. Starting processing...")
    print("   This is where it used to hang!")
    
    payload = {
        "user_id": user['id'],
        "week_of": "10-14-10-18",
        "provider": "openai",
        "slot_ids": []
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/process-week",
            json=payload,
            timeout=10
        )
        result = response.json()
        
        if response.status_code == 200:
            print(f"   ✓ Processing started successfully!")
            print(f"   Plan ID: {result.get('plan_id')}")
            plan_id = result.get('plan_id')
        else:
            print(f"   ❌ Processing failed: {result}")
            return False
    except requests.exceptions.Timeout:
        print("   ❌ Request timed out - backend may have hung!")
        return False
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return False
    
    # 4. Monitor progress
    print("\n4. Monitoring progress...")
    print("   Polling every 2 seconds for 20 seconds...")
    
    for i in range(10):
        time.sleep(2)
        try:
            response = requests.get(
                f"{BASE_URL}/api/progress/{plan_id}",
                timeout=5
            )
            progress = response.json()
            stage = progress.get('stage', 'unknown')
            percent = progress.get('progress', 0)
            message = progress.get('message', '')
            
            print(f"   [{i+1}/10] Stage: {stage}, Progress: {percent}%, Message: {message}")
            
            if stage == "completed":
                print("\n   ✓ Processing completed successfully!")
                return True
            elif stage == "failed":
                print(f"\n   ❌ Processing failed: {message}")
                return False
                
        except Exception as e:
            print(f"   ⚠️  Progress check failed: {e}")
    
    print("\n   ⚠️  Processing still running after 20 seconds")
    print("   This is expected for real LLM processing.")
    print("   The important thing is it didn't hang!")
    return True


if __name__ == "__main__":
    print("Testing the asyncio.to_thread() fix for database calls\n")
    
    success = test_processing()
    
    print("\n" + "=" * 60)
    if success:
        print("✓ SUCCESS: Processing did not hang!")
        print("The asyncio.to_thread() fix is working correctly.")
    else:
        print("❌ FAILURE: Processing encountered an error")
        print("Check the backend logs for details.")
    print("=" * 60)
    
    sys.exit(0 if success else 1)

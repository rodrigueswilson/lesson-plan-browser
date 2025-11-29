"""
Test processing and capture backend logs in real-time.
"""

import requests
import time

BASE_URL = "http://127.0.0.1:8000"

print("Starting processing test...")
print("Watch the backend terminal for DEBUG output!")
print("=" * 60)

# Use Daniela Silva, process just first slot
user_id = "29fa9ed7-3174-4999-86fd-40a542c28cff"

# Get first slot
response = requests.get(f"{BASE_URL}/api/users/{user_id}/slots")
slots = response.json()
first_slot_id = slots[0]['id']

print(f"\nProcessing slot: {slots[0]['subject']} (Grade {slots[0]['grade']})")
print(f"Slot ID: {first_slot_id}")
print("\n" + "=" * 60)
print("CHECK BACKEND TERMINAL FOR DEBUG OUTPUT")
print("=" * 60 + "\n")

# Start processing
payload = {
    "user_id": user_id,
    "week_of": "10-14-10-18",
    "provider": "mock",
    "slot_ids": [first_slot_id]
}

response = requests.post(f"{BASE_URL}/api/process-week", json=payload)
result = response.json()

if response.status_code == 200:
    plan_id = result.get('plan_id')
    print(f"✓ Processing started, Plan ID: {plan_id}")
    print("\nMonitoring for 30 seconds...")
    
    for i in range(30):
        time.sleep(1)
        try:
            resp = requests.get(f"{BASE_URL}/api/progress/{plan_id}", timeout=2)
            if resp.status_code == 200:
                progress = resp.json()
                stage = progress.get('stage', 'unknown')
                percent = progress.get('progress', 0)
                print(f"  [{i+1:2d}s] Stage: {stage:12s} Progress: {percent:3d}%")
                
                if stage in ["completed", "failed"]:
                    print(f"\n✓ Processing {stage}!")
                    break
            else:
                print(f"  [{i+1:2d}s] Progress check returned {resp.status_code}")
        except Exception as e:
            print(f"  [{i+1:2d}s] Error: {str(e)[:50]}")
else:
    print(f"❌ Failed to start: {response.status_code}")
    print(result)

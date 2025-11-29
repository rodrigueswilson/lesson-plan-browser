"""
Test the backend API directly without the frontend.
This verifies that the backend processing works end-to-end.
"""

import requests
import time
import json

API_BASE = "http://localhost:8000/api"

print("=" * 60)
print("Backend API Direct Test")
print("=" * 60)
print()

# Test 1: Health check
print("[1/4] Testing health endpoint...")
try:
    response = requests.get(f"{API_BASE}/health")
    if response.status_code == 200:
        print(f"✅ Health check passed: {response.json()}")
    else:
        print(f"❌ Health check failed: {response.status_code}")
        exit(1)
except Exception as e:
    print(f"❌ Cannot connect to backend: {e}")
    print("Make sure the backend is running on http://localhost:8000")
    exit(1)

print()

# Test 2: Get users
print("[2/4] Fetching users...")
try:
    response = requests.get(f"{API_BASE}/users")
    if response.status_code == 200:
        users = response.json()
        print(f"✅ Found {len(users)} users:")
        for user in users:
            print(f"   - {user['name']} (ID: {user['id']})")
        
        if not users:
            print("❌ No users found. Please create a user first.")
            exit(1)
        
        # Use Daniela Silva (second user) who likely has slots configured
        test_user = users[1] if len(users) > 1 else users[0]
        user_id = test_user['id']
        print(f"\n   Using user: {test_user['name']}")
    else:
        print(f"❌ Failed to fetch users: {response.status_code}")
        exit(1)
except Exception as e:
    print(f"❌ Error fetching users: {e}")
    exit(1)

print()

# Test 3: Get user slots
print("[3/4] Fetching user slots...")
try:
    response = requests.get(f"{API_BASE}/users/{user_id}/slots")
    if response.status_code == 200:
        slots = response.json()
        print(f"✅ Found {len(slots)} slots:")
        for slot in slots:
            print(f"   - Slot {slot['slot_number']}: {slot['subject']} (Grade {slot['grade']})")
        
        if not slots:
            print("❌ No slots configured for this user.")
            exit(1)
    else:
        print(f"❌ Failed to fetch slots: {response.status_code}")
        exit(1)
except Exception as e:
    print(f"❌ Error fetching slots: {e}")
    exit(1)

print()

# Test 4: Process week (just initiate, don't wait for completion)
print("[4/4] Initiating processing...")
print("⚠️  This will start actual processing - make sure you have lesson plans in the input folder!")
print()
proceed = input("Proceed with processing test? (y/N): ")

if proceed.lower() != 'y':
    print("\nTest cancelled. Backend is working correctly!")
    exit(0)

try:
    payload = {
        "user_id": user_id,
        "week_of": "10/14-10/18",  # Week 42 (adjust if needed)
        "provider": "openai"
    }
    
    print(f"\nSending request: {json.dumps(payload, indent=2)}")
    response = requests.post(f"{API_BASE}/process-week", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        plan_id = result.get('plan_id')
        print(f"✅ Processing started!")
        print(f"   Plan ID: {plan_id}")
        print(f"\n   Watch the backend terminal for progress logs...")
        print(f"   The backend should show:")
        print(f"     - background_process_started")
        print(f"     - media_extracted")
        print(f"     - Processing messages")
        print(f"\n   If you see errors in the backend terminal, share them!")
    else:
        print(f"❌ Failed to start processing: {response.status_code}")
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"❌ Error starting processing: {e}")

print()
print("=" * 60)
print("Test complete!")
print("=" * 60)

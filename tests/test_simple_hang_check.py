"""
Simple test to check if get_user_slots hangs in the backend.
"""

import requests
import time

BASE_URL = "http://127.0.0.1:8000"

print("Testing if get_user_slots hangs...")
print("=" * 60)

# Use Daniela Silva who has 5 slots
user_id = "29fa9ed7-3174-4999-86fd-40a542c28cff"

print(f"\n1. Getting slots for user: {user_id}")
print("   (This used to hang indefinitely)")

start = time.time()
try:
    response = requests.get(
        f"{BASE_URL}/api/users/{user_id}/slots",
        timeout=10
    )
    elapsed = time.time() - start
    
    if response.status_code == 200:
        slots = response.json()
        print(f"   ✓ Got {len(slots)} slots in {elapsed:.2f}s")
        print(f"   ✓ NO HANG! The fix is working!")
        
        for slot in slots:
            print(f"      - Slot {slot['slot_number']}: {slot['subject']} Grade {slot['grade']}")
    else:
        print(f"   ❌ Error: {response.status_code} - {response.text}")
        
except requests.exceptions.Timeout:
    print(f"   ❌ TIMEOUT after 10 seconds - still hanging!")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("Test complete!")

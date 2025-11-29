"""
Add slots for Wilson Rodrigues via API.
You can modify this script to add the slots Wilson needs.
"""

import requests
import sys

BASE_URL = "http://127.0.0.1:8000"
WILSON_USER_ID = "8d3154dc-1d16-4b9c-9b30-07397630465e"

# Define slots to add - modify this list as needed
SLOTS_TO_ADD = [
    # Example slots - modify these to match what Wilson needs
    # {
    #     "slot_number": 2,
    #     "subject": "ELA",
    #     "grade": "3",
    #     "homeroom": "",
    #     "proficiency_levels": "1,2,3",
    #     "primary_teacher_first_name": "",
    #     "primary_teacher_last_name": ""
    # },
]

def add_slot(slot_data):
    """Add a slot via API."""
    try:
        response = requests.post(
            f"{BASE_URL}/api/users/{WILSON_USER_ID}/slots",
            json=slot_data,
            timeout=10
        )
        if response.status_code == 200:
            slot = response.json()
            print(f"[OK] Created Slot {slot['slot_number']}: {slot['subject']} - Grade {slot['grade']}")
            return True
        else:
            print(f"[ERROR] Failed to create slot: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"[ERROR] Error creating slot: {e}")
        return False

def main():
    print("=" * 60)
    print("Add Slots for Wilson Rodrigues")
    print("=" * 60)
    
    if not SLOTS_TO_ADD:
        print("\nNo slots defined in SLOTS_TO_ADD.")
        print("Edit this script to add the slots Wilson needs.")
        print("\nExample:")
        print("""
SLOTS_TO_ADD = [
    {
        "slot_number": 2,
        "subject": "ELA",
        "grade": "3",
        "homeroom": "",
        "proficiency_levels": "1,2,3",
        "primary_teacher_first_name": "Teacher",
        "primary_teacher_last_name": "Name"
    },
]
        """)
        return 0
    
    print(f"\nWill add {len(SLOTS_TO_ADD)} slot(s) for Wilson...")
    
    success_count = 0
    for slot_data in SLOTS_TO_ADD:
        if add_slot(slot_data):
            success_count += 1
    
    print(f"\n{'=' * 60}")
    print(f"Results: {success_count}/{len(SLOTS_TO_ADD)} slots created")
    print(f"{'=' * 60}")
    
    return 0 if success_count == len(SLOTS_TO_ADD) else 1

if __name__ == "__main__":
    sys.exit(main())


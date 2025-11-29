"""
Check Wilson's slots in both Supabase projects.
"""

import os
import sys
from backend.config import Settings
from supabase import create_client

WILSON_USER_ID = "8d3154dc-1d16-4b9c-9b30-07397630465e"

settings = Settings()

print("=" * 60)
print("Checking Wilson Rodrigues in Both Supabase Projects")
print("=" * 60)

# Check Project 1
print("\n[Project 1 - Wilson's Project]")
try:
    if settings.SUPABASE_URL_PROJECT1 and settings.SUPABASE_KEY_PROJECT1:
        client1 = create_client(settings.SUPABASE_URL_PROJECT1, settings.SUPABASE_KEY_PROJECT1)
        
        # Check if user exists
        user_response = client1.table("users").select("*").eq("id", WILSON_USER_ID).execute()
        if user_response.data:
            user = user_response.data[0]
            print(f"User found: {user.get('name')} ({user.get('email')})")
            
            # Get slots
            slots_response = client1.table("class_slots").select("*").eq("user_id", WILSON_USER_ID).order("slot_number").execute()
            slots = slots_response.data
            print(f"\nSlots in Project 1: {len(slots)}")
            for slot in slots:
                print(f"  Slot {slot['slot_number']}: {slot['subject']} - Grade {slot['grade']} (Homeroom: {slot.get('homeroom') or 'N/A'})")
        else:
            print("User not found in Project 1")
    else:
        print("Project 1 credentials not configured")
except Exception as e:
    print(f"Error checking Project 1: {e}")

# Check Project 2
print("\n[Project 2 - Daniela's Project]")
try:
    if settings.SUPABASE_URL_PROJECT2 and settings.SUPABASE_KEY_PROJECT2:
        client2 = create_client(settings.SUPABASE_URL_PROJECT2, settings.SUPABASE_KEY_PROJECT2)
        
        # Check if user exists
        user_response = client2.table("users").select("*").eq("id", WILSON_USER_ID).execute()
        if user_response.data:
            user = user_response.data[0]
            print(f"User found: {user.get('name')} ({user.get('email')})")
            
            # Get slots
            slots_response = client2.table("class_slots").select("*").eq("user_id", WILSON_USER_ID).order("slot_number").execute()
            slots = slots_response.data
            print(f"\nSlots in Project 2: {len(slots)}")
            for slot in slots:
                print(f"  Slot {slot['slot_number']}: {slot['subject']} - Grade {slot['grade']} (Homeroom: {slot.get('homeroom') or 'N/A'})")
        else:
            print("User not found in Project 2")
    else:
        print("Project 2 credentials not configured")
except Exception as e:
    print(f"Error checking Project 2: {e}")

print("\n" + "=" * 60)
print("Summary")
print("=" * 60)
print("\nWilson should be in Project 1 (project1).")
print("If slots are missing, they may need to be recreated.")


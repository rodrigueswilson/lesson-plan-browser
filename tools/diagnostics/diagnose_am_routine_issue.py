"""Diagnose A.M. Routine issue for User 2 (Daniela Silva).

This script investigates why User 2's A.M. Routine slot at 08:15-08:30
incorrectly shows a lesson plan when clicked, while User 1's correctly does nothing.
"""

import os
from backend.config import Settings
from supabase import create_client
from backend.utils.schedule_utils import is_non_class_period, normalize_subject

settings = Settings()

# User IDs
USER_1_ID = "04fe8898-cb89-4a73-affb-64a97a98f820"  # Wilson Rodrigues
USER_2_ID = "29fa9ed7-3174-4999-86fd-40a542c28cff"  # Daniela Silva

print("=" * 80)
print("Diagnosing A.M. Routine Click Issue")
print("=" * 80)

def check_user_schedules(client, user_id, user_name, project_name):
    """Check schedule entries for a specific user."""
    print(f"\n{'='*80}")
    print(f"Checking {user_name} (User ID: {user_id}) in {project_name}")
    print(f"{'='*80}")
    
    try:
        # Get all schedule entries for this user
        response = client.table("schedules").select("*").eq("user_id", user_id).execute()
        all_entries = response.data
        
        print(f"\nTotal schedule entries: {len(all_entries)}")
        
        # Filter for A.M. Routine entries (all variations)
        am_routine_entries = []
        for entry in all_entries:
            subject = entry.get('subject', '') or ''
            subject_upper = subject.upper()
            if any(variant in subject_upper for variant in ['A.M. ROUTINE', 'AM ROUTINE', 'MORNING ROUTINE']):
                am_routine_entries.append(entry)
        
        print(f"\nA.M. Routine entries found: {len(am_routine_entries)}")
        
        if am_routine_entries:
            print("\nDetailed A.M. Routine Entry Information:")
            print("-" * 80)
            for i, entry in enumerate(am_routine_entries, 1):
                print(f"\nEntry {i}:")
                print(f"  ID: {entry.get('id')}")
                print(f"  Subject: '{entry.get('subject')}'")
                print(f"  Normalized: '{normalize_subject(entry.get('subject', ''))}'")
                print(f"  Is Non-Class Period: {is_non_class_period(entry.get('subject', ''))}")
                print(f"  Day: {entry.get('day_of_week')}")
                print(f"  Time: {entry.get('start_time')} - {entry.get('end_time')}")
                print(f"  Slot Number: {entry.get('slot_number')}")
                print(f"  Is Active: {entry.get('is_active')}")
                print(f"  Grade: {entry.get('grade')}")
                print(f"  Homeroom: {entry.get('homeroom')}")
                print(f"  Plan Slot Group ID: {entry.get('plan_slot_group_id')}")
                
                # Check for entries at 08:15-08:30
                if entry.get('start_time') == '08:15' and entry.get('end_time') == '08:30':
                    print(f"  *** THIS IS THE PROBLEMATIC TIME SLOT ***")
                    
                    # Check if there are other entries at the same time
                    same_time_entries = [
                        e for e in all_entries
                        if e.get('day_of_week') == entry.get('day_of_week')
                        and e.get('start_time') == '08:15'
                        and e.get('end_time') == '08:30'
                        and e.get('id') != entry.get('id')
                    ]
                    if same_time_entries:
                        print(f"  WARNING: Found {len(same_time_entries)} other entries at same time slot:")
                        for other in same_time_entries:
                            print(f"    - ID: {other.get('id')}, Subject: '{other.get('subject')}', Is Active: {other.get('is_active')}")
        else:
            print("\nNo A.M. Routine entries found for this user.")
        
        # Check for entries at 08:15-08:30 regardless of subject
        print(f"\n{'='*80}")
        print("All entries at 08:15-08:30:")
        print(f"{'='*80}")
        time_slot_entries = [
            e for e in all_entries
            if e.get('start_time') == '08:15' and e.get('end_time') == '08:30'
        ]
        
        if time_slot_entries:
            for entry in time_slot_entries:
                print(f"\n  Subject: '{entry.get('subject')}'")
                print(f"    Day: {entry.get('day_of_week')}")
                print(f"    Is Active: {entry.get('is_active')}")
                print(f"    Is Non-Class: {is_non_class_period(entry.get('subject', ''))}")
                print(f"    ID: {entry.get('id')}")
        else:
            print("  No entries found at 08:15-08:30")
            
    except Exception as e:
        print(f"Error checking {user_name}: {e}")
        import traceback
        traceback.print_exc()

# Check both projects
if settings.SUPABASE_URL_PROJECT1 and settings.SUPABASE_KEY_PROJECT1:
    print("\nChecking Project 1 (Wilson Rodrigues)...")
    try:
        client1 = create_client(settings.SUPABASE_URL_PROJECT1, settings.SUPABASE_KEY_PROJECT1)
        check_user_schedules(client1, USER_1_ID, "Wilson Rodrigues", "Project 1")
    except Exception as e:
        print(f"Error accessing Project 1: {e}")

if settings.SUPABASE_URL_PROJECT2 and settings.SUPABASE_KEY_PROJECT2:
    print("\nChecking Project 2 (Daniela Silva)...")
    try:
        client2 = create_client(settings.SUPABASE_URL_PROJECT2, settings.SUPABASE_KEY_PROJECT2)
        check_user_schedules(client2, USER_2_ID, "Daniela Silva", "Project 2")
    except Exception as e:
        print(f"Error accessing Project 2: {e}")

print("\n" + "=" * 80)
print("Diagnosis Complete")
print("=" * 80)
print("\nSummary:")
print("- Check if User 2's A.M. Routine entries have is_active=true (should be false)")
print("- Check if subject field doesn't match isNonClassPeriod() exactly")
print("- Check if there are duplicate entries at the same time slot")
print("- Check if there are both lesson and non-class entries at 08:15-08:30")


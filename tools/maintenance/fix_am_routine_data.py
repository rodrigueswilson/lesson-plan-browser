"""Fix A.M. Routine data issues for User 2 (Daniela Silva).

This script should be run AFTER diagnose_am_routine_issue.py reveals data problems.
It will:
- Update all A.M. Routine entries to have is_active: false
- Normalize subject names to "A.M. Routine"
- Clear grade, homeroom, and plan_slot_group_id for non-class periods
"""

import os
from backend.config import Settings
from supabase import create_client
from backend.utils.schedule_utils import is_non_class_period, normalize_subject

settings = Settings()

# User IDs
USER_2_ID = "29fa9ed7-3174-4999-86fd-40a542c28cff"  # Daniela Silva

print("=" * 80)
print("Fixing A.M. Routine Data Issues for User 2")
print("=" * 80)
print("\nWARNING: This script will modify database entries.")
print("Make sure you have run diagnose_am_routine_issue.py first to identify issues.")
print()

response = input("Do you want to proceed? (yes/no): ")
if response.lower() != 'yes':
    print("Aborted.")
    exit(0)

if not settings.SUPABASE_URL_PROJECT2 or not settings.SUPABASE_KEY_PROJECT2:
    print("ERROR: Project 2 (Daniela Silva) credentials not configured")
    exit(1)

try:
    client = create_client(settings.SUPABASE_URL_PROJECT2, settings.SUPABASE_KEY_PROJECT2)
    
    # Get all schedule entries for User 2
    response = client.table("schedules").select("*").eq("user_id", USER_2_ID).execute()
    all_entries = response.data
    
    print(f"\nTotal schedule entries for User 2: {len(all_entries)}")
    
    # Find all A.M. Routine entries (all variations)
    am_routine_entries = []
    for entry in all_entries:
        subject = entry.get('subject', '') or ''
        subject_upper = subject.upper()
        if any(variant in subject_upper for variant in ['A.M. ROUTINE', 'AM ROUTINE', 'MORNING ROUTINE']):
            am_routine_entries.append(entry)
    
    print(f"\nA.M. Routine entries found: {len(am_routine_entries)}")
    
    if not am_routine_entries:
        print("No A.M. Routine entries found. Nothing to fix.")
        exit(0)
    
    # Fix each entry
    fixed_count = 0
    for entry in am_routine_entries:
        entry_id = entry.get('id')
        current_subject = entry.get('subject', '')
        current_is_active = entry.get('is_active')
        current_grade = entry.get('grade')
        current_homeroom = entry.get('homeroom')
        current_group_id = entry.get('plan_slot_group_id')
        
        # Determine what needs to be fixed
        needs_fix = False
        updates = {}
        
        # Normalize subject to "A.M. Routine"
        normalized_subject = normalize_subject(current_subject)
        if normalized_subject != "A.M. Routine":
            normalized_subject = "A.M. Routine"
        
        if current_subject != normalized_subject:
            updates['subject'] = normalized_subject
            needs_fix = True
        
        # Set is_active to false
        if current_is_active is not False:
            updates['is_active'] = False
            needs_fix = True
        
        # Clear grade if present
        if current_grade is not None:
            updates['grade'] = None
            needs_fix = True
        
        # Clear homeroom if present
        if current_homeroom is not None:
            updates['homeroom'] = None
            needs_fix = True
        
        # Clear plan_slot_group_id if present
        if current_group_id is not None:
            updates['plan_slot_group_id'] = None
            needs_fix = True
        
        if needs_fix:
            print(f"\nFixing entry {entry_id}:")
            print(f"  Day: {entry.get('day_of_week')}, Time: {entry.get('start_time')}-{entry.get('end_time')}")
            print(f"  Old subject: '{current_subject}' -> New: '{normalized_subject}'")
            print(f"  Old is_active: {current_is_active} -> New: False")
            if current_grade:
                print(f"  Clearing grade: {current_grade}")
            if current_homeroom:
                print(f"  Clearing homeroom: {current_homeroom}")
            if current_group_id:
                print(f"  Clearing plan_slot_group_id: {current_group_id}")
            
            # Update the entry
            try:
                client.table("schedules").update(updates).eq("id", entry_id).execute()
                fixed_count += 1
                print(f"  ✓ Fixed")
            except Exception as e:
                print(f"  ✗ Error updating entry {entry_id}: {e}")
        else:
            print(f"\nEntry {entry_id} is already correct (subject: '{current_subject}', is_active: {current_is_active})")
    
    print("\n" + "=" * 80)
    print(f"Fix Complete: {fixed_count} entries updated")
    print("=" * 80)
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)


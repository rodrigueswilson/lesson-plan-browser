"""
Migrate Wilson's 6 slots from Project 1 to Project 2.
"""

import sys
import uuid
from backend.config import Settings
from supabase import create_client

# Original Wilson in Project 1 (has 6 slots)
ORIGINAL_WILSON_ID = "04fe8898-cb89-4a73-affb-64a97a98f820"

# Current Wilson in Project 2 (needs the slots)
CURRENT_WILSON_ID = "8d3154dc-1d16-4b9c-9b30-07397630465e"

settings = Settings()

print("=" * 60)
print("Migrating Wilson's Slots from Project 1 to Project 2")
print("=" * 60)

# Get slots from Project 1
print("\n[Step 1] Fetching slots from Project 1...")
try:
    client1 = create_client(settings.SUPABASE_URL_PROJECT1, settings.SUPABASE_KEY_PROJECT1)
    slots_response = client1.table("class_slots").select("*").eq("user_id", ORIGINAL_WILSON_ID).order("slot_number").execute()
    original_slots = slots_response.data
    
    print(f"Found {len(original_slots)} slot(s) in Project 1:")
    for slot in original_slots:
        print(f"  Slot {slot['slot_number']}: {slot['subject']} - Grade {slot['grade']} (Homeroom: {slot.get('homeroom') or 'N/A'})")
except Exception as e:
    print(f"Error fetching slots from Project 1: {e}")
    sys.exit(1)

# Check current slots in Project 2
print("\n[Step 2] Checking current slots in Project 2...")
try:
    client2 = create_client(settings.SUPABASE_URL_PROJECT2, settings.SUPABASE_KEY_PROJECT2)
    current_slots_response = client2.table("class_slots").select("*").eq("user_id", CURRENT_WILSON_ID).order("slot_number").execute()
    current_slots = current_slots_response.data
    
    print(f"Found {len(current_slots)} slot(s) in Project 2:")
    for slot in current_slots:
        print(f"  Slot {slot['slot_number']}: {slot['subject']} - Grade {slot['grade']} (Homeroom: {slot.get('homeroom') or 'N/A'})")
except Exception as e:
    print(f"Error checking slots in Project 2: {e}")
    sys.exit(1)

# Prepare slots for migration
print("\n[Step 3] Preparing slots for migration...")
slots_to_migrate = []
existing_slot_numbers = {slot['slot_number'] for slot in current_slots}

for slot in original_slots:
    slot_number = slot['slot_number']
    
    # Skip if slot number already exists in Project 2
    if slot_number in existing_slot_numbers:
        print(f"  Skipping Slot {slot_number} (already exists in Project 2)")
        continue
    
    # Prepare slot data (change user_id to current Wilson, generate new ID)
    slot_data = {
        'id': str(uuid.uuid4()),  # Generate new UUID for the slot
        'user_id': CURRENT_WILSON_ID,
        'slot_number': slot['slot_number'],
        'subject': slot['subject'],
        'grade': slot['grade'],
        'homeroom': slot.get('homeroom'),
        'proficiency_levels': slot.get('proficiency_levels'),
        'primary_teacher_file': slot.get('primary_teacher_file'),
        'primary_teacher_name': slot.get('primary_teacher_name'),
        'primary_teacher_first_name': slot.get('primary_teacher_first_name'),
        'primary_teacher_last_name': slot.get('primary_teacher_last_name'),
        'primary_teacher_file_pattern': slot.get('primary_teacher_file_pattern'),
        'display_order': slot.get('display_order'),
    }
    slots_to_migrate.append(slot_data)
    print(f"  Will migrate Slot {slot_number}: {slot['subject']} - Grade {slot['grade']}")

if not slots_to_migrate:
    print("\nNo slots to migrate (all slots already exist in Project 2)")
    sys.exit(0)

# Confirm migration
print(f"\n[Step 4] Ready to migrate {len(slots_to_migrate)} slot(s)")
print("Proceeding with migration...")

# Migrate slots to Project 2
print("\n[Step 5] Migrating slots to Project 2...")
success_count = 0
for slot_data in slots_to_migrate:
    try:
        # Remove None values
        slot_data_clean = {k: v for k, v in slot_data.items() if v is not None}
        
        result = client2.table("class_slots").insert(slot_data_clean).execute()
        if result.data:
            print(f"  [OK] Migrated Slot {slot_data['slot_number']}: {slot_data['subject']} - Grade {slot_data['grade']}")
            success_count += 1
        else:
            print(f"  [ERROR] Failed to migrate Slot {slot_data['slot_number']}")
    except Exception as e:
        print(f"  [ERROR] Failed to migrate Slot {slot_data['slot_number']}: {e}")

# Verify migration
print("\n[Step 6] Verifying migration...")
try:
    final_slots_response = client2.table("class_slots").select("*").eq("user_id", CURRENT_WILSON_ID).order("slot_number").execute()
    final_slots = final_slots_response.data
    
    print(f"\nWilson now has {len(final_slots)} slot(s) in Project 2:")
    for slot in final_slots:
        print(f"  Slot {slot['slot_number']}: {slot['subject']} - Grade {slot['grade']} (Homeroom: {slot.get('homeroom') or 'N/A'})")
    
    print("\n" + "=" * 60)
    print(f"Migration Complete: {success_count}/{len(slots_to_migrate)} slots migrated")
    print("=" * 60)
except Exception as e:
    print(f"Error verifying migration: {e}")


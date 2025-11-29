"""Check Wilson's current slot configuration."""
from backend.database import get_db

db = get_db()
wilson_id = "04fe8898-cb89-4a73-affb-64a97a98f820"
slots = db.get_user_slots(wilson_id)

print("="*80)
print("WILSON'S CURRENT SLOT CONFIGURATION")
print("="*80)
print()

for slot in slots:
    print(f"Slot {slot['slot_number']}: {slot['subject']}")
    print(f"  Teacher Name: {slot.get('primary_teacher_name', 'NULL')}")
    print(f"  Teacher First: {slot.get('primary_teacher_first_name', 'NULL')}")
    print(f"  Teacher Last: {slot.get('primary_teacher_last_name', 'NULL')}")
    print(f"  File Pattern: {slot.get('primary_teacher_file_pattern', 'NULL')}")
    print(f"  File Path: {slot.get('primary_teacher_file', 'NULL')}")
    print()

print("="*80)
print("FILES IN W44 FOLDER:")
print("="*80)
import os
folder = r"F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W44"
if os.path.exists(folder):
    files = [f for f in os.listdir(folder) if f.endswith('.docx')]
    for f in files:
        print(f"  - {f}")
else:
    print("  Folder not found!")

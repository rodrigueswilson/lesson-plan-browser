"""Debug file resolution logic."""
from backend.database import get_db
from backend.file_manager import get_file_manager
from pathlib import Path
import os

db = get_db()
wilson_id = "04fe8898-cb89-4a73-affb-64a97a98f820"
slots = db.get_user_slots(wilson_id)
user = db.get_user(wilson_id)

week_of = "10-27-10-31"
base_path = user.get("base_path_override")

print("="*80)
print("FILE RESOLUTION DEBUG")
print("="*80)
print(f"User: {user['name']}")
print(f"Base path: {base_path}")
print(f"Week: {week_of}")
print()

# Get week folder
file_mgr = get_file_manager(base_path=base_path)
week_folder = file_mgr.get_week_folder(week_of)

print(f"Week folder: {week_folder}")
print(f"Folder exists: {week_folder.exists()}")
print()

if week_folder.exists():
    print("Files in folder:")
    for f in week_folder.iterdir():
        if f.suffix == '.docx':
            print(f"  - {f.name}")
    print()

print("="*80)
print("SLOT RESOLUTION ATTEMPTS")
print("="*80)
print()

for slot in slots:
    print(f"Slot {slot['slot_number']}: {slot['subject']}")
    print(f"  Teacher pattern: {slot.get('primary_teacher_file_pattern', 'NULL')}")
    print(f"  Teacher name: {slot.get('primary_teacher_name', 'NULL')}")
    print(f"  Primary file: {slot.get('primary_teacher_file', 'NULL')}")
    
    # Try to find file using pattern
    pattern = slot.get('primary_teacher_file_pattern') or slot.get('primary_teacher_name')
    
    if pattern and week_folder.exists():
        print(f"  Looking for pattern: '{pattern}'")
        found = []
        for f in week_folder.iterdir():
            if f.suffix == '.docx' and pattern.lower() in f.name.lower():
                found.append(f.name)
        
        if found:
            print(f"  ✅ FOUND: {found}")
        else:
            print(f"  ❌ NOT FOUND")
    else:
        print(f"  ⚠️  No pattern to search")
    
    print()

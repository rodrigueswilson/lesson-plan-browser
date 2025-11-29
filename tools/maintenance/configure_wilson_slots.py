"""Configure Wilson's slots to use W44 files."""
from backend.database import get_db

db = get_db()
wilson_id = "04fe8898-cb89-4a73-affb-64a97a98f820"

# Get Wilson's slots
slots = db.get_user_slots(wilson_id)

print("Configuring Wilson's slots for W44...")
print()

# We have these files in W44:
# 1. "10_27-10_31 Davies Lesson Plans.docx"
# 2. "Lang Lesson Plans 10_27_25-10_31_25.docx"

for slot in slots:
    slot_num = slot['slot_number']
    subject = slot['subject']
    
    # Configure based on what we know
    if 'ELA' in subject and slot_num == 1:
        # Slot 1: ELA - use Davies
        db.update_class_slot(
            slot['id'],
            primary_teacher_first_name="",
            primary_teacher_last_name="Davies",
            primary_teacher_file_pattern="Davies"
        )
        print(f"✅ Slot {slot_num} ({subject}): Configured for Davies")
    
    elif 'ELA' in subject and slot_num == 2:
        # Slot 2: ELA/SS - use Lang
        db.update_class_slot(
            slot['id'],
            primary_teacher_first_name="Sarah",
            primary_teacher_last_name="Lang",
            primary_teacher_file_pattern="Lang"
        )
        print(f"✅ Slot {slot_num} ({subject}): Configured for Lang")
    
    elif 'Science' in subject:
        # Slot 3: Science - use Davies
        db.update_class_slot(
            slot['id'],
            primary_teacher_first_name="",
            primary_teacher_last_name="Davies",
            primary_teacher_file_pattern="Davies"
        )
        print(f"✅ Slot {slot_num} ({subject}): Configured for Davies")
    
    elif 'Math' in subject:
        # Slots 4-5: Math - use Lang
        db.update_class_slot(
            slot['id'],
            primary_teacher_first_name="Sarah",
            primary_teacher_last_name="Lang",
            primary_teacher_file_pattern="Lang"
        )
        print(f"✅ Slot {slot_num} ({subject}): Configured for Lang")

print()
print("=" * 80)
print("✅ Configuration complete!")
print("=" * 80)
print()
print("Now try processing W44 again. The system should find:")
print("  - Davies file for ELA and Science slots")
print("  - Lang file for ELA/SS and Math slots")

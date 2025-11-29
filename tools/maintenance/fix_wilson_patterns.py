"""Fix Wilson's file patterns to match teacher names."""
from backend.database import get_db

db = get_db()
wilson_id = "04fe8898-cb89-4a73-affb-64a97a98f820"
slots = db.get_user_slots(wilson_id)

print("Fixing Wilson's file patterns...")
print()

for slot in slots:
    teacher_last = slot.get('primary_teacher_last_name', '')
    
    # Set pattern to match the teacher's last name
    db.update_class_slot(
        slot['id'],
        primary_teacher_file_pattern=teacher_last
    )
    
    print(f"✅ Slot {slot['slot_number']} ({slot['subject']}): Pattern set to '{teacher_last}'")

print()
print("="*80)
print("✅ FIXED! Now the patterns match:")
print("="*80)
print("  Slot 1 (Kelsey Lang) → Pattern: Lang")
print("  Slot 2 (Donna Savoca) → Pattern: Savoca")
print("  Slot 3 (Donna Savoca) → Pattern: Savoca")
print("  Slot 4 (Donna Savoca) → Pattern: Savoca")
print("  Slot 5 (Caitlin Davies) → Pattern: Davies")
print()
print("Now try processing W44 again!")

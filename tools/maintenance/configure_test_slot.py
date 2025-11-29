"""Configure a test slot with a real file for testing."""

from backend.database import get_db
from pathlib import Path

db = get_db()

# Get Daniela Silva
users = db.list_users()
daniela = next((u for u in users if 'Daniela' in u['name']), None)

if not daniela:
    print("❌ Daniela Silva not found")
    exit(1)

print(f"✓ Found user: {daniela['name']}")

# Get her slots
slots = db.get_user_slots(daniela['id'])
if not slots:
    print("❌ No slots found")
    exit(1)

print(f"✓ Found {len(slots)} slots")

# Use first slot (ELA/SS)
slot = slots[0]
print(f"✓ Using Slot {slot['slot_number']}: {slot['subject']}")

# Set a test file - use Lang's lesson plan (has hyperlinks)
test_file = str(Path("d:/LP/input/Lang Lesson Plans 9_15_25-9_19_25.docx").absolute())

print(f"\n📝 Configuring slot with test file:")
print(f"   {test_file}")

# Check if file exists
if not Path(test_file).exists():
    print(f"\n❌ File not found: {test_file}")
    exit(1)

print(f"✓ File exists")

# Update slot
try:
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE class_slots SET primary_teacher_file = ? WHERE id = ?",
            (test_file, slot['id'])
        )
        conn.commit()
    
    print(f"\n✅ SUCCESS! Slot configured.")
    print(f"\nNow you can run:")
    print(f"   python test_hyperlink_simple.py")
    
except Exception as e:
    print(f"\n❌ Failed to update slot: {e}")

"""Verify migration was successful."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.database import Database

db = Database()

print("="*80)
print("MIGRATION VERIFICATION")
print("="*80)

# Check schema
print("\n1. Checking schema...")
with db.get_connection() as conn:
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("PRAGMA table_info(users)")
    user_columns = [row[1] for row in cursor.fetchall()]
    print(f"\nUsers table columns: {', '.join(user_columns)}")
    
    has_first = 'first_name' in user_columns
    has_last = 'last_name' in user_columns
    print(f"  ✓ first_name: {'YES' if has_first else 'NO'}")
    print(f"  ✓ last_name: {'YES' if has_last else 'NO'}")
    
    # Class slots table
    cursor.execute("PRAGMA table_info(class_slots)")
    slot_columns = [row[1] for row in cursor.fetchall()]
    print(f"\nClass slots table columns: {', '.join(slot_columns)}")
    
    has_teacher_first = 'primary_teacher_first_name' in slot_columns
    has_teacher_last = 'primary_teacher_last_name' in slot_columns
    print(f"  ✓ primary_teacher_first_name: {'YES' if has_teacher_first else 'NO'}")
    print(f"  ✓ primary_teacher_last_name: {'YES' if has_teacher_last else 'NO'}")

# Check data
print("\n2. Checking migrated data...")
users = db.list_users()
print(f"\nFound {len(users)} users:")
for user in users:
    name = user['name']
    first = user.get('first_name', 'NULL')
    last = user.get('last_name', 'NULL')
    print(f"  - {name}")
    print(f"      first_name: '{first}'")
    print(f"      last_name: '{last}'")
    print(f"      Status: {'✓ Complete' if first and last else '⚠️  Needs review'}")

print(f"\nChecking slots...")
total_slots = 0
complete_slots = 0
for user in users:
    slots = db.get_user_slots(user['id'])
    total_slots += len(slots)
    for slot in slots:
        teacher = slot.get('primary_teacher_name', '')
        first = slot.get('primary_teacher_first_name', '')
        last = slot.get('primary_teacher_last_name', '')
        if first and last:
            complete_slots += 1

print(f"  Total slots: {total_slots}")
print(f"  Complete (first + last): {complete_slots}")
print(f"  Need review: {total_slots - complete_slots}")

print("\n" + "="*80)
print("✅ MIGRATION VERIFICATION COMPLETE")
print("="*80)

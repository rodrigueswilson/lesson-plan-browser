"""Test updated database CRUD methods with structured names."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.database import Database

print("="*80)
print("DATABASE CRUD TESTS - Structured Names")
print("="*80)

db = Database()

# Test 1: Create user with first/last name
print("\n1. Testing create_user with first_name/last_name...")
user_id = db.create_user(
    first_name="Test",
    last_name="User",
    email="test@example.com"
)
user = db.get_user(user_id)
print(f"  Created user: {user['name']}")
print(f"    first_name: '{user['first_name']}'")
print(f"    last_name: '{user['last_name']}'")
assert user['first_name'] == "Test", "First name mismatch"
assert user['last_name'] == "User", "Last name mismatch"
assert user['name'] == "Test User", "Computed name mismatch"
print("  ✓ PASS")

# Test 2: Create user with backward compatibility (name only)
print("\n2. Testing create_user with name only (backward compat)...")
user_id2 = db.create_user(name="Jane Doe")
user2 = db.get_user(user_id2)
print(f"  Created user: {user2['name']}")
print(f"    first_name: '{user2['first_name']}'")
print(f"    last_name: '{user2['last_name']}'")
assert user2['first_name'] == "Jane", "First name not split correctly"
assert user2['last_name'] == "Doe", "Last name not split correctly"
assert user2['name'] == "Jane Doe", "Name not preserved"
print("  ✓ PASS")

# Test 3: Update user first/last name
print("\n3. Testing update_user with first_name/last_name...")
success = db.update_user(
    user_id,
    first_name="Updated",
    last_name="Name"
)
user = db.get_user(user_id)
print(f"  Updated user: {user['name']}")
print(f"    first_name: '{user['first_name']}'")
print(f"    last_name: '{user['last_name']}'")
assert user['first_name'] == "Updated", "First name not updated"
assert user['last_name'] == "Name", "Last name not updated"
assert user['name'] == "Updated Name", "Computed name not updated"
print("  ✓ PASS")

# Test 4: Update user with name only (backward compat)
print("\n4. Testing update_user with name only (backward compat)...")
success = db.update_user(user_id2, name="John Smith")
user2 = db.get_user(user_id2)
print(f"  Updated user: {user2['name']}")
print(f"    first_name: '{user2['first_name']}'")
print(f"    last_name: '{user2['last_name']}'")
assert user2['first_name'] == "John", "First name not split on update"
assert user2['last_name'] == "Smith", "Last name not split on update"
assert user2['name'] == "John Smith", "Name not updated"
print("  ✓ PASS")

# Test 5: Update class slot with teacher names
print("\n5. Testing update_class_slot with teacher names...")
# Get an existing slot
users = db.list_users()
test_user = [u for u in users if u['name'] == 'Daniela Silva'][0]
slots = db.get_user_slots(test_user['id'])
if slots:
    slot = slots[0]
    print(f"  Updating slot {slot['slot_number']}: {slot.get('primary_teacher_name', 'N/A')}")
    
    success = db.update_class_slot(
        slot['id'],
        primary_teacher_first_name="Sarah",
        primary_teacher_last_name="Lang"
    )
    
    updated_slot = db.get_slot(slot['id'])
    print(f"  Updated slot:")
    print(f"    primary_teacher_first_name: '{updated_slot.get('primary_teacher_first_name', '')}'")
    print(f"    primary_teacher_last_name: '{updated_slot.get('primary_teacher_last_name', '')}'")
    print(f"    primary_teacher_name (computed): '{updated_slot.get('primary_teacher_name', '')}'")
    
    assert updated_slot['primary_teacher_first_name'] == "Sarah", "Teacher first name not updated"
    assert updated_slot['primary_teacher_last_name'] == "Lang", "Teacher last name not updated"
    assert updated_slot['primary_teacher_name'] == "Sarah Lang", "Computed teacher name not updated"
    print("  ✓ PASS")
else:
    print("  ⚠️  SKIP (no slots found)")

# Test 6: Partial update (only first name)
print("\n6. Testing partial update (only first_name)...")
success = db.update_user(user_id, first_name="Partial")
user = db.get_user(user_id)
print(f"  Updated user: {user['name']}")
print(f"    first_name: '{user['first_name']}'")
print(f"    last_name: '{user['last_name']}'")
assert user['first_name'] == "Partial", "First name not updated"
assert user['last_name'] == "Name", "Last name should remain unchanged"
assert user['name'] == "Partial Name", "Computed name not updated correctly"
print("  ✓ PASS")

# Cleanup
print("\n7. Cleaning up test users...")
db.delete_user(user_id)
db.delete_user(user_id2)
print("  ✓ Cleanup complete")

print("\n" + "="*80)
print("✅ ALL CRUD TESTS PASSED")
print("="*80)

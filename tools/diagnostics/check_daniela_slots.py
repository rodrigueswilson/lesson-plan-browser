from backend.database import Database

db = Database()
user = db.get_user_by_name('Daniela Silva')
slots = db.get_user_slots(user['id'])

print(f"User: {user['name']}")
print(f"User ID: {user['id']}")
print(f"\nSlots:")
for s in slots:
    print(f"  Slot {s['slot_number']}: {s['subject']}")
    print(f"    File: {s.get('primary_teacher_file', 'NOT SET')}")
    print()

"""Check what slots exist for a user."""
from backend.database import get_db

user_id = '04fe8898-cb89-4a73-affb-64a97a98f820'

db = get_db()
slots = db.get_user_slots(user_id)

print(f'Found {len(slots)} slots for user {user_id}:')
for s in slots:
    print(f"  - ID: {s['id']}")
    print(f"    Teacher: {s.get('primary_teacher_name', 'NO NAME')}")
    print(f"    Subject: {s.get('subject', 'NO SUBJECT')}")
    print(f"    Grade: {s.get('grade', 'NO GRADE')}")
    print()

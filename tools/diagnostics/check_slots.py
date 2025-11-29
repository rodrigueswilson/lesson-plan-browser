"""Quick script to check which slots have files configured."""

from backend.database import get_db

db = get_db()

print("=" * 80)
print("SLOT CONFIGURATION CHECK")
print("=" * 80)

users = db.list_users()
for user in users:
    print(f"\n👤 User: {user['name']} (ID: {user['id']})")
    
    slots = db.get_user_slots(user['id'])
    if not slots:
        print("   No slots configured")
        continue
    
    print(f"   Found {len(slots)} slots:")
    
    for slot in slots:
        slot_num = slot['slot_number']
        subject = slot['subject']
        primary_file = slot.get('primary_teacher_file', 'NOT SET')
        
        has_file = primary_file and primary_file != 'NOT SET'
        status = "✅" if has_file else "❌"
        
        print(f"\n   {status} Slot {slot_num}: {subject}")
        print(f"      Primary file: {primary_file}")
        
        if has_file:
            from pathlib import Path
            exists = Path(primary_file).exists()
            print(f"      File exists: {'✅ YES' if exists else '❌ NO'}")

print("\n" + "=" * 80)
print("RECOMMENDATION")
print("=" * 80)
print("\nTo test, either:")
print("1. Use the frontend to configure a slot with a valid file path")
print("2. Or manually update the database with a test file path")

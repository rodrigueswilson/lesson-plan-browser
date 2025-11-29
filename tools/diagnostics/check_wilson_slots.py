from backend.database import Database

db = Database()

# Get Wilson's user
user = db.get_user_by_name('Wilson Rodrigues')
slots = db.get_user_slots(user['id'])

print(f"User: {user['name']}")
print(f"User ID: {user['id']}")
print(f"\nSlots:")
for s in slots:
    print(f"  Slot {s['slot_number']}: {s['subject']}")
    print(f"    File: {s.get('primary_teacher_file', 'NOT SET')}")
    print()

# Also check weekly plan
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, week_of, week_folder_path, status
        FROM weekly_plans 
        WHERE user_id = ? AND week_of = '10-27-10-31'
        ORDER BY generated_at DESC
        LIMIT 1
    """, (user['id'],))
    
    plan = cursor.fetchone()
    if plan:
        print(f"Latest Weekly Plan:")
        print(f"  Plan ID: {plan[0]}")
        print(f"  Week: {plan[1]}")
        print(f"  Folder Path: {plan[2]}")
        print(f"  Status: {plan[3]}")

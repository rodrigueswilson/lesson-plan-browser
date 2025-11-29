from backend.database import Database

db = Database()

user = db.get_user_by_name('Daniela Silva')
slots = db.get_user_slots(user['id'])

print(f"=== {user['name']} Configuration ===\n")

for slot in slots:
    print(f"Slot {slot['slot_number']}: {slot['subject']}")
    print(f"  First Name: {slot.get('primary_teacher_first_name')}")
    print(f"  Last Name: {slot.get('primary_teacher_last_name')}")
    print(f"  File Pattern: {slot.get('primary_teacher_file_pattern')}")
    print(f"  Full Name (for output): {slot.get('primary_teacher_name')}")
    print()

# Check weekly plan
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT week_folder_path
        FROM weekly_plans 
        WHERE user_id = ? AND week_of = '10-27-10-31'
        ORDER BY generated_at DESC
        LIMIT 1
    """, (user['id'],))
    
    plan = cursor.fetchone()
    if plan:
        print(f"Week Folder: {plan[0]}")

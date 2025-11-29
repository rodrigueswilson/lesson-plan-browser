from backend.database import Database

db = Database()

# Get Daniela's user
user = db.get_user_by_name('Daniela Silva')
slots = db.get_user_slots(user['id'])

print(f"Clearing individual file paths for {user['name']}...")
print("(System will auto-detect files from parent folder)\n")

with db.get_connection() as conn:
    cursor = conn.cursor()
    
    for slot in slots:
        cursor.execute("""
            UPDATE class_slots
            SET primary_teacher_file = NULL
            WHERE id = ?
        """, (slot['id'],))
        
        print(f"✅ Slot {slot['slot_number']} ({slot['subject']}): Cleared")
    
    conn.commit()
    print(f"\n✅ All slot file paths cleared!")
    print(f"   System will use: F:\\rodri\\Documents\\OneDrive\\AS\\Daniela LP\\[most recent folder]")

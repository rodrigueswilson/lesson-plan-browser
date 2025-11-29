from backend.database import Database

db = Database()

# Get Daniela's user
user = db.get_user_by_name('Daniela Silva')
slots = db.get_user_slots(user['id'])

# Map slots to teacher names based on W44 files
teacher_mappings = {
    1: ("Catarina", "Morais"),      # ELA/SS
    2: ("Ms.", "Santiago"),          # Social Studies  
    3: ("Mariela", "Grande"),        # Science/Health
    4: ("Mariela", "Grande"),        # Science/Health (duplicate)
    5: ("Catarina", "Morais")        # Math
}

print(f"Updating teacher names for {user['name']}...\n")

with db.get_connection() as conn:
    cursor = conn.cursor()
    
    for slot in slots:
        slot_num = slot['slot_number']
        if slot_num in teacher_mappings:
            first_name, last_name = teacher_mappings[slot_num]
            
            cursor.execute("""
                UPDATE class_slots
                SET primary_teacher_first_name = ?,
                    primary_teacher_last_name = ?
                WHERE id = ?
            """, (first_name, last_name, slot['id']))
            
            print(f"✅ Slot {slot_num} ({slot['subject']}): {first_name} {last_name}")
    
    conn.commit()
    print(f"\n✅ All teacher names updated!")

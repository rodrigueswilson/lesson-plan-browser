from backend.database import Database

db = Database()

# Get Daniela's user
user = db.get_user_by_name('Daniela Silva')
slots = db.get_user_slots(user['id'])

# Set file patterns to LAST NAME ONLY for file matching
file_pattern_mappings = {
    1: "Morais",      # ELA/SS - Catarina Morais
    2: "Santiago",    # Social Studies - Ms. Santiago
    3: "Grande",      # Science/Health - Mariela Grande
    4: "Grande",      # Science/Health - Mariela Grande
    5: "Morais"       # Math - Catarina Morais
}

print(f"Setting file patterns for {user['name']}...\n")

with db.get_connection() as conn:
    cursor = conn.cursor()
    
    for slot in slots:
        slot_num = slot['slot_number']
        if slot_num in file_pattern_mappings:
            pattern = file_pattern_mappings[slot_num]
            
            cursor.execute("""
                UPDATE class_slots
                SET primary_teacher_file_pattern = ?
                WHERE id = ?
            """, (pattern, slot['id']))
            
            print(f"✅ Slot {slot_num} ({slot['subject']}): Pattern = '{pattern}'")
    
    conn.commit()
    print(f"\n✅ All file patterns updated!")
    print(f"   System will now match files using last names only")
